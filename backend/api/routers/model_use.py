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
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from api.models.job import Job, JobStatus, JobType
from api.models.user import User
from api.dependencies.auth import get_current_active_user
from api.services.email_service import email_service
from api.utils.security import security_validator
from api.websocket.task_manager import task_status_manager
from config.database import SessionLocal, get_db
from config.settings import settings


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/model-use", tags=["Model Use"])


class ModelUsePredictCreate(BaseModel):
    model_type: str
    test_data_path: str
    email: Optional[EmailStr] = None

    model_path: Optional[str] = None
    som_model_path: Optional[str] = None
    winmap_path: Optional[str] = None  # 兼容旧前端字段（当前 SOM 推理不需要）

    encoder_path: Optional[str] = None
    classifier_path: Optional[str] = None

    scaler_path: Optional[str] = None
    un_semi_model_path: Optional[str] = None


class ModelUsePredictResponse(BaseModel):
    job_id: str
    model_type: str
    status: str
    message: str
    created_at: str


def _generate_job_id() -> str:
    return f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _validate_path_required(path: Optional[str], *, allowed_extensions: list[str], field_name: str) -> Path:
    if not path:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field_name} is a required field")
    try:
        return security_validator.validate_file_path(path, allowed_extensions=[e.lower() for e in allowed_extensions])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field_name} verification failed: {str(e)}")


async def _run_command_async(
    cmd: list[str],
    *,
    cwd: str,
    terminal_log_path: Path,
    timeout_sec: int = 3600,
) -> None:
    terminal_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(terminal_log_path, "w", encoding="utf-8") as log_fp:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
        )
        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout_sec)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError(f"Command timeout ({timeout_sec}s): {' '.join(cmd)}")

    if proc.returncode != 0:  # type: ignore[name-defined]
        raise RuntimeError(f"Command execution failed (code={proc.returncode}): {' '.join(cmd)}")  # type: ignore[union-attr]


