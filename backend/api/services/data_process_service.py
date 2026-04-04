"""
数据处理服务层：处理基因组、转录组等生物数据的业务逻辑
"""
import os
import uuid
import logging
import json
import subprocess
from datetime import datetime
from typing import Optional
from pathlib import Path
import asyncio
import math
from contextlib import asynccontextmanager
from fastapi import UploadFile, HTTPException

from sqlalchemy.orm import Session
from sqlalchemy import text
from api.models.user import User
from api.models.job import Job, JobType, JobStatus
from api.schemas.data_process import (
    GenomeProcessResponse,
    TranscriptomeProcessResponse,
    ProteinProcessResponse,
    IntegrationProcessResponse,
    PvalueIntegrationProcessResponse,
)
from api.utils.file_utils import save_uploaded_file
from api.websocket.task_manager import task_status_manager
from api.services.email_service import email_service
from api.services.concurrency import GLOBAL_TASK_SEM, next_server_seq
from api.utils.subprocess_utils import run_subprocess
from config.settings import settings

logger = logging.getLogger(__name__)


def _r_mysql_subprocess_env() -> dict[str, str]:
    """与 FastAPI settings 一致的数据库环境变量，供 R 子进程读取（避免缺省 localhost 走 Unix socket）。"""
    return {
        "DB_HOST": settings.DB_HOST,
        "DB_USER": settings.DB_USER,
        "DB_PASSWORD": settings.DB_PASSWORD,
        "DB_NAME": settings.DB_NAME,
        "DB_PORT": str(settings.DB_PORT),
    }


