"""
数据分析服务层：处理各种生物数据分析的业务逻辑
"""
import os
import uuid
import logging
import json
import shutil
from datetime import datetime
from typing import Optional, List
from pathlib import Path
import asyncio

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from api.models.user import User
from api.models.job import Job, JobType, JobStatus
from api.schemas.analysis import (
    AnalysisResponse,
    AnalysisResultFile,
    AnalysisResultResponse,
    ComprehensiveEnrichmentRequest,
)
from api.utils.file_utils import save_uploaded_file
from api.websocket.task_manager import task_status_manager
from api.services.email_service import email_service

logger = logging.getLogger(__name__)


class AnalysisService:
    """数据分析服务类"""
    
    # 路径配置
    RSCRIPT_PATH = "/opt/anaconda/envs/R_442/bin/Rscript"
    RSCRIPT_OPTIONS = "--no-save"
    R_SCRIPTS_DIR = Path("/xp/www/AutoMATA/code/data_analysis_plot")
    JOBS_BASE_DIR = Path("/xp/www/AutoMATA/download_data/Jobs")
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.upload_dir = Path("uploaded_files")
        self.upload_dir.mkdir(exist_ok=True)
    
    def _generate_job_id(self) -> str:
        """生成任务ID"""
        return f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def _create_job_dirs(self, job_id: str) -> tuple[Path, Path]:
        """创建任务目录和结果目录"""
        job_dir = self.JOBS_BASE_DIR / job_id
        result_dir = job_dir / "result"
        job_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)
        return job_dir, result_dir
    
    async def _save_file_to_job_dir(
        self, 
        file: UploadFile, 
        job_dir: Path, 
        filename: str
    ) -> Path:
        """保存上传文件到任务目录"""
        file_path = job_dir / filename
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        await file.seek(0)  # 重置文件指针
        return file_path
    
    async def _execute_r_script(
        self,
        job_id: str,
        r_script: str,
        cmd_args: List[str],
        job_dir: Path,
        analysis_name: str,
        email: Optional[str] = None
    ) -> bool:
        """
        执行R脚本的通用方法
        
        Args:
            job_id: 任务ID
            r_script: R脚本文件名
            cmd_args: 命令行参数列表
            job_dir: 任务目录
            analysis_name: 分析名称(用于日志)
            
        Returns:
            是否执行成功
        """
        try:
            # 更新任务状态为处理中
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.PROCESSING
                job.updated_at = datetime.now()
                self.db.commit()
                
                # 推送WebSocket状态
                try:
                    await task_status_manager.send_task_status(
                        str(self.user.id),
                        {
                            "job_id": job_id,
                            "status": "Processing",
                            "progress": 0,
                            "message": f"开始{analysis_name}"
                        }
                    )
                except Exception as e:
                    logger.debug(f"WebSocket状态推送失败: {e}")
            
            # 构建完整命令
            r_script_path = str(self.R_SCRIPTS_DIR / r_script)
            cmd = f"{self.RSCRIPT_PATH} {self.RSCRIPT_OPTIONS} {r_script_path} {' '.join(cmd_args)}"
            
            # 保存命令到config文件
            config_file = job_dir / "config.txt"
            with open(config_file, "w") as f:
                f.write(f"command: {cmd}\n")
            
            # 执行R脚本
            terminal_log = job_dir / "terminal_msg.txt"
            full_cmd = f"{cmd} > {terminal_log} 2>&1"
            
            logger.info(f"执行R脚本: {full_cmd}")
            
            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            # 更新任务结果
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                result_dir = job_dir / "result"
                if process.returncode == 0:
                    job.status = JobStatus.COMPLETED
                    job.result_file = str(result_dir)
                    job.output_params = json.dumps({
                        "result_dir": str(result_dir),
                        "terminal_log": str(terminal_log)
                    }, ensure_ascii=False)
                    
                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": "Completed",
                                "progress": 100,
                                "result_file": str(result_dir),
                                "message": f"{analysis_name}完成"
                            }
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket状态推送失败: {e}")
                else:
                    # 读取错误日志
                    error_msg = ""
                    if terminal_log.exists():
                        with open(terminal_log, "r") as f:
                            error_msg = f.read()[-1000:]  # 最后1000字符
                    
                    job.status = JobStatus.FAILED
                    job.error_message = error_msg or "R脚本执行失败"
                    
                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": "Failed",
                                "progress": 0,
                                "error_message": job.error_message[:200],
                                "message": f"{analysis_name}失败"
                            }
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket状态推送失败: {e}")
                
                job.updated_at = datetime.now()
                self.db.commit()
                
                logger.info(f"{analysis_name}完成: job_id={job_id}, status={job.status}")
                
                # 如果任务成功且提供了邮箱，发送结果邮件
                if process.returncode == 0 and email:
                    try:
                        await email_service.send_result_email(
                            to_email=email,
                            job_id=job_id,
                            analysis_type=analysis_name,
                            result_dir=str(result_dir)
                        )
                    except Exception as e:
                        logger.warning(f"邮件发送失败（不影响任务结果）: {e}")
                
                return process.returncode == 0
                
        except Exception as e:
            logger.error(f"{analysis_name}执行失败: job_id={job_id}, error={str(e)}")
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.updated_at = datetime.now()
                self.db.commit()
            return False
    
    async def _run_r_script_to_log(
        self,
        r_script: str,
        cmd_args: List[str],
        log_file: Path,
        config_file: Optional[Path] = None
    ) -> int:
        """
        执行 R 脚本并将 stdout/stderr 写入指定日志文件。
        与 _execute_r_script 不同：不修改 Job 状态，不推送 WebSocket。

        Returns:
            进程退出码
        """
        r_script_path = str(self.R_SCRIPTS_DIR / r_script)
        cmd = f"{self.RSCRIPT_PATH} {self.RSCRIPT_OPTIONS} {r_script_path} {' '.join(cmd_args)}"

        if config_file is not None:
            try:
                with open(config_file, "w") as f:
                    f.write(f"command: {cmd}\n")
            except Exception as e:
                logger.debug(f"写入 config 失败（不影响执行）: {e}")

        log_file.parent.mkdir(parents=True, exist_ok=True)
        full_cmd = f"{cmd} > {log_file} 2>&1"
        logger.info(f"执行R脚本（自定义日志）: {full_cmd}")

        process = await asyncio.create_subprocess_shell(
            full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return int(process.returncode or 0)

    # ==================== PCA 分析 ====================
    
    async def analyze_pca(
        self,
        file: UploadFile,
        confidence: float = 0.95,
        boundary: str = "FALSE",
        permanova: str = "FALSE",
        method: Optional[str] = None,
        email: Optional[str] = None
    ) -> AnalysisResponse:
        """PCA主成分分析"""
        try:
            job_id = self._generate_job_id()
            job_dir, result_dir = self._create_job_dirs(job_id)
            
            # 保存数据文件
            data_file = await self._save_file_to_job_dir(
                file, job_dir, f"{job_id}_data.txt"
            )
            
            # 创建任务记录
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.DATA_ANALYSIS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps({
                    "analysis_type": "pca",
                    "confidence": confidence,
                    "boundary": boundary,
                    "permanova": permanova,
                    "method": method,
                    "email": email,
                    "original_filename": file.filename
                }, ensure_ascii=False),
                created_at=datetime.now()
            )
            self.db.add(job)
            self.db.commit()
            
            # 异步执行分析
            asyncio.create_task(self._execute_pca_analysis(
                job_id, data_file, job_dir, confidence, boundary, permanova, method, email
            ))
            
            return AnalysisResponse(
                job_id=job_id,
                status="Submitted",
                message="PCA分析任务已提交",
                created_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"PCA分析服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")
    
    async def _execute_pca_analysis(
        self,
        job_id: str,
        data_file: Path,
        job_dir: Path,
        confidence: float,
        boundary: str,
        permanova: str,
        method: Optional[str],
        email: Optional[str] = None
    ):
        """执行PCA分析"""
        cmd_args = [
            f"-i {data_file}",
            f"-j {job_id}",
            f"-c {confidence}",
            f"-b {boundary}",
            f"-p {permanova}"
        ]
        if permanova == "TRUE" and method:
            cmd_args.append(f"-m {method}")
        
        await self._execute_r_script(job_id, "pca.R", cmd_args, job_dir, "PCA分析", email)
    
    # ==================== 相关性热图 ====================
    
    async def analyze_correlation_heatmap(
        self,
        file: UploadFile,
        email: Optional[str] = None
    ) -> AnalysisResponse:
        """相关性热图分析"""
        try:
            job_id = self._generate_job_id()
            job_dir, result_dir = self._create_job_dirs(job_id)
            
            data_file = await self._save_file_to_job_dir(
                file, job_dir, f"{job_id}_data.txt"
            )
            
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.DATA_ANALYSIS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps({
                    "analysis_type": "correlation_heatmap",
                    "email": email,
                    "original_filename": file.filename
                }, ensure_ascii=False),
                created_at=datetime.now()
            )
            self.db.add(job)
            self.db.commit()
            
            asyncio.create_task(self._execute_correlation_heatmap(
                job_id, data_file, job_dir, email
            ))
            
            return AnalysisResponse(
                job_id=job_id,
                status="Submitted",
                message="相关性热图分析任务已提交",
                created_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"相关性热图分析服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")
    
    async def _execute_correlation_heatmap(
        self,
        job_id: str,
        data_file: Path,
        job_dir: Path,
        email: Optional[str] = None
    ):
        """执行相关性热图分析"""
        cmd_args = [f"-i {data_file}", f"-j {job_id}"]
        await self._execute_r_script(job_id, "cor_heatmap.r", cmd_args, job_dir, "相关性热图分析", email)
    
    # ==================== 火山图 ====================
    
    async def analyze_volcano(
        self,
        file: UploadFile,
        gmt_file: Optional[UploadFile] = None,
        gene_sig: Optional[str] = None,
        fc_thr: float = 1.0,
        padj_thr: float = 0.05,
        top: int = 10,
        top_fc_thr: float = 1.0,
        top_padj_thr: float = 0.05,
        email: Optional[str] = None
    ) -> AnalysisResponse:
        """火山图分析"""
        try:
            job_id = self._generate_job_id()
            job_dir, result_dir = self._create_job_dirs(job_id)
            
            data_file = await self._save_file_to_job_dir(
                file, job_dir, f"{job_id}_data.txt"
            )
            
            gmt_path = "none"
            if gmt_file:
                gmt_saved = await self._save_file_to_job_dir(
                    gmt_file, job_dir, f"{job_id}_data2.gmt"
                )
                gmt_path = str(gmt_saved)
            
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.DATA_ANALYSIS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps({
                    "analysis_type": "volcano",
                    "gene_sig": gene_sig,
                    "fc_thr": fc_thr,
                    "padj_thr": padj_thr,
                    "top": top,
                    "top_fc_thr": top_fc_thr,
                    "top_padj_thr": top_padj_thr,
                    "email": email,
                    "original_filename": file.filename
                }, ensure_ascii=False),
                created_at=datetime.now()
            )
            self.db.add(job)
            self.db.commit()
            
            asyncio.create_task(self._execute_volcano_analysis(
                job_id, data_file, gmt_path, job_dir, gene_sig, fc_thr, 
                padj_thr, top, top_fc_thr, top_padj_thr, email
            ))
            
            return AnalysisResponse(
                job_id=job_id,
                status="Submitted",
                message="火山图分析任务已提交",
                created_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"火山图分析服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")
    
    async def _execute_volcano_analysis(
        self, job_id: str, data_file: Path, gmt_path: str, job_dir: Path,
        gene_sig: Optional[str], fc_thr: float, padj_thr: float,
        top: int, top_fc_thr: float, top_padj_thr: float,
        email: Optional[str] = None
    ):
        """执行火山图分析"""
        cmd_args = [
            f"-i {data_file}",
            f"-j {job_id}",
            f"-g {gmt_path}",
            f"--fc_thr {fc_thr}",
            f"--padj_thr {padj_thr}",
            f"--top {top}",
            f"--top_fc_thr {top_fc_thr}",
            f"--top_padj_thr {top_padj_thr}"
        ]
        if gene_sig:
            cmd_args.append(f"--gene_sig {gene_sig}")
        
        await self._execute_r_script(job_id, "volcano_gsea_padj.R", cmd_args, job_dir, "火山图分析", email)
    
    # ==================== 韦恩图 ====================
    
    async def analyze_venn(
        self,
        file: UploadFile,
        plot_type: str = "venn",
        email: Optional[str] = None
    ) -> AnalysisResponse:
        """韦恩图分析"""
        try:
            job_id = self._generate_job_id()
            job_dir, result_dir = self._create_job_dirs(job_id)
            
            data_file = await self._save_file_to_job_dir(
                file, job_dir, f"{job_id}_data.txt"
            )
            
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.DATA_ANALYSIS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps({
                    "analysis_type": "venn",
                    "plot_type": plot_type,
                    "email": email,
                    "original_filename": file.filename
                }, ensure_ascii=False),
                created_at=datetime.now()
            )
            self.db.add(job)
            self.db.commit()
            
            asyncio.create_task(self._execute_venn_analysis(
                job_id, data_file, job_dir, plot_type, email
            ))
            
            return AnalysisResponse(
                job_id=job_id,
                status="Submitted",
                message="韦恩图分析任务已提交",
                created_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"韦恩图分析服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")
    
    async def _execute_venn_analysis(
        self, job_id: str, data_file: Path, job_dir: Path, plot_type: str,
        email: Optional[str] = None
    ):
        """执行韦恩图分析"""
        cmd_args = [f"-i {data_file}", f"-j {job_id}", f"-t {plot_type}"]
        await self._execute_r_script(job_id, "venn.R", cmd_args, job_dir, "韦恩图分析", email)
    
    # ==================== 差异基因聚类热图 ====================
    
    async def analyze_gene_cluster_heatmap(
        self,
        file: UploadFile,
        row_annotation_file: Optional[UploadFile] = None,
        col_annotation_file: Optional[UploadFile] = None,
        show_col_name: str = "TRUE",
        show_row_name: str = "FALSE",
        clustering_dis_row: str = "euclidean",
        clustering_dis_col: str = "euclidean",
        scale: str = "row",
        annotation_type: str = "only_data",
        group: str = "FALSE",
        email: Optional[str] = None
    ) -> AnalysisResponse:
        """差异基因聚类热图分析"""
        try:
            job_id = self._generate_job_id()
            job_dir, result_dir = self._create_job_dirs(job_id)
            
            data_file = await self._save_file_to_job_dir(
                file, job_dir, f"{job_id}_data.txt"
            )
            
            row_file_path = None
            col_file_path = None
            
            if row_annotation_file and annotation_type in ["data_with_row_annotation", "data_with_row_col"]:
                row_file_path = await self._save_file_to_job_dir(
                    row_annotation_file, job_dir, f"{job_id}_row.txt"
                )
            
            if col_annotation_file and annotation_type in ["data_with_col_annotation", "data_with_row_col"]:
                col_file_path = await self._save_file_to_job_dir(
                    col_annotation_file, job_dir, f"{job_id}_col.txt"
                )
            
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.DATA_ANALYSIS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps({
                    "analysis_type": "gene_cluster_heatmap",
                    "show_col_name": show_col_name,
                    "show_row_name": show_row_name,
                    "clustering_dis_row": clustering_dis_row,
                    "clustering_dis_col": clustering_dis_col,
                    "scale": scale,
                    "annotation_type": annotation_type,
                    "group": group,
                    "email": email,
                    "original_filename": file.filename
                }, ensure_ascii=False),
                created_at=datetime.now()
            )
            self.db.add(job)
            self.db.commit()
            
            asyncio.create_task(self._execute_gene_cluster_heatmap(
                job_id, data_file, job_dir, row_file_path, col_file_path,
                show_col_name, show_row_name, clustering_dis_row, clustering_dis_col,
                scale, annotation_type, group, email
            ))
            
            return AnalysisResponse(
                job_id=job_id,
                status="Submitted",
                message="差异基因聚类热图分析任务已提交",
                created_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"差异基因聚类热图分析服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")
    
    async def _execute_gene_cluster_heatmap(
        self, job_id: str, data_file: Path, job_dir: Path,
        row_file: Optional[Path], col_file: Optional[Path],
        show_col_name: str, show_row_name: str,
        clustering_dis_row: str, clustering_dis_col: str,
        scale: str, annotation_type: str, group: str,
        email: Optional[str] = None
    ):
        """执行差异基因聚类热图分析"""
        cmd_args = [
            f"-i {data_file}",
            f"-j {job_id}",
            f"-a {annotation_type}",
            f"-b {show_row_name}",
            f"-c {show_col_name}",
            f"-d {clustering_dis_row}",
            f"-e {clustering_dis_col}",
            f"-h {scale}",
            f"-k {group}"
        ]
        if row_file:
            cmd_args.append(f"-f {row_file}")
        if col_file:
            cmd_args.append(f"-g {col_file}")
        
        await self._execute_r_script(job_id, "df_cluster_heatmap.R", cmd_args, job_dir, "差异基因聚类热图分析", email)
    
    # ==================== 哑铃图 ====================
    
    async def analyze_dumbbell(
        self,
        file: UploadFile,
        x_label: Optional[str] = None,
        mark_fams: Optional[str] = None,
        email: Optional[str] = None
    ) -> AnalysisResponse:
        """哑铃图分析"""
        try:
            job_id = self._generate_job_id()
            job_dir, result_dir = self._create_job_dirs(job_id)
            
            data_file = await self._save_file_to_job_dir(
                file, job_dir, f"{job_id}_data.txt"
            )
            
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.DATA_ANALYSIS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps({
                    "analysis_type": "dumbbell",
                    "x_label": x_label,
                    "mark_fams": mark_fams,
                    "email": email,
                    "original_filename": file.filename
                }, ensure_ascii=False),
                created_at=datetime.now()
            )
            self.db.add(job)
            self.db.commit()
            
            asyncio.create_task(self._execute_dumbbell_analysis(
                job_id, data_file, job_dir, x_label, mark_fams, email
            ))
            
            return AnalysisResponse(
                job_id=job_id,
                status="Submitted",
                message="哑铃图分析任务已提交",
                created_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"哑铃图分析服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")
    
    async def _execute_dumbbell_analysis(
        self, job_id: str, data_file: Path, job_dir: Path,
        x_label: Optional[str], mark_fams: Optional[str],
        email: Optional[str] = None
    ):
        """执行哑铃图分析"""
        cmd_args = [f"-i {data_file}", f"-j {job_id}"]
        if x_label:
            cmd_args.append(f"-a {x_label}")
        if mark_fams:
            cmd_args.append(f"-b {mark_fams}")
        
        await self._execute_r_script(job_id, "dumbbell.R", cmd_args, job_dir, "哑铃图分析", email)
    
    # ==================== 哑铃条形图 ====================
    
    async def analyze_dumbbell_bar(
        self,
        file1: UploadFile,
        file2: UploadFile,
        x_label: Optional[str] = None,
        mark_fams: Optional[str] = None,
        email: Optional[str] = None
    ) -> AnalysisResponse:
        """哑铃条形图分析"""
        try:
            job_id = self._generate_job_id()
            job_dir, result_dir = self._create_job_dirs(job_id)
            
            data_file1 = await self._save_file_to_job_dir(
                file1, job_dir, f"{job_id}_data1.txt"
            )
            data_file2 = await self._save_file_to_job_dir(
                file2, job_dir, f"{job_id}_data2.txt"
            )
            
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.DATA_ANALYSIS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps({
                    "analysis_type": "dumbbell_bar",
                    "x_label": x_label,
                    "mark_fams": mark_fams,
                    "email": email,
                    "original_filename1": file1.filename,
                    "original_filename2": file2.filename
                }, ensure_ascii=False),
                created_at=datetime.now()
            )
            self.db.add(job)
            self.db.commit()
            
            asyncio.create_task(self._execute_dumbbell_bar_analysis(
                job_id, data_file1, job_dir, x_label, mark_fams, email
            ))
            
            return AnalysisResponse(
                job_id=job_id,
                status="Submitted",
                message="哑铃条形图分析任务已提交",
                created_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"哑铃条形图分析服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")
    
    async def _execute_dumbbell_bar_analysis(
        self, job_id: str, data_file: Path, job_dir: Path,
        x_label: Optional[str], mark_fams: Optional[str],
        email: Optional[str] = None
    ):
        """执行哑铃条形图分析"""
        cmd_args = [f"-i {data_file}", f"-j {job_id}", f"-c {data_file}"]
        if x_label:
            cmd_args.append(f"-a {x_label}")
        if mark_fams:
            cmd_args.append(f"-b {mark_fams}")
        
        await self._execute_r_script(job_id, "dumbbell_bar.R", cmd_args, job_dir, "哑铃条形图分析", email)
    
    # ==================== GO富集分析 ====================
    
    async def analyze_go_enrichment(
        self,
        file: UploadFile,
        organism: str = "Homo_sapiens",
        pvalue: float = 0.05,
        qvalue: float = 0.1,
        plot_type: str = "bubble",
        term_num: int = 10,
        correction: str = "BH",
        email: Optional[str] = None
    ) -> AnalysisResponse:
        """GO富集分析"""
        try:
            job_id = self._generate_job_id()
            job_dir, result_dir = self._create_job_dirs(job_id)
            
            data_file = await self._save_file_to_job_dir(
                file, job_dir, f"{job_id}_data.txt"
            )
            
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.DATA_ANALYSIS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps({
                    "analysis_type": "go_enrichment",
                    "organism": organism,
                    "pvalue": pvalue,
                    "qvalue": qvalue,
                    "plot_type": plot_type,
                    "term_num": term_num,
                    "correction": correction,
                    "email": email,
                    "original_filename": file.filename
                }, ensure_ascii=False),
                created_at=datetime.now()
            )
            self.db.add(job)
            self.db.commit()
            
            asyncio.create_task(self._execute_go_enrichment(
                job_id, data_file, job_dir, organism, pvalue, qvalue, 
                plot_type, term_num, correction, email
            ))
            
            return AnalysisResponse(
                job_id=job_id,
                status="Submitted",
                message="GO富集分析任务已提交",
                created_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"GO富集分析服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")
    
    async def _execute_go_enrichment(
        self, job_id: str, data_file: Path, job_dir: Path,
        organism: str, pvalue: float, qvalue: float,
        plot_type: str, term_num: int, correction: str,
        email: Optional[str] = None
    ):
        """执行GO富集分析"""
        cmd_args = [
            f"-i {data_file}",
            f"-j {job_id}",
            f"-a {plot_type}",
            f"-b {organism}",
            f"-c {pvalue}",
            f"-d {qvalue}",
            f"-g {correction}"
        ]
        if plot_type in ["chord", "cluster", "bubble", "barplot"]:
            cmd_args.append(f"-e {term_num}")
        
        await self._execute_r_script(job_id, "go_enrichment.R", cmd_args, job_dir, "GO富集分析", email)
    
    # ==================== KEGG富集分析 ====================
    
    async def analyze_kegg_enrichment(
        self,
        file: UploadFile,
        organism: str = "hsa",
        pvalue: float = 0.05,
        qvalue: float = 0.1,
        plot_type: str = "bubble",
        term_num: int = 10,
        correction: str = "BH",
        email: Optional[str] = None
    ) -> AnalysisResponse:
        """KEGG富集分析"""
        try:
            job_id = self._generate_job_id()
            job_dir, result_dir = self._create_job_dirs(job_id)
            
            data_file = await self._save_file_to_job_dir(
                file, job_dir, f"{job_id}_data.txt"
            )
            
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.DATA_ANALYSIS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps({
                    "analysis_type": "kegg_enrichment",
                    "organism": organism,
                    "pvalue": pvalue,
                    "qvalue": qvalue,
                    "plot_type": plot_type,
                    "term_num": term_num,
                    "correction": correction,
                    "email": email,
                    "original_filename": file.filename
                }, ensure_ascii=False),
                created_at=datetime.now()
            )
            self.db.add(job)
            self.db.commit()
            
            asyncio.create_task(self._execute_kegg_enrichment(
                job_id, data_file, job_dir, organism, pvalue, qvalue,
                plot_type, term_num, correction, email
            ))
            
            return AnalysisResponse(
                job_id=job_id,
                status="Submitted",
                message="KEGG富集分析任务已提交",
                created_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"KEGG富集分析服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")
    
    async def _execute_kegg_enrichment(
        self, job_id: str, data_file: Path, job_dir: Path,
        organism: str, pvalue: float, qvalue: float,
        plot_type: str, term_num: int, correction: str,
        email: Optional[str] = None
    ):
        """执行KEGG富集分析"""
        cmd_args = [
            f"-i {data_file}",
            f"-j {job_id}",
            f"-a {plot_type}",
            f"-b {organism}",
            f"-c {pvalue}",
            f"-d {qvalue}",
            f"-g {correction}"
        ]
        if plot_type in ["chord", "cluster", "bubble"]:
            cmd_args.append(f"-e {term_num}")
        
        await self._execute_r_script(job_id, "kegg_enrichment.R", cmd_args, job_dir, "KEGG富集分析", email)
    
    # ==================== PPI分析 ====================
    
    async def analyze_ppi(
        self,
        file: UploadFile,
        organism: str = "Homo_sapiens",
        nomenclature: str = "SYMBOL",
        threshold: float = 0.4,
        plot_type: str = "network",
        show_nodes: int = 50,
        email: Optional[str] = None
    ) -> AnalysisResponse:
        """PPI蛋白互作网络分析"""
        try:
            job_id = self._generate_job_id()
            job_dir, result_dir = self._create_job_dirs(job_id)
            
            data_file = await self._save_file_to_job_dir(
                file, job_dir, f"{job_id}_data.txt"
            )
            
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.DATA_ANALYSIS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps({
                    "analysis_type": "ppi",
                    "organism": organism,
                    "nomenclature": nomenclature,
                    "threshold": threshold,
                    "plot_type": plot_type,
                    "show_nodes": show_nodes,
                    "email": email,
                    "original_filename": file.filename
                }, ensure_ascii=False),
                created_at=datetime.now()
            )
            self.db.add(job)
            self.db.commit()
            
            asyncio.create_task(self._execute_ppi_analysis(
                job_id, data_file, job_dir, organism, nomenclature,
                threshold, plot_type, show_nodes, email
            ))
            
            return AnalysisResponse(
                job_id=job_id,
                status="Submitted",
                message="PPI分析任务已提交",
                created_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"PPI分析服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")
    
    async def _execute_ppi_analysis(
        self, job_id: str, data_file: Path, job_dir: Path,
        organism: str, nomenclature: str, threshold: float,
        plot_type: str, show_nodes: int,
        email: Optional[str] = None
    ):
        """执行PPI分析"""
        cmd_args = [
            f"-i {data_file}",
            f"-j {job_id}",
            f"-a {nomenclature}",
            f"-b {organism}",
            f"-c {threshold}",
            f"-d {plot_type}",
            f"-e {show_nodes}"
        ]
        await self._execute_r_script(job_id, "ppi.R", cmd_args, job_dir, "PPI分析", email)
    
    # ==================== 综合分析(差异表达分析) ====================
    
    async def analyze_comprehensive(
        self,
        expression_file: UploadFile,
        group_file: UploadFile,
        organism: str = "Homo_sapiens",
        fc_threshold: float = 1.0,
        padj_threshold: float = 0.05,
        data_type: str = "read_counts",
        correction: str = "BH",
        email: Optional[str] = None
    ) -> AnalysisResponse:
        """综合分析(差异表达分析)"""
        try:
            job_id = self._generate_job_id()
            job_dir, result_dir = self._create_job_dirs(job_id)
            
            expr_file = await self._save_file_to_job_dir(
                expression_file, job_dir, f"{job_id}_data.txt"
            )
            info_file = await self._save_file_to_job_dir(
                group_file, job_dir, f"{job_id}_info.txt"
            )
            
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.DATA_ANALYSIS,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps({
                    "analysis_type": "comprehensive",
                    "organism": organism,
                    "fc_threshold": fc_threshold,
                    "padj_threshold": padj_threshold,
                    "data_type": data_type,
                    "correction": correction,
                    "email": email,
                    "expression_filename": expression_file.filename,
                    "group_filename": group_file.filename
                }, ensure_ascii=False),
                created_at=datetime.now()
            )
            self.db.add(job)
            self.db.commit()
            
            asyncio.create_task(self._execute_comprehensive_analysis(
                job_id, expr_file, info_file, job_dir, organism,
                fc_threshold, padj_threshold, data_type, correction, email
            ))
            
            return AnalysisResponse(
                job_id=job_id,
                status="Submitted",
                message="综合分析任务已提交",
                created_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"综合分析服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")
    
    async def _execute_comprehensive_analysis(
        self, job_id: str, expr_file: Path, info_file: Path, job_dir: Path,
        organism: str, fc_threshold: float, padj_threshold: float,
        data_type: str, correction: str, email: Optional[str] = None
    ):
        """执行综合分析"""
        # 根据数据类型选择R脚本
        if data_type == "read_counts":
            r_script = "../DESeq2_read_count.R"  # 相对于 data_analysis_plot 目录
        else:
            r_script = "../limma_fpkm_df.R"
        
        cmd_args = [
            f"-i {expr_file}",
            f"-k {info_file}",
            f"-j {job_id}",
            f"-c {fc_threshold}",
            f"-d {padj_threshold}",
            f"-e {correction}"
        ]
        
        # 使用绝对路径执行
        r_script_path = f"/xp/www/AutoMATA/code/{r_script.replace('../', '')}"
        
        try:
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.PROCESSING
                job.updated_at = datetime.now()
                self.db.commit()

                # 与其它分析保持一致：主动推送 WebSocket 状态，确保前端显示 processing 动画
                try:
                    await task_status_manager.send_task_status(
                        str(self.user.id),
                        {
                            "job_id": job_id,
                            "status": "Processing",
                            "progress": 0,
                            "message": "开始综合差异表达分析"
                        }
                    )
                except Exception as e:
                    logger.debug(f"WebSocket状态推送失败（综合分析 Processing）: {e}")
            
            cmd = f"{self.RSCRIPT_PATH} {self.RSCRIPT_OPTIONS} {r_script_path} {' '.join(cmd_args)}"
            
            config_file = job_dir / "config.txt"
            with open(config_file, "w") as f:
                f.write(f"command: {cmd}\n")
            
            terminal_log = job_dir / "terminal_msg.txt"
            full_cmd = f"{cmd} > {terminal_log} 2>&1"
            
            logger.info(f"执行综合分析R脚本: {full_cmd}")
            
            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                result_dir = job_dir / "result"
                if process.returncode == 0:
                    job.status = JobStatus.COMPLETED
                    job.result_file = str(result_dir)

                    # 推送 completed 状态（前端轮询兜底，这里用于保持一致体验）
                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": "Completed",
                                "progress": 100,
                                "result_file": str(result_dir),
                                "message": "综合差异表达分析完成"
                            }
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket状态推送失败（综合分析 Completed）: {e}")
                    
                    # 发送邮件通知
                    if email:
                        try:
                            await email_service.send_result_email(
                                to_email=email,
                                job_id=job_id,
                                analysis_type="综合分析",
                                result_dir=str(result_dir)
                            )
                        except Exception as e:
                            logger.warning(f"邮件发送失败（不影响任务结果）: {e}")
                else:
                    error_msg = ""
                    if terminal_log.exists():
                        with open(terminal_log, "r") as f:
                            error_msg = f.read()[-1000:]
                    job.status = JobStatus.FAILED
                    job.error_message = error_msg or "R脚本执行失败"

                    try:
                        await task_status_manager.send_task_status(
                            str(self.user.id),
                            {
                                "job_id": job_id,
                                "status": "Failed",
                                "progress": 0,
                                "error_message": job.error_message,
                                "message": "综合差异表达分析失败"
                            }
                        )
                    except Exception as e:
                        logger.debug(f"WebSocket状态推送失败（综合分析 Failed）: {e}")
                
                job.updated_at = datetime.now()
                self.db.commit()
                
        except Exception as e:
            logger.error(f"综合分析执行失败: job_id={job_id}, error={str(e)}")
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.updated_at = datetime.now()
                self.db.commit()

    # ==================== 综合分析：继续 GO/KEGG 富集 ====================

    async def analyze_comprehensive_enrichment(
        self,
        job_id: str,
        req: ComprehensiveEnrichmentRequest
    ) -> AnalysisResponse:
        """
        在综合分析结果基础上继续执行 GO + KEGG 富集（沿用同一 job_id）。
        串行执行：GO -> KEGG。
        """
        try:
            job = self.db.query(Job).filter(
                Job.job_id == job_id,
                Job.user_id == self.user.id
            ).first()
            if not job:
                raise HTTPException(status_code=404, detail="任务不存在")

            base_dir = Path("/xp/www/AutoMATA/download_data/Jobs")
            job_dir = base_dir / job_id
            result_dir = job_dir / "result"
            if not result_dir.exists():
                raise HTTPException(status_code=400, detail="该任务尚未生成 result 目录，无法继续富集分析")

            select_file = result_dir / f"select_{req.type_analysis}.txt"
            if not select_file.exists():
                raise HTTPException(status_code=400, detail=f"缺少差异筛选文件: {select_file.name}")

            # 记录追加参数（不影响主流程）
            try:
                existing = {}
                if job.output_params:
                    existing = json.loads(job.output_params) if isinstance(job.output_params, str) else {}
                existing["comprehensive_enrichment"] = {
                    "type_analysis": req.type_analysis,
                    "go": {
                        "organism": req.go_organism,
                        "pvalue": req.go_pvalue,
                        "qvalue": req.go_qvalue,
                        "plot_type": req.go_plot_type,
                        "term_num": req.go_term_num,
                        "correction": req.go_correction,
                    },
                    "kegg": {
                        "organism": req.kegg_organism,
                        "pvalue": req.kegg_pvalue,
                        "qvalue": req.kegg_qvalue,
                        "plot_type": req.kegg_plot_type,
                        "term_num": req.kegg_term_num,
                        "correction": req.kegg_correction,
                    },
                }
                job.output_params = json.dumps(existing, ensure_ascii=False)
                job.updated_at = datetime.now()
                self.db.commit()
            except Exception:
                self.db.rollback()

            asyncio.create_task(self._execute_comprehensive_enrichment(job_id, job_dir, req))

            return AnalysisResponse(
                job_id=job_id,
                status="Submitted",
                message="综合分析继续GO+KEGG富集任务已提交",
                created_at=datetime.now()
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"综合分析继续富集服务失败: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"服务处理失败: {str(e)}")

    async def _execute_comprehensive_enrichment(
        self,
        job_id: str,
        job_dir: Path,
        req: ComprehensiveEnrichmentRequest
    ):
        """串行执行 GO -> KEGG 富集分析（沿用同一 job_id），并分别写独立日志文件"""
        result_dir = job_dir / "result"
        select_file = result_dir / f"select_{req.type_analysis}.txt"

        job = self.db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == self.user.id
        ).first()
        if not job:
            return

        # 标记处理中（一次提交只在最终完成时推 Completed，避免前端误提示“已完成”）
        try:
            job.status = JobStatus.PROCESSING
            job.result_file = str(result_dir)
            job.updated_at = datetime.now()
            self.db.commit()
        except Exception as e:
            logger.debug(f"更新综合富集状态失败（不影响执行）: {e}")
            self.db.rollback()

        try:
            try:
                await task_status_manager.send_task_status(
                    str(self.user.id),
                    {
                        "job_id": job_id,
                        "status": "Processing",
                        "progress": 0,
                        "message": "开始综合分析的 GO + KEGG 富集分析"
                    }
                )
            except Exception as e:
                logger.debug(f"WebSocket状态推送失败（综合富集 Processing）: {e}")

            # GO
            go_args = [
                f"-i {select_file}",
                f"-j {job_id}",
                f"-a {req.go_plot_type}",
                f"-b {req.go_organism}",
                f"-c {req.go_pvalue}",
                f"-d {req.go_qvalue}",
                f"-f {req.type_analysis}",
                f"-g {req.go_correction}",
            ]
            if req.go_plot_type in ["chord", "cluster", "bubble", "barplot"]:
                go_args.append(f"-e {req.go_term_num}")

            go_log = job_dir / "terminal_go_msg.txt"
            go_cfg = job_dir / "config_go.txt"
            rc_go = await self._run_r_script_to_log("go_enrichment.R", go_args, go_log, go_cfg)
            if rc_go != 0:
                err_tail = ""
                try:
                    if go_log.exists():
                        with open(go_log, "r") as f:
                            err_tail = f.read()[-1200:]
                except Exception:
                    pass

                job.status = JobStatus.FAILED
                job.error_message = err_tail or "GO富集分析失败"
                job.updated_at = datetime.now()
                self.db.commit()

                try:
                    await task_status_manager.send_task_status(
                        str(self.user.id),
                        {
                            "job_id": job_id,
                            "status": "Failed",
                            "progress": 0,
                            "error_message": (job.error_message or "")[:200],
                            "message": "GO富集分析失败"
                        }
                    )
                except Exception as e:
                    logger.debug(f"WebSocket状态推送失败（综合富集 GO Failed）: {e}")
                return

            # KEGG
            kegg_args = [
                f"-i {select_file}",
                f"-j {job_id}",
                f"-a {req.kegg_plot_type}",
                f"-b {req.kegg_organism}",
                f"-c {req.kegg_pvalue}",
                f"-d {req.kegg_qvalue}",
                f"-f {req.type_analysis}",
                f"-g {req.kegg_correction}",
            ]
            if req.kegg_plot_type in ["chord", "cluster", "bubble"]:
                kegg_args.append(f"-e {req.kegg_term_num}")

            kegg_log = job_dir / "terminal_kegg_msg.txt"
            kegg_cfg = job_dir / "config_kegg.txt"
            rc_kegg = await self._run_r_script_to_log("kegg_enrichment.R", kegg_args, kegg_log, kegg_cfg)
            if rc_kegg != 0:
                err_tail = ""
                try:
                    if kegg_log.exists():
                        with open(kegg_log, "r") as f:
                            err_tail = f.read()[-1200:]
                except Exception:
                    pass

                job.status = JobStatus.FAILED
                job.error_message = err_tail or "KEGG富集分析失败"
                job.updated_at = datetime.now()
                self.db.commit()

                try:
                    await task_status_manager.send_task_status(
                        str(self.user.id),
                        {
                            "job_id": job_id,
                            "status": "Failed",
                            "progress": 0,
                            "error_message": (job.error_message or "")[:200],
                            "message": "KEGG富集分析失败"
                        }
                    )
                except Exception as e:
                    logger.debug(f"WebSocket状态推送失败（综合富集 KEGG Failed）: {e}")
                return

            # 两者都成功，才推 completed
            job.status = JobStatus.COMPLETED
            job.error_message = None
            job.updated_at = datetime.now()
            self.db.commit()

            try:
                await task_status_manager.send_task_status(
                    str(self.user.id),
                    {
                        "job_id": job_id,
                        "status": "Completed",
                        "progress": 100,
                        "result_file": str(result_dir),
                        "message": "GO + KEGG 富集分析完成"
                    }
                )
            except Exception as e:
                logger.debug(f"WebSocket状态推送失败（综合富集 Completed）: {e}")

        except Exception as e:
            logger.error(f"综合富集执行失败: job_id={job_id}, error={str(e)}")
            try:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.updated_at = datetime.now()
                self.db.commit()
            except Exception:
                self.db.rollback()
            try:
                await task_status_manager.send_task_status(
                    str(self.user.id),
                    {
                        "job_id": job_id,
                        "status": "Failed",
                        "progress": 0,
                        "error_message": str(e)[:200],
                        "message": "综合富集分析失败"
                    }
                )
            except Exception:
                pass
    
    # ==================== 获取分析结果 ====================
    
    def get_analysis_result(self, job_id: str) -> AnalysisResultResponse:
        """获取分析结果"""
        job = self.db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == self.user.id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        result_files = []
        if job.result_file and Path(job.result_file).exists():
            result_dir = Path(job.result_file)
            if result_dir.is_dir():
                for f in result_dir.iterdir():
                    if f.is_file():
                        result_files.append(AnalysisResultFile(
                            filename=f.name,
                            format=f.suffix.lstrip('.'),
                            size=f.stat().st_size,
                            path=str(f)
                        ))
        
        return AnalysisResultResponse(
            job_id=job_id,
            status=job.status.value if job.status else "Unknown",
            result_files=result_files,
            error_message=job.error_message
        )
    
    def get_result_file_path(self, job_id: str, filename: str) -> Path:
        """获取结果文件路径"""
        job = self.db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == self.user.id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if not job.result_file:
            raise HTTPException(status_code=404, detail="结果文件不存在")
        
        result_dir = Path(job.result_file)
        file_path = result_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")
        
        return file_path
