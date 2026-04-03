"""
分析并训练：监督学习 →（split 时恢复全集）→ 可选 ID 转换 → 转置为 R 输入 → DESeq2/limma。
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from api.models.job import Job, JobStatus, JobType
from api.models.user import User
from api.services.email_service import email_service
from api.services.training_service import TrainingService, _is_zip_deliverable
from api.utils.expression_matrix_php import transpose_expression_file_like_php
from api.websocket.task_manager import task_status_manager
from api.services.concurrency import GLOBAL_TASK_SEM, next_server_seq
from api.utils.subprocess_utils import run_subprocess
from config.database import SessionLocal
from config.settings import settings

logger = logging.getLogger(__name__)

JOBS_ROOT = settings.path_jobs
REPO_ROOT = settings.path_repo
RSCRIPT = "/opt/anaconda/envs/R_442/bin/Rscript"


def _organism_to_mysql2tpm_r(organism: str) -> str:
    return {
        "Homo_sapiens": "homo_sapiens",
        "Bovine": "bos_taurus",
        "Mus_musculus": "mus_musculus",
        "Drosophila_melanogaster": "drosophila_melanogaster",
    }[organism]


def _gene_nomenclature_to_r_flags(gene_nomenclature: str) -> tuple[str, str]:
    if gene_nomenclature == "gene_id":
        return "GeneID", "GeneID"
    if gene_nomenclature == "ensembl":
        return "EnsemblID", "EnsemblID"
    raise ValueError("internal")


class AnalysisTrainService:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.jobs_root = JOBS_ROOT

    def _stage_supervised_dataset(
        self,
        ts: TrainingService,
        job_id: str,
        jobs_dir: Path,
        parameters: Dict[str, Any],
        dataset_path: Optional[str],
    ) -> None:
        strategy = parameters.get("strategy", "split")
        if strategy == "upload":
            train_fid = parameters.get("train_dataset_file_id")
            val_fid = parameters.get("validation_dataset_file_id")
            test_fid = parameters.get("test_dataset_file_id")
            if train_fid and val_fid and test_fid:
                for fid, suffix in (
                    (train_fid, "_data.txt"),
                    (val_fid, "_val.txt"),
                    (test_fid, "_test.txt"),
                ):
                    src = ts._validate_dataset_path(f"file://{fid}")
                    shutil.copy2(str(src), str(jobs_dir / f"{job_id}{suffix}"))
            elif dataset_path:
                src = ts._validate_dataset_path(dataset_path)
                shutil.copy2(str(src), str(jobs_dir / f"{job_id}_data.txt"))
            else:
                raise ValueError("upload strategy requires three file")
        elif strategy == "kfold":
            train_fid = parameters.get("kfold_train_dataset_file_id")
            test_fid = parameters.get("kfold_test_dataset_file_id")
            if train_fid and test_fid:
                shutil.copy2(
                    str(ts._validate_dataset_path(f"file://{train_fid}")),
                    str(jobs_dir / f"{job_id}_data.txt"),
                )
                shutil.copy2(
                    str(ts._validate_dataset_path(f"file://{test_fid}")),
                    str(jobs_dir / f"{job_id}_test.txt"),
                )
            elif dataset_path:
                src = ts._validate_dataset_path(dataset_path)
                shutil.copy2(str(src), str(jobs_dir / f"{job_id}_data.txt"))
            else:
                raise ValueError("kfold strategy requires training/test file")
        elif dataset_path:
            src = ts._validate_dataset_path(dataset_path)
            shutil.copy2(str(src), str(jobs_dir / f"{job_id}_data.txt"))
        else:
            raise ValueError("split strategy requires dataset_path (e.g. file://<id>)")

    def create_task(
        self,
        task_name: str,
        model_type: str,
        parameters: Dict[str, Any],
        analysis: Dict[str, Any],
        group_info_file_id: str,
        dataset_path: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Job:
        job_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        payload = {
            "task_name": task_name,
            "model_type": model_type,
            "training_type": "supervised",
            "parameters": parameters,
            "dataset_path": dataset_path,
            "analysis": analysis,
            "group_info_file_id": group_info_file_id,
        }
        job = Job(
            job_id=job_id,
            user_id=self.user.id,
            job_type=JobType.ANALYSIS_TRAIN,
            status=JobStatus.SUBMITTED,
            progress=0,
            current_step="已提交，等待执行",
            input_params=json.dumps(payload, ensure_ascii=False),
            created_at=datetime.now(),
        )
        self.db.add(job)
        self.db.commit()
        resolved_email = email if email is not None else parameters.get("email")
        asyncio.create_task(
            self._execute_background(
                user_id=int(self.user.id),
                job_id=job_id,
                model_type=model_type,
                parameters=parameters,
                analysis=analysis,
                group_info_file_id=group_info_file_id,
                dataset_path=dataset_path,
                email=resolved_email,
            )
        )
        return job

    async def _execute_background(
        self,
        user_id: int,
        job_id: str,
        model_type: str,
        parameters: Dict[str, Any],
        analysis: Dict[str, Any],
        group_info_file_id: str,
        dataset_path: Optional[str],
        email: Optional[str],
    ) -> None:
        bg_db = SessionLocal()
        try:
            bg_user = bg_db.query(User).filter(User.id == user_id).first()
            if not bg_user:
                raise RuntimeError(f"Background task not found user: {user_id}")
            svc = AnalysisTrainService(db=bg_db, user=bg_user)
            await svc._execute_pipeline(
                job_id=job_id,
                model_type=model_type,
                parameters=parameters,
                analysis=analysis,
                group_info_file_id=group_info_file_id,
                dataset_path=dataset_path,
                email=email,
            )
        finally:
            bg_db.close()

    async def _fail(self, job_id: str, msg: str, email: Optional[str]) -> None:
        job = self.db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error_message = msg
            job.current_step = "分析或训练失败"
            job.updated_at = datetime.now()
        self.db.commit()
        try:
            await task_status_manager.send_task_status(
                str(self.user.id),
                {
                    "job_id": job_id,
                    "status": JobStatus.FAILED.value,
                    "progress": 0,
                    "current_step": "分析或训练失败",
                    "error_message": msg,
                    "message": msg,
                },
            )
        except Exception as e:
            logger.debug("WebSocket: %s", e)
        if email:
            try:
                await email_service.send_failure_email(
                    to_email=email,
                    job_id=job_id,
                    analysis_type="分析并训练",
                    error_message=msg,
                )
            except Exception as e:
                logger.warning("失败邮件: %s", e)

    async def _execute_pipeline(
        self,
        job_id: str,
        model_type: str,
        parameters: Dict[str, Any],
        analysis: Dict[str, Any],
        group_info_file_id: str,
        dataset_path: Optional[str],
        email: Optional[str],
    ) -> None:
        jobs_dir = self.jobs_root / job_id
        result_dir = jobs_dir / "result"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)
        strategy = parameters.get("strategy", "split")
        data_txt = jobs_dir / f"{job_id}_data.txt"
        origin_txt = jobs_dir / f"{job_id}_data_origin.txt"
        info_txt = jobs_dir / f"{job_id}_info.txt"

        try:
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.PROCESSING
                job.progress = 5
                job.current_step = "准备数据与分组文件"
                job.updated_at = datetime.now()
            self.db.commit()

            ts = TrainingService(self.db, self.user)
            self._stage_supervised_dataset(ts, job_id, jobs_dir, parameters, dataset_path)

            gi_src = ts._validate_dataset_path(f"file://{group_info_file_id}")
            shutil.copy2(str(gi_src), str(info_txt))

            if strategy == "split":
                shutil.copy2(str(data_txt), str(origin_txt))

            if email:
                (jobs_dir / "email.txt").write_text(
                    f"email: {email}\n from analysis_train FastAPI\n", encoding="utf-8"
                )

            if job:
                job.progress = 30
                job.current_step = "执行监督学习训练"
                job.updated_at = datetime.now()
            self.db.commit()

            await ts._execute_supervised_training_core(
                job_id=job_id,
                model_type=model_type,
                parameters=parameters,
                jobs_dir=jobs_dir,
                result_dir=result_dir,
            )

            if strategy == "split":
                train_txt = jobs_dir / f"{job_id}_data_train.txt"
                if data_txt.exists():
                    data_txt.rename(train_txt)
                if origin_txt.exists():
                    shutil.move(str(origin_txt), str(data_txt))

            gn = analysis["gene_nomenclature"]
            organism = analysis["organism"]
            data_type = analysis["data_type"]
            fc = analysis["fc"]
            padj = analysis["padj"]
            correction = analysis["correction"]

            id_log = result_dir / "terminal_msg_data_process.txt"
            if gn != "symbol":
                gflag, hflag = _gene_nomenclature_to_r_flags(gn)
                r_o = _organism_to_mysql2tpm_r(organism)
                cmd = [
                    RSCRIPT,
                    "--no-save",
                    str(REPO_ROOT / "code" / "mysql2TPM.R"),
                    "-g",
                    gflag,
                    "-a",
                    job_id,
                    "-h",
                    hflag,
                    "-r",
                    r_o,
                    "-i",
                    str(data_txt),
                    "-o",
                    str(data_txt),
                ]
                id_log.parent.mkdir(parents=True, exist_ok=True)
                logger.info("[ANALYSIS_TRAIN] mysql2TPM %s", cmd)
                with open(id_log, "w", encoding="utf-8") as log_fp:
                    acquired_immediately = False
                    try:
                        await asyncio.wait_for(GLOBAL_TASK_SEM.acquire(), timeout=0)
                        acquired_immediately = True
                    except Exception:
                        acquired_immediately = False
                    if not acquired_immediately:
                        if job and job.status == JobStatus.SUBMITTED and (job.current_step or "") != "排队中（等待资源）":
                            job.current_step = "排队中（等待资源）"
                            job.updated_at = datetime.now()
                            self.db.commit()
                            try:
                                await task_status_manager.send_task_status(
                                    str(self.user.id),
                                    {
                                        "job_id": job_id,
                                        "status": JobStatus.SUBMITTED.value,
                                        "progress": job.progress or 0,
                                        "current_step": job.current_step,
                                        "message": "排队中（等待资源）",
                                        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                                        "server_seq": next_server_seq(),
                                    },
                                )
                            except Exception:
                                pass
                        await GLOBAL_TASK_SEM.acquire()
                    try:
                        r1 = await run_subprocess(
                            cmd,
                            cwd=str(REPO_ROOT),
                            stdout=log_fp,
                            stderr=subprocess.STDOUT,
                            timeout=7200,
                            shell=False,
                            text=True,
                        )
                    finally:
                        GLOBAL_TASK_SEM.release()
                if r1.returncode != 0:
                    raise RuntimeError(
                        f"Gene ID conversion failed, log: {id_log}, exit={r1.returncode}"
                    )

            if job:
                job.progress = 70
                job.current_step = "转置表达矩阵并运行差异分析"
                job.updated_at = datetime.now()
            self.db.commit()

            transpose_expression_file_like_php(data_txt)

            r_script = (
                REPO_ROOT / "code" / "DESeq2_read_count.R"
                if data_type == "read_counts"
                else REPO_ROOT / "code" / "limma_fpkm_df.R"
            )
            de_log = jobs_dir / "terminal_msg.txt"
            cmd_de = [
                RSCRIPT,
                "--no-save",
                str(r_script),
                "-i",
                str(data_txt),
                "-k",
                str(info_txt),
                "-j",
                job_id,
                "-c",
                str(fc),
                "-d",
                str(padj),
                "-e",
                correction,
            ]
            logger.info("[ANALYSIS_TRAIN] DE %s", cmd_de)
            with open(de_log, "w", encoding="utf-8") as log_fp:
                acquired_immediately = False
                try:
                    await asyncio.wait_for(GLOBAL_TASK_SEM.acquire(), timeout=0)
                    acquired_immediately = True
                except Exception:
                    acquired_immediately = False
                if not acquired_immediately:
                    job = self.db.query(Job).filter(Job.job_id == job_id).first()
                    if job and job.status == JobStatus.SUBMITTED and (job.current_step or "") != "排队中（等待资源）":
                        job.current_step = "排队中（等待资源）"
                        job.updated_at = datetime.now()
                        self.db.commit()
                        try:
                            await task_status_manager.send_task_status(
                                str(self.user.id),
                                {
                                    "job_id": job_id,
                                    "status": JobStatus.SUBMITTED.value,
                                    "progress": job.progress or 0,
                                    "current_step": job.current_step,
                                    "message": "排队中（等待资源）",
                                    "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                                    "server_seq": next_server_seq(),
                                },
                            )
                        except Exception:
                            pass
                    await GLOBAL_TASK_SEM.acquire()
                try:
                    r2 = await run_subprocess(
                        cmd_de,
                        cwd=str(REPO_ROOT),
                        stdout=log_fp,
                        stderr=subprocess.STDOUT,
                        timeout=7200,
                        shell=False,
                        text=True,
                    )
                finally:
                    GLOBAL_TASK_SEM.release()
            if r2.returncode != 0:
                raise RuntimeError(f"Differential analysis failed, log: {de_log}, exit={r2.returncode}")

            zip_path = str(jobs_dir / "model_result.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in result_dir.rglob("*"):
                    if path.is_file():
                        zf.write(path, path.relative_to(result_dir))

            if not _is_zip_deliverable(zip_path):
                raise RuntimeError("Result zip cannot be delivered")

            out_meta = {
                "analysis": analysis,
                "result_rel": "result",
                "zip": "model_result.zip",
                "previews": {
                    "volcano_png": f"download_data/Jobs/{job_id}/result/volcano.png",
                    "heatmap_png": f"download_data/Jobs/{job_id}/result/df_cluster_heatmap.png",
                },
            }
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.COMPLETED
                job.progress = 100
                job.current_step = "已完成"
                job.result_file = zip_path
                job.output_params = json.dumps(out_meta, ensure_ascii=False)
                job.completed_at = datetime.now()
                job.updated_at = datetime.now()
            self.db.commit()

            try:
                await task_status_manager.send_task_status(
                    str(self.user.id),
                    {
                        "job_id": job_id,
                        "status": JobStatus.COMPLETED.value,
                        "progress": 100,
                        "current_step": "已完成",
                        "result_file": zip_path,
                        "message": "分析并训练完成",
                    },
                )
            except Exception as e:
                logger.debug("WebSocket: %s", e)

            if email:
                try:
                    await email_service.send_result_email(
                        to_email=email,
                        job_id=job_id,
                        analysis_type="分析并训练",
                        result_dir=zip_path,
                    )
                except Exception as e:
                    logger.warning("结果邮件: %s", e)

        except Exception as e:
            logger.exception("[ANALYSIS_TRAIN] job_id=%s", job_id)
            await self._fail(job_id, str(e), email)