class DataProcessService:
    """数据处理服务类"""
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.upload_dir = Path("uploaded_files")
        self.process_dir = settings.path_process_config
        self.upload_dir.mkdir(exist_ok=True)
        self.process_dir.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def _global_script_slot(self, job_id: str):
        """
        Global (all-job-types) concurrency gate for external script execution.

        Queued semantics:
        - Keep status as Submitted
        - Write current_step='排队中（等待资源）' at most once while waiting
        """
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
            yield
        finally:
            GLOBAL_TASK_SEM.release()
    
    # <!-- 
    # 审查上下文：
    # - 设计意图：封装数据处理的核心业务逻辑，处理文件上传、任务创建、R脚本调用等
    # - 已知局限：R脚本调用采用同步方式，大数据处理时可能阻塞，后续可改为异步或Celery任务
    # - 业务背景：实现与原PHP系统相同的数据处理功能
    # - 测试重点：文件上传保存、任务状态管理、R脚本参数传递、错误处理
    # -->
    
    async def process_genome_data(
        self,
        file: UploadFile,
        gene_nomenclature: str,
        data_type: str,
        organism: str,
        email: Optional[str] = None
    ) -> GenomeProcessResponse:
        """
        处理基因组数据
        
        Args:
            file: 上传的文件
            gene_nomenclature: 基因命名方式
            data_type: 数据类型
            organism: 物种
            email: 用户邮箱
            
        Returns:
            处理结果响应
        """
        try:
            # 生成任务ID
            job_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # 保存上传文件
            original_filename = file.filename or "unknown.txt"
            saved_file_path = await save_uploaded_file(file, self.upload_dir, job_id)
            
            # 创建任务记录
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                # job_type="genome_process",
                # status="Submitted",
                job_type=JobType.GENOME_PROCESS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps({
                    "gene_nomenclature": gene_nomenclature,
                    "data_type": data_type,
                    "organism": organism,
                    "email": email,
                    "original_filename": original_filename
                }),
                created_at=datetime.now()
            )
            self.db.add(job)
            self.db.commit()
            
            # 异步处理数据（避免阻塞主线程）
            asyncio.create_task(self._execute_genome_processing(
                job_id, saved_file_path, gene_nomenclature, data_type, organism, email
            ))
            
            return GenomeProcessResponse(
                job_id=job_id,
                status="Submitted",
                message="基因组数据处理任务已提交",
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"基因组数据处理服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Service processing failure: {str(e)}")
    
    async def process_transcriptome_data(
        self,
        file: UploadFile,
        mrna_nomenclature: str,
        data_type: str,
        organism: str,
        email: Optional[str] = None
    ) -> TranscriptomeProcessResponse:
        """
        处理转录组数据
        
        Args:
            file: 上传的文件
            mrna_nomenclature: mRNA命名方式
            data_type: 数据类型
            organism: 物种
            email: 用户邮箱
            
        Returns:
            处理结果响应
        """
        try:
            # 生成任务ID
            job_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # 保存上传文件
            original_filename = file.filename or "unknown.txt"
            saved_file_path = await save_uploaded_file(file, self.upload_dir, job_id)
            
            # 创建任务记录
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                # job_type="transcriptome_process",
                # status="Submitted",
                job_type=JobType.TRANSCRIPTOME_PROCESS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps({
                    "mrna_nomenclature": mrna_nomenclature,
                    "data_type": data_type,
                    "organism": organism,
                    "email": email,
                    "original_filename": original_filename
                }),
                created_at=datetime.now()
            )
            self.db.add(job)
            self.db.commit()
            
            # 异步处理数据
            asyncio.create_task(self._execute_transcriptome_processing(
                job_id, saved_file_path, mrna_nomenclature, data_type, organism, email
            ))
            
            return TranscriptomeProcessResponse(
                job_id=job_id,
                status="Submitted",
                message="转录组数据处理任务已提交",
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"转录组数据处理服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Service processing failure: {str(e)}")

    async def process_protein_data(
        self,
        file: UploadFile,
        protein_nomenclature: str,
        organism: str,
        email: Optional[str] = None,
    ) -> ProteinProcessResponse:
        """
        处理蛋白质数据

        - 将 Entry / RefSeq / AlphaFoldDB / Ensembl ID 映射为蛋白质 Symbol
        - 将表达值转换为 log2(value + 1) 格式，空或非法数据填充为 0
        """
        try:
            # 生成任务ID
            job_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # 保存上传文件
            original_filename = file.filename or "unknown.txt"
            saved_file_path = await save_uploaded_file(file, self.upload_dir, job_id)

            # 创建任务记录
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.PROTEIN_PROCESS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps(
                    {
                        "protein_nomenclature": protein_nomenclature,
                        "organism": organism,
                        "email": email,
                        "original_filename": original_filename,
                    },
                    ensure_ascii=False,
                ),
                created_at=datetime.now(),
            )
            self.db.add(job)
            self.db.commit()

            # 异步处理数据
            asyncio.create_task(
                self._execute_protein_processing(
                    job_id=job_id,
                    file_path=saved_file_path,
                    protein_nomenclature=protein_nomenclature,
                    organism=organism,
                    email=email,
                )
            )

            return ProteinProcessResponse(
                job_id=job_id,
                status="Submitted",
                message="蛋白质数据处理任务已提交",
                created_at=datetime.now(),
            )
        except Exception as e:
            logger.error(f"蛋白质数据处理服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Service processing failure: {str(e)}")

    async def process_integration_data(
        self,
        pheno_file: UploadFile,
        file_1: UploadFile,
        file_2: UploadFile,
        file_3: UploadFile,
        email: Optional[str] = None
    ) -> IntegrationProcessResponse:
        """
        处理多组学数据整合
        
        Args:
            pheno_file: 表型数据文件
            file_1: 组学数据文件1
            file_2: 组学数据文件2
            file_3: 组学数据文件3
            email: 用户邮箱
            
        Returns:
            处理结果响应
        """
        try:
            # 生成任务ID
            job_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # 保存上传文件
            pheno_saved = await save_uploaded_file(pheno_file, self.upload_dir, f"{job_id}_pheno")
            file1_saved = await save_uploaded_file(file_1, self.upload_dir, f"{job_id}_omics_1")
            file2_saved = await save_uploaded_file(file_2, self.upload_dir, f"{job_id}_omics_2")
            file3_saved = await save_uploaded_file(file_3, self.upload_dir, f"{job_id}_omics_3")
            
            # 创建任务记录（注意：Path 需要转成字符串才能进行 JSON 序列化）
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.INTEGRATION_PROCESS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps(
                    {
                        "email": email,
                        "pheno_file": str(pheno_saved),
                        "file_1": str(file1_saved),
                        "file_2": str(file2_saved),
                        "file_3": str(file3_saved),
                    },
                    ensure_ascii=False,
                ),
                created_at=datetime.now(),
            )
            self.db.add(job)
            self.db.commit()
            
            # 异步处理数据
            asyncio.create_task(
                self._execute_integration_processing(
                    job_id=job_id,
                    pheno_path=pheno_saved,
                    file1_path=file1_saved,
                    file2_path=file2_saved,
                    file3_path=file3_saved,
                    email=email,
                )
            )
            
            return IntegrationProcessResponse(
                job_id=job_id,
                status="Submitted",
                message="多组学数据整合任务已提交",
                created_at=datetime.now(),
            )
        except Exception as e:
            logger.error(f"多组学数据整合服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Service processing failure: {str(e)}")

    async def process_pvalue_integration(
        self,
        file_1: UploadFile,
        file_2: UploadFile,
        file_3: UploadFile,
        method: str,
        email: Optional[str] = None,
    ) -> PvalueIntegrationProcessResponse:
        """
        处理 pvalue 多组学整合
        """
        try:
            # 生成任务ID
            job_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # 保存上传文件
            file1_saved = await save_uploaded_file(file_1, self.upload_dir, f"{job_id}_omics_1")
            file2_saved = await save_uploaded_file(file_2, self.upload_dir, f"{job_id}_omics_2")
            file3_saved = await save_uploaded_file(file_3, self.upload_dir, f"{job_id}_omics_3")

            # 创建任务记录
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                # 注意：数据库中 job_type 的 ENUM 目前没有单独的 pvalue_integration 项，
                # 为避免 1265 Data truncated 错误，这里暂时复用 DATA_ANALYSIS 类型。
                # job_type=JobType.DATA_ANALYSIS,
                job_type=JobType.PVALUE_INTEGRATION,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps(
                    {
                        "email": email,
                        "method": method,
                        "file_1": str(file1_saved),
                        "file_2": str(file2_saved),
                        "file_3": str(file3_saved),
                    },
                    ensure_ascii=False,
                ),
                created_at=datetime.now(),
            )
            self.db.add(job)
            self.db.commit()

            # 异步处理数据
            asyncio.create_task(
                self._execute_pvalue_integration_processing(
                    job_id=job_id,
                    file1_path=file1_saved,
                    file2_path=file2_saved,
                    file3_path=file3_saved,
                    method=method,
                    email=email,
                )
            )

            return PvalueIntegrationProcessResponse(
                job_id=job_id,
                status="Submitted",
                message="pvalue 多组学整合任务已提交",
                created_at=datetime.now(),
            )
        except Exception as e:
            logger.error(f"pvalue 多组学整合服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Service processing failure: {str(e)}")
    
    async def _execute_genome_processing(
        self,
        job_id: str,
        file_path: Path,
        gene_nomenclature: str,
        data_type: str,
        organism: str,
        email: Optional[str]
    ):
        """执行基因组数据处理"""
        try:
            async with self._global_script_slot(job_id):
                # 更新任务状态：拿到 slot 后才进入 Processing（排队时仍为 Submitted）
                job = self.db.query(Job).filter(Job.job_id == job_id).first()
                if job:
                    job.status = JobStatus.PROCESSING
                    job.current_step = "开始处理基因组数据"
                    job.updated_at = datetime.now()
                    self.db.commit()
                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": JobStatus.PROCESSING.value,
                                "progress": 0,
                                "message": "开始处理基因组数据",
                                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                                "server_seq": next_server_seq(),
                            },
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket 状态推送失败: {e}")

            # 准备 Jobs 目录的输入文件（与原 PHP 实现兼容）
            jobs_dir = settings.path_jobs / job_id
            jobs_dir.mkdir(parents=True, exist_ok=True)
            jobs_input_file = jobs_dir / "origin.txt"
                
            # 复制上传文件到 Jobs 目录
            import shutil
            shutil.copy2(str(file_path), str(jobs_input_file))
                
            # 构建 R脚本命令（使用绝对路径）
            r_script = str(settings.path_code / "mysql2TPM.R")
            output_dir = self.process_dir / job_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 使用绝对路径确保 R 脚本能正确访问文件
            output_file = str(settings.path_jobs / job_id / "processed.txt")
                
            # 参数映射
            nomenclature_map = {"GeneID": "GeneID", "EnsemblID": "EnsemblID", "Symbol": "Symbol"}
            type_map = {"FPKM": "FPKM", "TPM": "TPM", "ReadCounts": "ReadCounts", "RPKM": "RPKM", "RPM": "RPM"}
            organism_map = {
                "homo_sapiens": "homo_sapiens",
                "mus_musculus": "mus_musculus", 
                "drosophila_melanogaster": "drosophila_melanogaster",
                "arabidopsis_thaliana": "arabidopsis_thaliana",
                "bos_taurus": "bos_taurus"
            }
                
            cmd = [
                settings.RSCRIPT_PATH, r_script,
                "-g", nomenclature_map[gene_nomenclature],
                "-d", type_map[data_type],
                "-r", organism_map[organism],
                "-i", str(jobs_input_file),
                "-o", output_file,  # 使用绝对路径
                "-h", "none",
                "-a", job_id  # 关键：传递 jobID 参数
            ]

            result = await run_subprocess(
                cmd,
                cwd=os.getcwd(),
                shell=False,
                timeout=None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=_r_mysql_subprocess_env(),
            )

            # 更新任务结果
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                if result.returncode == 0:
                    job.status = JobStatus.COMPLETED
                    job.current_step = "已完成"
                    job.result_file = output_file  # 使用绝对路径
                    job.output_params = json.dumps({"stdout": result.stdout}, ensure_ascii=False)
                    job.updated_at = datetime.now()
                    self.db.commit()  # 自己改

                                
                    # 推送完成状态
                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": "Completed",
                                "progress": 100,
                                "result_file": job.result_file,
                                "message": "基因组数据处理完成"
                            }
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket 状态推送失败: {e}")
                                    
                else:
                    job.status = JobStatus.FAILED
                    job.current_step = "处理失败"
                    _err = (result.stderr or "").strip()
                    if not _err:
                        _err = (result.stdout or "").strip()
                    job.error_message = _err or "R 脚本执行失败"
                    job.updated_at = datetime.now()
                    self.db.commit()

                    # 推送失败状态
                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": "Failed",
                                "progress": 0,
                                "error_message": job.error_message,
                                "message": "基因组数据处理失败"
                            }
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket 状态推送失败: {e}")

                logger.info(f"基因组处理完成：job_id={job_id}, status={job.status}")
                
                # 如果任务成功且提供了邮箱，发送结果邮件
                if job.status == "Completed" and email:
                    try:
                        await email_service.send_result_email(
                            to_email=email,
                            job_id=job_id,
                            analysis_type="基因组数据处理",
                            result_dir=job.result_file
                        )
                    except Exception as e:
                        logger.warning(f"邮件发送失败（不影响任务结果）: {e}")
            
        except Exception as e:
            logger.error(f"基因组处理执行失败: job_id={job_id}, error={str(e)}")
            # 更新失败状态
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.updated_at = datetime.now()
                try:
                    self.db.commit()
                except Exception:
                    # If even the failure commit fails, the status can remain stale (Processing).
                    pass
    
    async def _execute_transcriptome_processing(
        self,
        job_id: str,
        file_path: Path,
        mrna_nomenclature: str,
        data_type: str,
        organism: str,
        email: Optional[str]
    ):
        """执行转录组数据处理"""
        try:
            async with self._global_script_slot(job_id):
                # 更新任务状态：拿到 slot 后才进入 Processing（排队时仍为 Submitted）
                job = self.db.query(Job).filter(Job.job_id == job_id).first()
                if job:
                    job.status = JobStatus.PROCESSING
                    job.current_step = "开始处理转录组数据"
                    job.updated_at = datetime.now()
                    self.db.commit()
                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": JobStatus.PROCESSING.value,
                                "progress": 0,
                                "message": "开始处理转录组数据",
                                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                                "server_seq": next_server_seq(),
                            },
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket 状态推送失败: {e}")

            # 准备 Jobs 目录的输入文件（与原 PHP 实现兼容）
            jobs_dir = settings.path_jobs / job_id
            jobs_dir.mkdir(parents=True, exist_ok=True)
            jobs_input_file = jobs_dir / "origin.txt"
                
            # 复制上传文件到 Jobs 目录
            import shutil
            shutil.copy2(str(file_path), str(jobs_input_file))
                
            # 构建 R脚本命令（使用绝对路径）
            r_script = str(settings.path_code / "mrna_mysql2TPM.R")
            output_dir = self.process_dir / job_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 使用绝对路径确保 R 脚本能正确访问文件
            output_file = str(settings.path_jobs / job_id / "processed.txt")
                
            # 参数映射
            nomenclature_map = {"Refseq": "Refseq", "EnsemblID": "EnsemblID", "Transcript_name": "Transcript_name"}
            type_map = {"FPKM": "FPKM", "TPM": "TPM", "ReadCounts": "ReadCounts", "RPKM": "RPKM", "RPM": "RPM"}
            organism_map = {
                "homo_sapiens": "homo_sapiens",
                "mus_musculus": "mus_musculus",
                "drosophila_melanogaster": "drosophila_melanogaster",
                "bos_taurus": "bos_taurus"
            }
                
            cmd = [
                settings.RSCRIPT_PATH, r_script,
                "-g", nomenclature_map[mrna_nomenclature],  # 修正为 -g（与 R脚本定义一致）
                "-d", type_map[data_type],
                "-r", organism_map[organism],
                "-i", str(jobs_input_file),
                "-o", output_file,  # 使用绝对路径
                "-a", job_id  # 关键：传递 jobID 参数
            ]
            
            result = await run_subprocess(
                cmd,
                cwd=os.getcwd(),
                shell=False,
                timeout=None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=_r_mysql_subprocess_env(),
            )
                        
            # 更新任务结果
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                if result.returncode == 0:
                    job.status = JobStatus.COMPLETED
                    job.current_step = "已完成"
                    job.result_file = output_file  # 使用绝对路径
                    job.output_params = json.dumps({"stdout": result.stdout}, ensure_ascii=False)
                    job.updated_at = datetime.now()
                    self.db.commit()  # 自己改
                                
                    # 推送完成状态
                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": "Completed",
                                "progress": 100,
                                "result_file": job.result_file,
                                "message": "转录组数据处理完成"
                            }
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket 状态推送失败: {e}")
                                    
                else:
                    job.status = JobStatus.FAILED
                    job.current_step = "处理失败"
                    _err_tx = (result.stderr or "").strip()
                    if not _err_tx:
                        _err_tx = (result.stdout or "").strip()
                    job.error_message = _err_tx or "R 脚本执行失败"
                    job.updated_at = datetime.now()
                    self.db.commit()

                    # 推送失败状态
                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": "Failed",
                                "progress": 0,
                                "error_message": job.error_message,
                                "message": "转录组数据处理失败"
                            }
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket 状态推送失败: {e}")

                logger.info(f"转录组处理完成：job_id={job_id}, status={job.status}")
                
                # 如果任务成功且提供了邮箱，发送结果邮件
                if job.status == "Completed" and email:
                    try:
                        await email_service.send_result_email(
                            to_email=email,
                            job_id=job_id,
                            analysis_type="转录组数据处理",
                            result_dir=job.result_file
                        )
                    except Exception as e:
                        logger.warning(f"邮件发送失败（不影响任务结果）: {e}")
            
        except Exception as e:
            logger.error(f"转录组处理执行失败: job_id={job_id}, error={str(e)}")
            # 更新失败状态
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.updated_at = datetime.now()
                self.db.commit()  # 自己改
    async def _execute_protein_processing(
        self,
        job_id: str,
        file_path: Path,
        protein_nomenclature: str,
        organism: str,
        email: Optional[str],
    ):
        """
        执行蛋白质数据处理

        逻辑参考原 protein2.php：
        - 根据命名方式和物种，从 protein_* 表查询 Symbol
        - 生成 [命名ID, Symbol, log2(value+1)...] 结果矩阵
        """
        try:
            # 更新任务状态
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.PROCESSING
                job.updated_at = datetime.now()
                self.db.commit()

                # 通过 WebSocket 推送状态更新
                try:
                    await task_status_manager.send_task_status(
                        str(self.user.id),
                        {
                            "job_id": job_id,
                            "status": JobStatus.PROCESSING.value,
                            "progress": 0,
                            "message": "开始处理蛋白质数据",
                        },
                    )
                except Exception as e:
                    logger.debug(f"WebSocket 状态推送失败: {e}")

            # 读取上传文件
            if not file_path.exists():
                raise RuntimeError(f"输入文件不存在: {file_path}")

            with open(file_path, "r", encoding="utf-8") as f:
                raw_lines = [line.rstrip("\n\r") for line in f if line.strip()]

            if not raw_lines:
                raise RuntimeError("输入文件为空")

            header_cols = raw_lines[0].split("\t")
            if len(header_cols) < 2:
                raise RuntimeError("输入文件格式错误：至少需要一列ID和一列样本数据")

            sample_names = header_cols[1:]
            sample_count = len(sample_names)

            ids = []
            data_map = {}
            for line in raw_lines[1:]:
                cols = line.split("\t")
                if not cols or not cols[0]:
                    continue
                pid = cols[0]
                ids.append(pid)
                # 后续会根据 sample_count 自动补齐/截断
                data_map[pid] = cols[1:]

            # 映射 organism -> protein 表名
            table_map = {
                "homo_sapiens": "protein_homo_sapiens",
                "bos_taurus": "protein_bos_taurus",
                "mus_musculus": "protein_mus",
                "drosophila_melanogaster": "protein_dm",
            }
            table_name = table_map.get(organism)
            if not table_name:
                raise RuntimeError(f"不支持的物种: {organism}")

            # 查询 Symbol（参考 protein2.php 逻辑）
            engine = self.db.get_bind()
            id_to_symbol = {}
            processed_clean = {}

            def _clean_id(value: str) -> str:
                # 移除小数点及后面的所有内容（与 PHP cleanRefSeq 一致）
                if not value:
                    return ""
                return value.split(".")[0]

            with engine.connect() as conn:
                for raw_id in ids:
                    cleaned = _clean_id(raw_id)
                    if not cleaned:
                        continue

                    # 复用已处理过的 ID，避免重复查询
                    if cleaned in processed_clean:
                        id_to_symbol[raw_id] = processed_clean[cleaned]
                        continue

                    symbol = ""

                    if protein_nomenclature == "RefSeq":
                        # RefSeq 处理：先模糊匹配，再在结果中精确比对 cleaned ID
                        sql = text(
                            f"SELECT RefSeq, Symbol FROM {table_name} WHERE RefSeq LIKE :pattern"
                        )
                        rows = conn.execute(
                            sql, {"pattern": f"%{raw_id}%"}
                        ).fetchall()
                        for row in rows:
                            refseq_field = row[0] or ""
                            for db_ref in refseq_field.split(";"):
                                cleaned_db = _clean_id(db_ref.strip())
                                if cleaned_db == cleaned:
                                    symbol = row[1]
                                    break
                            if symbol:
                                break
                    else:
                        # 其它命名方式：Entry / AlphaFoldDB / Ensembl
                        if protein_nomenclature == "Ensembl":
                            col_name = "Protein_stable_ID"
                        else:
                            col_name = protein_nomenclature

                        sql = text(
                            f"SELECT Symbol FROM {table_name} WHERE {col_name} = :pid LIMIT 1"
                        )
                        row = conn.execute(sql, {"pid": raw_id}).fetchone()
                        if row:
                            symbol = row[0]

                    if symbol:
                        id_to_symbol[raw_id] = symbol
                        processed_clean[cleaned] = symbol

            # 生成输出内容：命名ID, Symbol, log2(value+1)
            jobs_dir = settings.path_jobs / job_id
            jobs_dir.mkdir(parents=True, exist_ok=True)
            output_file = jobs_dir / "processed.txt"

            lines_out = []
            header_out = (
                f"{protein_nomenclature}\tSymbol\t" + "\t".join(sample_names)
            )
            lines_out.append(header_out)

            for pid in ids:
                symbol = id_to_symbol.get(pid, "")
                sample_values = data_map.get(pid, [])

                # 补齐或截断为固定样本数
                if len(sample_values) < sample_count:
                    sample_values = sample_values + ["0"] * (
                        sample_count - len(sample_values)
                    )
                elif len(sample_values) > sample_count:
                    sample_values = sample_values[:sample_count]

                log_values = []
                for v in sample_values:
                    v_str = (v or "").strip()
                    if not v_str:
                        log_values.append("0")
                        continue
                    try:
                        num = float(v_str)
                    except ValueError:
                        num = 0.0
                    if num != 0:
                        log_val = math.log2(num + 1.0)
                        log_values.append(f"{log_val:.6f}")
                    else:
                        log_values.append("0")

                lines_out.append(f"{pid}\t{symbol}\t" + "\t".join(log_values))

            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines_out) + "\n")

            # 更新任务结果
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.COMPLETED
                job.result_file = str(output_file)
                job.output_params = json.dumps(
                    {"stdout": f"Protein process finished: {output_file}"},
                    ensure_ascii=False,
                )
                job.updated_at = datetime.now()
                self.db.commit()

                # 推送完成状态
                try:
                    await task_status_manager.send_task_status(
                        str(self.user.id),
                        {
                            "job_id": job_id,
                            "status": JobStatus.COMPLETED.value,
                            "progress": 100,
                            "result_file": job.result_file,
                            "message": "蛋白质数据处理完成",
                        },
                    )
                except Exception as e:
                    logger.debug(f"WebSocket 状态推送失败: {e}")

            logger.info(f"蛋白质处理完成：job_id={job_id}, output={output_file}")
            
            # 如果任务成功且提供了邮箱，发送结果邮件
            if email:
                try:
                    await email_service.send_result_email(
                        to_email=email,
                        job_id=job_id,
                        analysis_type="蛋白质数据处理",
                        result_dir=str(output_file)
                    )
                except Exception as e:
                    logger.warning(f"邮件发送失败（不影响任务结果）: {e}")
        except Exception as e:
            logger.error(f"蛋白质处理执行失败: job_id={job_id}, error={str(e)}")
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.updated_at = datetime.now()
                self.db.commit()
    async def _execute_integration_processing(
        self,
        job_id: str,
        pheno_path: Path,
        file1_path: Path,
        file2_path: Path,
        file3_path: Path,
        email: Optional[str],
    ):
        """执行多组学数据整合（调用 Python integration.py 脚本）"""
        try:
            # 更新任务状态
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.PROCESSING
                job.updated_at = datetime.now()
                self.db.commit()
                
                # 通过 WebSocket 推送状态更新
                try:
                    await task_status_manager.send_task_status(
                        str(self.user.id),
                        {
                            "job_id": job_id,
                            "status": JobStatus.PROCESSING.value,
                            "progress": 0,
                            "message": "开始进行多组学数据整合",
                        },
                    )
                except Exception as e:
                    logger.debug(f"WebSocket 状态推送失败: {e}")
            
            # 准备 Jobs 目录及输入文件（与原 PHP 实现保持一致）
            jobs_dir = settings.path_jobs / job_id
            jobs_dir.mkdir(parents=True, exist_ok=True)
            result_dir = jobs_dir / "result"
            result_dir.mkdir(parents=True, exist_ok=True)
            
            # 目标文件路径（integration.py 期望的命名）
            pheno_file = jobs_dir / f"{job_id}_pheno.txt"
            omics1_file = jobs_dir / f"{job_id}_omics_1.txt"
            omics2_file = jobs_dir / f"{job_id}_omics_2.txt"
            omics3_file = jobs_dir / f"{job_id}_omics_3.txt"
            output_file = result_dir / f"{job_id}_result.txt"
            
            # 将上传文件拷贝到 Jobs 目录并改名
            import shutil
            
            shutil.copy2(str(pheno_path), str(pheno_file))
            shutil.copy2(str(file1_path), str(omics1_file))
            shutil.copy2(str(file2_path), str(omics2_file))
            shutil.copy2(str(file3_path), str(omics3_file))
            
            # 构建 Python 脚本命令（与 integration.php 保持一致）
            python_exec = settings.PYTHON_EXEC_PATH
            script_path = str(settings.path_code / "train_model" / "integration.py")
            
            cmd = [
                python_exec,
                script_path,
                "--jobID",
                job_id,
                "--pheno_file",
                str(pheno_file),
                "--file_1",
                str(omics1_file),
                "--file_2",
                str(omics2_file),
                "--file_3",
                str(omics3_file),
                "--output_file",
                str(output_file),
            ]
            
            async with self._global_script_slot(job_id):
                result = await run_subprocess(
                    cmd,
                    cwd=os.getcwd(),
                    shell=False,
                    timeout=None,
                    stdout=None,
                    stderr=None,
                    text=True,
                )
            
            # 更新任务结果
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                if result.returncode == 0:
                    job.status = JobStatus.COMPLETED
                    job.current_step = "已完成"
                    job.result_file = str(output_file)
                    job.output_params = json.dumps(
                        {"stdout": result.stdout}, ensure_ascii=False
                    )
                    job.updated_at = datetime.now()
                    self.db.commit()  # 自己改

                    
                    # 推送完成状态
                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": JobStatus.COMPLETED.value,
                                "progress": 100,
                                "result_file": job.result_file,
                                "message": "多组学数据整合完成",
                            },
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket 状态推送失败: {e}")
                else:
                    job.status = JobStatus.FAILED
                    job.current_step = "处理失败"
                    job.error_message = result.stderr or "Integration 脚本执行失败"
                    job.updated_at = datetime.now()
                    self.db.commit()

                    # 推送失败状态
                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": JobStatus.FAILED.value,
                                "progress": 0,
                                "error_message": job.error_message,
                                "message": "多组学数据整合失败",
                            },
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket 状态推送失败: {e}")

                logger.info(f"多组学数据整合完成：job_id={job_id}, status={job.status}")
                
                # 如果任务成功且提供了邮箱，发送结果邮件
                if job.status == JobStatus.COMPLETED and email:
                    try:
                        await email_service.send_result_email(
                            to_email=email,
                            job_id=job_id,
                            analysis_type="多组学数据整合",
                            result_dir=str(result_dir)
                        )
                    except Exception as e:
                        logger.warning(f"邮件发送失败（不影响任务结果）: {e}")
        
        except Exception as e:
            logger.error(f"多组学数据整合执行失败: job_id={job_id}, error={str(e)}")
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.updated_at = datetime.now()
                self.db.commit()

    async def _execute_pvalue_integration_processing(
        self,
        job_id: str,
        file1_path: Path,
        file2_path: Path,
        file3_path: Path,
        method: str,
        email: Optional[str],
    ):
        """
        执行 pvalue 多组学整合（调用 R 脚本 integration_pvalue.R）
        """
        try:
            # 更新任务状态
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.PROCESSING
                job.updated_at = datetime.now()
                self.db.commit()

                # 通过 WebSocket 推送状态更新
                try:
                    await task_status_manager.send_task_status(
                        str(self.user.id),
                        {
                            "job_id": job_id,
                            "status": JobStatus.PROCESSING.value,
                            "progress": 0,
                            "message": "开始进行 pvalue 多组学整合",
                        },
                    )
                except Exception as e:
                    logger.debug(f"WebSocket 状态推送失败: {e}")

            # 准备 Jobs 目录及输出文件
            jobs_dir = settings.path_jobs / job_id
            jobs_dir.mkdir(parents=True, exist_ok=True)
            result_dir = jobs_dir / "result"
            result_dir.mkdir(parents=True, exist_ok=True)
            output_file = result_dir / f"{job_id}_result.txt"

            # 构建 R 脚本命令
            r_script = str(settings.path_code / "integration_pvalue.R")
            rscript_path = settings.RSCRIPT_PATH

            cmd = [
                rscript_path,
                r_script,
                "-a",
                str(file1_path),
                "-b",
                str(file2_path),
                "-c",
                str(file3_path),
                "-d",
                method,
                "-j",
                job_id,
                "-e",
                str(output_file),
            ]

            async with self._global_script_slot(job_id):
                result = await run_subprocess(
                    cmd,
                    cwd=os.getcwd(),
                    shell=False,
                    timeout=None,
                    stdout=None,
                    stderr=None,
                    text=True,
                )

            # 更新任务结果
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                if result.returncode == 0:
                    job.status = JobStatus.COMPLETED
                    job.current_step = "已完成"
                    job.result_file = str(output_file)
                    job.output_params = json.dumps(
                        {"stdout": result.stdout}, ensure_ascii=False
                    )
                    job.updated_at = datetime.now()
                    self.db.commit()  # 自己改


                    # 推送完成状态
                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": JobStatus.COMPLETED.value,
                                "progress": 100,
                                "result_file": job.result_file,
                                "message": "pvalue 多组学整合完成",
                            },
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket 状态推送失败: {e}")
                else:
                    job.status = JobStatus.FAILED
                    job.current_step = "处理失败"
                    job.error_message = result.stderr or "integration_pvalue.R 脚本执行失败"
                    job.updated_at = datetime.now()
                    self.db.commit()

                    # 推送失败状态
                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": JobStatus.FAILED.value,
                                "progress": 0,
                                "error_message": job.error_message,
                                "message": "pvalue 多组学整合失败",
                            },
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket 状态推送失败: {e}")

                logger.info(f"pvalue 多组学整合完成：job_id={job_id}, status={job.status}")
                
                # 如果任务成功且提供了邮箱，发送结果邮件
                if job.status == JobStatus.COMPLETED and email:
                    try:
                        await email_service.send_result_email(
                            to_email=email,
                            job_id=job_id,
                            analysis_type="pvalue多组学整合",
                            result_dir=str(result_dir)
                        )
                    except Exception as e:
                        logger.warning(f"邮件发送失败（不影响任务结果）: {e}")

        except Exception as e:
            logger.error(f"pvalue 多组学整合执行失败: job_id={job_id}, error={str(e)}")
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.updated_at = datetime.now()
                self.db.commit()