@router.post("/predict", response_model=ModelUsePredictResponse)
async def predict(
    payload: ModelUsePredictCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    model_type_norm = (payload.model_type or "").strip().lower()
    if not model_type_norm:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="model_type can not be empty")

    # 统一 Jobs 目录（与训练/数据处理 PHP 版保持一致）
    jobs_root = settings.path_jobs

    test_data_path = _validate_path_required(
        payload.test_data_path,
        allowed_extensions=[".txt", ".csv", ".tsv"],
        field_name="test_data_path",
    )

    model_weights_ext = [".pth", ".pt", ".pkl"]

    supervised_models = {"cnn", "lstm", "rnn", "mlp", "autoencoder", "transformer", "rbfn"}
    unsupervised_models = {"vae", "deepcluster", "ladder", "pseudo"}

    required_model_paths: Dict[str, Path] = {}

    # 根据模型类型校验必需文件
    if model_type_norm in supervised_models:
        if model_type_norm == "autoencoder":
            required_model_paths["encoder_path"] = _validate_path_required(
                payload.encoder_path, allowed_extensions=model_weights_ext, field_name="encoder_path"
            )
            required_model_paths["classifier_path"] = _validate_path_required(
                payload.classifier_path, allowed_extensions=model_weights_ext, field_name="classifier_path"
            )
        elif model_type_norm == "som":
            # 目前这一分支理论上不会走到（som 单独处理），保留兜底
            required_model_paths["som_model_path"] = _validate_path_required(
                payload.som_model_path, allowed_extensions=model_weights_ext, field_name="som_model_path"
            )
        else:
            required_model_paths["model_path"] = _validate_path_required(
                payload.model_path, allowed_extensions=model_weights_ext, field_name="model_path"
            )
    elif model_type_norm == "som":
        required_model_paths["som_model_path"] = _validate_path_required(
            payload.som_model_path, allowed_extensions=model_weights_ext, field_name="som_model_path"
        )
    elif model_type_norm in unsupervised_models:
        required_model_paths["scaler_path"] = _validate_path_required(
            payload.scaler_path, allowed_extensions=model_weights_ext, field_name="scaler_path"
        )
        required_model_paths["un_semi_model_path"] = _validate_path_required(
            payload.un_semi_model_path,
            allowed_extensions=model_weights_ext,
            field_name="un_semi_model_path",
        )
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Unsupported model_type: {payload.model_type}")

    job_id = _generate_job_id()
    job = Job(
        job_id=job_id,
        user_id=int(current_user.id),
        job_type=JobType.MODEL_TRAIN,
        status=JobStatus.SUBMITTED,
        progress=0,
        current_step="已提交，等待执行",
        input_params=json.dumps(
            {
                "model_type": model_type_norm,
                "test_data_path": str(test_data_path),
                # 模型权重/预处理文件路径用于后台执行
                **{k: str(v) for k, v in required_model_paths.items()},
                "email": payload.email,
            },
            ensure_ascii=False,
        ),
        created_at=datetime.now(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # 异步执行模型推理（独立 DB 会话，避免请求会话关闭导致连接失效）
    asyncio.create_task(
        _execute_model_use_background(
            user_id=int(current_user.id),
            job_id=job_id,
            model_type=model_type_norm,
            test_data_path=str(test_data_path),
            model_paths={k: str(v) for k, v in required_model_paths.items()},
            email=str(payload.email) if payload.email else None,
        )
    )

    return ModelUsePredictResponse(
        job_id=job.job_id,
        model_type=model_type_norm,
        status=job.status.value if hasattr(job.status, "value") else str(job.status),
        message="模型预测任务已创建",
        created_at=job.created_at.isoformat() if job.created_at else datetime.now().isoformat(),
    )


async def _execute_model_use_background(
    *,
    user_id: int,
    job_id: str,
    model_type: str,
    test_data_path: str,
    model_paths: Dict[str, str],
    email: Optional[str] = None,
):
    """
    后台执行：复制文件 -> 调用 code/use_model/* 预测脚本 -> 压缩结果 -> 更新 Job
    """
    bg_db = SessionLocal()
    try:
        bg_user = bg_db.query(User).filter(User.id == user_id).first()
        if not bg_user:
            raise RuntimeError(f"Background model application not found user: {user_id}")

        jobs_root = settings.path_jobs
        jobs_dir = jobs_root / job_id
        result_dir = jobs_dir / "result"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)

        job = bg_db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            raise RuntimeError(f"Background not found Job: {job_id}")

        # 标记开始执行
        job.status = JobStatus.PROCESSING
        job.progress = 10
        job.current_step = "正在准备推理环境"
        job.updated_at = datetime.now()
        bg_db.commit()

        await task_status_manager.send_task_status(
            str(bg_user.id),
            {
                "job_id": job_id,
                "status": JobStatus.PROCESSING.value,
                "progress": 10,
                "current_step": "正在准备推理环境",
            },
        )

        # 复制数据文件（推理脚本固定读取 {jobID}_test.txt）
        test_src = security_validator.validate_file_path(
            test_data_path, allowed_extensions=[".txt", ".csv", ".tsv"]
        )
        test_dst = jobs_dir / f"{job_id}_test.txt"
        shutil.copy2(str(test_src), str(test_dst))

        # 标准化模型/预处理文件命名（与 code/use_model/* 脚本约定）
        model_pth = jobs_dir / "model.pth"
        model_scaler_pkl = jobs_dir / "scaler.pkl"

        if model_type == "autoencoder":
            shutil.copy2(model_paths["encoder_path"], str(jobs_dir / "model_autoencoder.pth"))
            shutil.copy2(model_paths["classifier_path"], str(jobs_dir / "model_cls.pth"))
        elif model_type == "som":
            shutil.copy2(model_paths["som_model_path"], str(model_pth))
        elif model_type in {"vae", "deepcluster", "ladder", "pseudo"}:
            shutil.copy2(model_paths["un_semi_model_path"], str(model_pth))
            shutil.copy2(model_paths["scaler_path"], str(model_scaler_pkl))
        else:
            shutil.copy2(model_paths["model_path"], str(model_pth))

        # 选择推理脚本并拼参数
        terminal_log = result_dir / "terminal.log"
        cwd = str(settings.path_repo)

        supervised_model_map = {
            "cnn": "CNN",
            "lstm": "LSTM",
            "rnn": "RNN",
            "mlp": "MLP",
            "autoencoder": "AutoEncoder",
            "transformer": "Transformer",
            "rbfn": "RBFN",
        }
        python_exec = "/opt/anaconda/envs/automata/bin/python"

        if model_type in supervised_model_map:
            script_path = str(settings.path_code / "use_model" / "general.py")
            cmd = [
                python_exec,
                script_path,
                "--jobID",
                str(job_id),
                "--model_type",
                supervised_model_map[model_type],
            ]
        elif model_type == "som":
            script_path = str(settings.path_code / "use_model" / "som.py")
            cmd = [
                python_exec,
                script_path,
                "--jobID",
                str(job_id),
                "--model_type",
                "SOM",
            ]
        else:
            # 无监督/半监督模型
            script_map = {
                "vae": str(settings.path_code / "use_model" / "predict_vae.py"),
                "deepcluster": str(settings.path_code / "use_model" / "predict_deepcluster.py"),
                "ladder": str(settings.path_code / "use_model" / "predict_ladder.py"),
                "pseudo": str(settings.path_code / "use_model" / "predict_pseudo.py"),
            }
            if model_type not in script_map:
                raise RuntimeError(f"Unsupported model_type: {model_type}")
            script_path = script_map[model_type]
            cmd = [
                python_exec,
                script_path,
                "--model_path",
                str(model_pth),
                "--scaler_path",
                str(model_scaler_pkl),
                "--data_path",
                str(test_dst),
                "--output_path",
                str(result_dir / "test_result"),
            ]

        job.current_step = "执行推理脚本"
        job.progress = 40
        job.updated_at = datetime.now()
        bg_db.commit()

        await task_status_manager.send_task_status(
            str(bg_user.id),
            {
                "job_id": job_id,
                "status": JobStatus.PROCESSING.value,
                "progress": 40,
                "current_step": "执行推理脚本",
                "message": "正在运行模型预测",
            },
        )

        await _run_command_async(
            cmd,
            cwd=cwd,
            terminal_log_path=terminal_log,
            timeout_sec=3600,
        )

        # 压缩结果目录
        job.current_step = "压缩结果"
        job.progress = 90
        job.updated_at = datetime.now()
        bg_db.commit()

        await task_status_manager.send_task_status(
            str(bg_user.id),
            {
                "job_id": job_id,
                "status": JobStatus.PROCESSING.value,
                "progress": 90,
                "current_step": "压缩结果",
                "message": "正在压缩结果文件",
            },
        )

        zip_file = str(result_dir) + ".zip"
        zip_file_tmp = zip_file + ".tmp"

        try:
            # 1) 先写入临时 zip（避免“已写入 DB 但 zip 未完全落盘”竞态）
            tmp_path = Path(zip_file_tmp)
            final_path = Path(zip_file)
            if tmp_path.exists():
                tmp_path.unlink()

            with zipfile.ZipFile(str(tmp_path), "w", zipfile.ZIP_DEFLATED) as zf:
                for path in result_dir.rglob("*"):
                    if path.is_file():
                        zf.write(path, path.relative_to(result_dir))

            # 2) 基础可交付校验：存在且非空
            if not tmp_path.exists() or tmp_path.stat().st_size <= 0:
                raise RuntimeError("Temporary zip cannot be delivered: file does not exist or is empty")

            # 3) 进一步校验 zip 是否可读（防止写入中途损坏）
            try:
                with zipfile.ZipFile(str(tmp_path), "r") as zf_check:
                    bad = zf_check.testzip()
                    if bad is not None:
                        raise RuntimeError(f"zip verification failed, bad file: {bad}")
            except zipfile.BadZipFile as e:
                raise RuntimeError(f"zip verification failed: bad zip: {e}") from e

            # 4) 原子 rename：tmp -> final
            # 同一文件系统内 rename 是原子的，能最大程度避免下载服务读到半成品
            tmp_path.replace(final_path)

            # 5) 最终校验
            if not final_path.exists() or final_path.stat().st_size <= 0:
                raise RuntimeError("Final zip cannot be delivered: file does not exist or is empty")
        except Exception as e:
            # 确保不把“不可交付 zip”写入 DB
            raise RuntimeError(f"Result compression failed/verification failed: {e}") from e

        job = bg_db.query(Job).filter(Job.job_id == job_id).first()
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.current_step = "模型应用完成"
        job.result_file = zip_file
        job.output_params = json.dumps({"model_type": model_type}, ensure_ascii=False)
        job.completed_at = datetime.now()
        job.updated_at = datetime.now()
        bg_db.commit()

        await task_status_manager.send_task_status(
            str(bg_user.id),
            {
                "job_id": job_id,
                "status": JobStatus.COMPLETED.value,
                "progress": 100,
                "current_step": "模型应用完成",
                "result_file": zip_file,
                "message": f"{model_type} 模型预测完成",
            },
        )

        # 如果任务成功且提供了邮箱，发送结果邮件（与训练任务一致：失败不影响任务结果）
        if email:
            try:
                await email_service.send_result_email(
                    to_email=email,
                    job_id=job_id,
                    analysis_type=f"模型应用({model_type})",
                    result_dir=zip_file,
                )
            except Exception as e:
                logger.warning(f"邮件发送失败（不影响任务结果）: {e}")
    except Exception as e:
        logger.exception(f"[MODEL_USE] 执行失败: job_id={job_id}, error={e}")
        try:
            job = bg_db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.progress = 0
                job.current_step = "执行失败"
                job.error_message = str(e)
                job.updated_at = datetime.now()
                job.completed_at = datetime.now()
                bg_db.commit()

                await task_status_manager.send_task_status(
                    str(user_id),
                    {
                        "job_id": job_id,
                        "status": JobStatus.FAILED.value,
                        "progress": 0,
                        "current_step": "执行失败",
                        "message": str(e),
                    },
                )
        except Exception:
            # 兜底：失败后不影响主流程
            pass
    finally:
        bg_db.close()

