"""
数据处理服务层：处理基因组、转录组等生物数据的业务逻辑
"""
import os
import uuid
import logging
import json
from datetime import datetime
from typing import Optional
from pathlib import Path
import asyncio
from fastapi import UploadFile, HTTPException

from sqlalchemy.orm import Session
from api.models.user import User
from api.models.job import Job
from api.schemas.data_process import (
    GenomeProcessResponse,
    TranscriptomeProcessResponse
)
from api.utils.file_utils import save_uploaded_file
from api.websocket.task_manager import task_status_manager

logger = logging.getLogger(__name__)

class DataProcessService:
    """数据处理服务类"""
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.upload_dir = Path("uploaded_files")
        self.process_dir = Path("/xp/www/AutoMATA/download_data/Config")  # 使用绝对路径
        self.upload_dir.mkdir(exist_ok=True)
        self.process_dir.mkdir(parents=True, exist_ok=True)
    
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
                job_type="genome_process",
                status="Submitted",
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
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")
    
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
                job_type="transcriptome_process",
                status="Submitted",
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
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")
    
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
            # 更新任务状态
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = "Processing"
                job.updated_at = datetime.now()
                self.db.commit()
                
                # 通过 WebSocket 推送状态更新
                try:
                    await task_status_manager.send_task_status(
                        str(self.user.id),
                        {
                            "job_id": job_id,
                            "status": "Processing",
                            "progress": 0,
                            "message": "开始处理基因组数据"
                        }
                    )
                except Exception as e:
                    logger.debug(f"WebSocket 状态推送失败: {e}")
                
            # 准备 Jobs 目录的输入文件（与原 PHP 实现兼容）
            jobs_dir = Path("/xp/www/AutoMATA/download_data/Jobs") / job_id
            jobs_dir.mkdir(parents=True, exist_ok=True)
            jobs_input_file = jobs_dir / "origin.txt"
                
            # 复制上传文件到 Jobs 目录
            import shutil
            shutil.copy2(str(file_path), str(jobs_input_file))
                
            # 构建 R脚本命令（使用绝对路径）
            r_script = "/xp/www/AutoMATA/code/mysql2TPM.R"
            output_dir = self.process_dir / job_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 使用绝对路径确保 R 脚本能正确访问文件
            output_file = "/xp/www/AutoMATA/download_data/Config/" + job_id + "/processed.txt"
                
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
                "Rscript", r_script,
                "-g", nomenclature_map[gene_nomenclature],
                "-d", type_map[data_type],
                "-r", organism_map[organism],
                "-i", str(jobs_input_file),
                "-o", output_file,  # 使用绝对路径
                "-a", job_id  # 关键：传递 jobID 参数
            ]
            
            # 执行 R脚本（使用完整的R环境路径）
            import subprocess
            rscript_path = "/opt/anaconda/envs/R_442/bin/Rscript"
            cmd[0] = rscript_path  # 替换第一个参数为完整路径
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
                        
            # 更新任务结果
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                if result.returncode == 0:
                    job.status = "Completed"
                    job.result_file = output_file  # 使用绝对路径
                    job.output_params = json.dumps({"stdout": result.stdout}, ensure_ascii=False)
                                
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
                    job.status = "Failed"
                    job.error_message = result.stderr or "R 脚本执行失败"
                                
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
                job.updated_at = datetime.now()
                self.db.commit()
                            
                logger.info(f"基因组处理完成：job_id={job_id}, status={job.status}")
            
        except Exception as e:
            logger.error(f"基因组处理执行失败: job_id={job_id}, error={str(e)}")
            # 更新失败状态
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = "Failed"
                job.error_message = str(e)
                job.updated_at = datetime.now()
                self.db.commit()
    
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
            # 更新任务状态
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = "Processing"
                job.updated_at = datetime.now()
                self.db.commit()
                
                # 通过 WebSocket 推送状态更新
                try:
                    await task_status_manager.send_task_status(
                        str(self.user.id),
                        {
                            "job_id": job_id,
                            "status": "Processing",
                            "progress": 0,
                            "message": "开始处理转录组数据"
                        }
                    )
                except Exception as e:
                    logger.debug(f"WebSocket 状态推送失败: {e}")
                
            # 准备 Jobs 目录的输入文件（与原 PHP 实现兼容）
            jobs_dir = Path("/xp/www/AutoMATA/download_data/Jobs") / job_id
            jobs_dir.mkdir(parents=True, exist_ok=True)
            jobs_input_file = jobs_dir / "origin.txt"
                
            # 复制上传文件到 Jobs 目录
            import shutil
            shutil.copy2(str(file_path), str(jobs_input_file))
                
            # 构建 R脚本命令（使用绝对路径）
            r_script = "/xp/www/AutoMATA/code/mrna_mysql2TPM.R"
            output_dir = self.process_dir / job_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 使用绝对路径确保 R 脚本能正确访问文件
            output_file = "/xp/www/AutoMATA/download_data/Config/" + job_id + "/processed.txt"
                
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
                "Rscript", r_script,
                "-g", nomenclature_map[mrna_nomenclature],  # 修正为 -g（与 R脚本定义一致）
                "-d", type_map[data_type],
                "-r", organism_map[organism],
                "-i", str(jobs_input_file),
                "-o", output_file,  # 使用绝对路径
                "-a", job_id  # 关键：传递 jobID 参数
            ]
            
            # 执行 R脚本（使用完整的R环境路径）
            import subprocess
            rscript_path = "/opt/anaconda/envs/R_442/bin/Rscript"
            cmd[0] = rscript_path  # 替换第一个参数为完整路径
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
                        
            # 更新任务结果
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                if result.returncode == 0:
                    job.status = "Completed"
                    job.result_file = output_file  # 使用绝对路径
                    job.output_params = json.dumps({"stdout": result.stdout}, ensure_ascii=False)
                                
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
                    job.status = "Failed"
                    job.error_message = result.stderr or "R 脚本执行失败"
                                
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
                job.updated_at = datetime.now()
                self.db.commit()
                            
                logger.info(f"转录组处理完成：job_id={job_id}, status={job.status}")
            
        except Exception as e:
            logger.error(f"转录组处理执行失败: job_id={job_id}, error={str(e)}")
            # 更新失败状态
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = "Failed"
                job.error_message = str(e)
                job.updated_at = datetime.now()
                self.db.commit()