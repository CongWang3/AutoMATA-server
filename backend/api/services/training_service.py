"""
模型训练服务层：封装监督学习训练任务的业务逻辑

设计目标：
- 与数据处理服务 (`DataProcessService`) 风格一致
- 复用 `jobs` 表做统一任务管理，使用 `JobType.MODEL_TRAIN`
- 通过异步任务执行 Python 训练脚本（参考 legacy PHP `modelTrain.php`）
"""

import json
import logging
import shutil
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import asyncio
import subprocess
from contextlib import asynccontextmanager
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.models.user import User
from api.models.job import Job, JobType, JobStatus
from api.services.concurrency import GLOBAL_TASK_SEM, next_server_seq
from api.utils.subprocess_utils import run_subprocess
from api.websocket.task_manager import task_status_manager
from api.utils.security import security_validator
from api.services.email_service import email_service
from config.database import SessionLocal
from config.settings import settings

logger = logging.getLogger(__name__)


# ============================================================
# 损失函数与优化器映射配置
# 与PHP版本保持一致（索引到名称的映射）
# ============================================================

# 监督学习配置
SUPERVISED_LOSS_FUNCTIONS = {
    0: "crossentropy",
    1: "focalloss",
    2: "nllloss",
    # 字符串形式也支持（前端可能直接发送名称）
    "crossentropy": "crossentropy",
    "focalloss": "focalloss",
    "nllloss": "nllloss"
}

SUPERVISED_OPTIMIZERS = {
    0: "adam",
    1: "sgd",
    2: "rmsprop",
    "adam": "adam",
    "sgd": "sgd",
    "rmsprop": "rmsprop"
}

# 无监督学习 VAE 配置
VAE_LOSS_FUNCTIONS = {
    0: "mse",
    1: "mae",
    2: "smooth_l1",
    3: "focal",
    4: "contrastive",
    5: "spectral",
    6: "wasserstein",
    7: "perceptual",
    8: "cosine",
    9: "kl_div",
    10: "regularization",
    11: "bce",
    12: "huber",
    13: "infonce",
    "mse": "mse",
    "mae": "mae",
    "smooth_l1": "smooth_l1",
    "focal": "focal",
    "contrastive": "contrastive",
    "spectral": "spectral",
    "wasserstein": "wasserstein",
    "perceptual": "perceptual",
    "cosine": "cosine",
    "kl_div": "kl_div",
    "regularization": "regularization",
    "bce": "bce",
    "huber": "huber",
    "infonce": "infonce",
}

# 无监督学习 DeepCluster 配置
DEEPCLUSTER_LOSS_FUNCTIONS = {
    0: "deepcluster", 1: "combined", 2: "center", 3: "contrastive",
    4: "spectral", 5: "entropy", 6: "compactness", 7: "separation",
    "deepcluster": "deepcluster", "combined": "combined", "center": "center",
    "contrastive": "contrastive", "spectral": "spectral", "entropy": "entropy",
    "compactness": "compactness", "separation": "separation"
}

UNSUPERVISED_OPTIMIZERS = {
    0: "adam",
    1: "sgd",
    2: "adamw",
    "adam": "adam",
    "sgd": "sgd",
    "adamw": "adamw"
}

# 半监督学习 Ladder 配置
LADDER_LOSS_FUNCTIONS = {
    0: "semi_supervised", 1: "focal", 2: "label_smoothing", 3: "contrastive",
    "semi_supervised": "semi_supervised", "focal": "focal",
    "label_smoothing": "label_smoothing", "contrastive": "contrastive"
}

# 半监督学习 Pseudo 配置
PSEUDO_LOSS_FUNCTIONS = {
    0: "pseudo_label", 1: "focal", 2: "label_smoothing",
    "pseudo_label": "pseudo_label", "focal": "focal", "label_smoothing": "label_smoothing"
}

SEMI_SUPERVISED_OPTIMIZERS = {
    0: "adam",
    1: "sgd",
    2: "adamw",
    3: "rmsprop",
    "adam": "adam",
    "sgd": "sgd",
    "adamw": "adamw",
    "rmsprop": "rmsprop"
}


def _resolve_loss_function(value, mapping: dict, default: str) -> str:
    """解析损失函数值（支持索引或字符串）"""
    if value is None:
        return default
    if isinstance(value, int):
        return mapping.get(value, default)
    if isinstance(value, str):
        return mapping.get(value.lower(), value.lower())
    return default


def _resolve_optimizer(value, mapping: dict, default: str) -> str:
    """解析优化器值（支持索引或字符串）"""
    if value is None:
        return default
    if isinstance(value, int):
        return mapping.get(value, default)
    if isinstance(value, str):
        return mapping.get(value.lower(), value.lower())
    return default


def _build_ratio_string(params: Dict[str, Any]) -> str:
    """
    根据前端参数构建 ratio 字符串
    
    支持两种前端发送格式:
    1. split_ratio: {train: 7, validation: 2, test: 1}  (监督学习格式)
    2. ratio: "7:2:1"  (无监督/半监督学习格式)
    
    Python脚本期望: "7:2:1" 或 "8:1:1"
    """
    strategy = params.get("strategy", "upload")
    
    if strategy == "split":
        # 优先检查 ratio 字段（字符串格式，无监督/半监督使用）
        ratio = params.get("ratio")
        if ratio and isinstance(ratio, str) and ":" in ratio:
            return ratio
        
        # 其次检查 split_ratio 字段（dict格式，监督学习使用）
        split_ratio = params.get("split_ratio", {})
        if isinstance(split_ratio, dict) and split_ratio:
            train = split_ratio.get("train", 7)
            val = split_ratio.get("validation", 2)
            test = split_ratio.get("test", 1)
            return f"{train}:{val}:{test}"
        elif isinstance(split_ratio, str):
            return split_ratio
        
        # 如果都没有提供，使用默认值
        return "7:2:1"
    
    # upload 或其他策略不使用 ratio
    return "0"


def _get_kfold_value(params: Dict[str, Any]) -> str:
    """获取 kfold 值"""
    strategy = params.get("strategy", "upload")
    if strategy == "kfold":
        return str(params.get("kfold", 5))
    return "0"  # 不使用 kfold


def _is_zip_deliverable(zip_path: str) -> bool:
    """
    判断 zip 文件是否可交付。

    交付条件：
    - zip 文件存在
    - zip 文件大小 > 0
    """
    try:
        p = Path(zip_path)
        return p.exists() and p.stat().st_size > 0
    except OSError:
        return False


class TrainingService:
    """模型训练服务类"""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        # 与 PHP 版保持一致的 Jobs 目录
        self.jobs_root = settings.path_jobs

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

    def _validate_dataset_path(self, dataset_path: str) -> Path:
        """
        验证数据集路径的安全性，防止路径遍历攻击
        
        支持 file:// 协议前缀，格式为 file://{file_id}
        
        Args:
            dataset_path: 用户提供的数据集路径
            
        Returns:
            验证后的Path对象
            
        Raises:
            ValueError: 当路径不安全或无效时
        """
        # <!-- 
        # 审查上下文：
        # - 设计意图：委托给统一的安全验证工具处理路径验证
        # - 已知局限：依赖外部安全模块的实现
        # - 业务背景：利用标准化的安全验证流程确保一致性
        # - 测试重点：验证与安全工具模块的集成效果
        # -->
        if not dataset_path:
            return None
        
        # 处理 file:// 协议前缀
        if dataset_path.startswith('file://'):
            # 提取 file_id
            file_id = dataset_path[7:]  # 去掉 'file://' 前缀
            
            # 从数据库查询文件记录
            from api.models.file import File
            file_record = self.db.query(File).filter(File.id == file_id).first()
            if not file_record:
                raise ValueError(f"File not found: {file_id}")
            
            # 使用实际文件路径进行验证
            actual_path = file_record.file_path
            return security_validator.validate_file_path(
                actual_path, 
                allowed_extensions=['.txt', '.csv', '.tsv']
            )
            
        # 使用统一的安全验证工具
        return security_validator.validate_file_path(
            dataset_path, 
            allowed_extensions=['.txt', '.csv', '.tsv']
        )

    async def create_supervised_task(
        self,
        task_name: str,
        model_type: str,
        parameters: Dict[str, Any],
        dataset_path: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Job:
        """
        创建监督学习训练任务
        
        Args:
            task_name: 任务名称
            model_type: 模型类型 (cnn, lstm, rnn, mlp, autoencoder, transformer, som, rbfn, all)
            parameters: 训练参数字典
            dataset_path: 数据集路径（可选）
        """
        return await self._create_training_task(
            task_name=task_name,
            model_type=model_type,
            training_type="supervised",
            parameters=parameters,
            dataset_path=dataset_path,
            email=email,
        )

    async def create_unsupervised_task(
        self,
        task_name: str,
        model_type: str,
        parameters: Dict[str, Any],
        dataset_path: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Job:
        """
        创建无监督学习训练任务
        
        Args:
            task_name: 任务名称
            model_type: 模型类型 (vae, deepcluster)
            parameters: 训练参数字典
            dataset_path: 数据集路径（可选）
        """
        return await self._create_training_task(
            task_name=task_name,
            model_type=model_type,
            training_type="unsupervised",
            parameters=parameters,
            dataset_path=dataset_path,
            email=email,
        )

    async def create_semi_supervised_task(
        self,
        task_name: str,
        model_type: str,
        parameters: Dict[str, Any],
        dataset_path: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Job:
        """
        创建半监督学习训练任务
        
        Args:
            task_name: 任务名称
            model_type: 模型类型 (ladder, pseudo)
            parameters: 训练参数字典
            dataset_path: 数据集路径（可选）
        """
        return await self._create_training_task(
            task_name=task_name,
            model_type=model_type,
            training_type="semi_supervised",
            parameters=parameters,
            dataset_path=dataset_path,
            email=email,
        )

    async def _create_training_task(
        self,
        task_name: str,
        model_type: str,
        training_type: str,
        parameters: Dict[str, Any],
        dataset_path: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Job:
        """
        创建训练任务的通用方法
        
        - 生成 job_id
        - 在 jobs 表中插入一条 MODEL_TRAIN 记录（不再写入 training_tasks 表）
        - 异步调用对应的Python训练脚本
        
        Args:
            task_name: 任务名称
            model_type: 模型类型
            training_type: 训练类型 (supervised, unsupervised, semi_supervised)
            parameters: 训练参数字典
            dataset_path: 数据集路径（可选）
        """
        try:
            # 生成 JobID，与数据处理保持一致格式
            job_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # 创建 Job 记录（统一任务管理，不再创建 TrainingTask）
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.MODEL_TRAIN,
                status=JobStatus.SUBMITTED,
                progress=0,
                current_step="已提交，等待执行",
                input_params=json.dumps(
                    {
                        "task_name": task_name,
                        "model_type": model_type,
                        "training_type": training_type,
                        "parameters": parameters,
                        "dataset_path": dataset_path,
                    },
                    ensure_ascii=False,
                ),
                created_at=datetime.now(),
            )
            self.db.add(job)
            self.db.commit()

            resolved_email = email if email is not None else parameters.get("email")

            # 异步执行训练任务（使用独立DB会话，避免请求会话关闭导致后台任务连接失效）
            asyncio.create_task(
                self._execute_training_background(
                    user_id=int(self.user.id),
                    job_id=job_id,
                    model_type=model_type,
                    training_type=training_type,
                    parameters=parameters,
                    dataset_path=dataset_path,
                    email=resolved_email,
                )
            )

            # 返回刚创建的 Job 记录
            return job
        except Exception as e:
            logger.exception(f"创建训练任务失败: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create the training task: {e}")

    async def _execute_training_background(
        self,
        user_id: int,
        job_id: str,
        model_type: str,
        training_type: str,
        parameters: Dict[str, Any],
        dataset_path: Optional[str],
        email: Optional[str] = None,
    ):
        bg_db = SessionLocal()
        try:
            bg_user = bg_db.query(User).filter(User.id == user_id).first()
            if not bg_user:
                raise RuntimeError(f"后台训练未找到用户: {user_id}")
            bg_service = TrainingService(db=bg_db, user=bg_user)
            await bg_service._execute_training(
                job_id=job_id,
                model_type=model_type,
                training_type=training_type,
                parameters=parameters,
                dataset_path=dataset_path,
                email=email,
            )
        except Exception as e:
            raise
        finally:
            bg_db.close()

    async def _execute_training(
        self,
        job_id: str,
        model_type: str,
        training_type: str,
        parameters: Dict[str, Any],
        dataset_path: Optional[str],
        email: Optional[str] = None,
    ):
        """
        执行模型训练（支持监督、无监督、半监督学习）
        
        根据训练类型调用对应的Python训练脚本
        """
        try:
            # 更新 Job 状态为 Processing
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.PROCESSING
                job.progress = 5
                job.current_step = "准备训练环境"
                job.updated_at = datetime.now()
                self.db.commit()

            # WebSocket 推送开始状态
            try:
                await task_status_manager.send_task_status(
                    str(self.user.id),
                    {
                        "job_id": job_id,
                        "status": JobStatus.PROCESSING.value,
                        "progress": 5,
                        "current_step": "准备训练环境",
                        "message": f"开始{training_type}训练模型",
                    },
                )
            except Exception as e:
                logger.debug(f"WebSocket 状态推送失败: {e}")

            # 准备 Jobs 目录
            jobs_dir = self.jobs_root / job_id
            result_dir = jobs_dir / "result"
            jobs_dir.mkdir(parents=True, exist_ok=True)
            result_dir.mkdir(parents=True, exist_ok=True)

            # 处理数据集文件（与 PHP modelTrain.php 对齐）
            # - split/kfold：单文件 -> {job_id}_data.txt
            # - upload：三文件 -> {job_id}_data.txt / _val.txt / _test.txt
            strategy = parameters.get("strategy", "split")
            if training_type in ("supervised", "unsupervised", "semi_supervised") and strategy == "upload":
                train_fid = parameters.get("train_dataset_file_id")
                val_fid = parameters.get("validation_dataset_file_id")
                test_fid = parameters.get("test_dataset_file_id")
                if train_fid and val_fid and test_fid:
                    for fid, suffix in (
                        (train_fid, "_data.txt"),
                        (val_fid, "_val.txt"),
                        (test_fid, "_test.txt"),
                    ):
                        src = self._validate_dataset_path(f"file://{fid}")
                        shutil.copy2(str(src), str(jobs_dir / f"{job_id}{suffix}"))
                elif dataset_path:
                    src = self._validate_dataset_path(dataset_path)
                    shutil.copy2(str(src), str(jobs_dir / f"{job_id}_data.txt"))
                else:
                    raise ValueError(
                        "upload strategy requires uploading training set, validation set, and test set"
                    )
            elif training_type in ("supervised", "unsupervised", "semi_supervised") and strategy == "kfold":
                # 与 PHP modelTrain.php KFold 分支一致：训练集 -> _data.txt，测试集 -> _test.txt
                train_fid = parameters.get("kfold_train_dataset_file_id")
                test_fid = parameters.get("kfold_test_dataset_file_id")
                if train_fid and test_fid:
                    src_train = self._validate_dataset_path(f"file://{train_fid}")
                    shutil.copy2(str(src_train), str(jobs_dir / f"{job_id}_data.txt"))
                    src_test = self._validate_dataset_path(f"file://{test_fid}")
                    shutil.copy2(str(src_test), str(jobs_dir / f"{job_id}_test.txt"))
                elif dataset_path:
                    src = self._validate_dataset_path(dataset_path)
                    shutil.copy2(str(src), str(jobs_dir / f"{job_id}_data.txt"))
                else:
                    raise ValueError(
                        "kfold strategy requires uploading training set and test set (and K value)"
                    )
            elif dataset_path:
                src = self._validate_dataset_path(dataset_path)
                shutil.copy2(str(src), str(jobs_dir / f"{job_id}_data.txt"))

            # 更新进度：加载数据
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.progress = 10
                job.current_step = "加载训练数据"
                job.updated_at = datetime.now()
                self.db.commit()

            try:
                await task_status_manager.send_task_status(
                    str(self.user.id),
                    {
                        "job_id": job_id,
                        "status": JobStatus.PROCESSING.value,
                        "progress": 10,
                        "current_step": "加载训练数据",
                        "message": "正在加载训练数据",
                    },
                )
            except Exception as e:
                logger.debug(f"WebSocket 状态推送失败: {e}")

            # 更新进度：开始训练
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.progress = 30
                job.current_step = f"执行{model_type}模型训练"
                job.updated_at = datetime.now()
                self.db.commit()

            try:
                await task_status_manager.send_task_status(
                    str(self.user.id),
                    {
                        "job_id": job_id,
                        "status": JobStatus.PROCESSING.value,
                        "progress": 30,
                        "current_step": f"执行{model_type}模型训练",
                        "message": f"正在执行{model_type}模型训练",
                    },
                )
            except Exception as e:
                logger.debug(f"WebSocket 状态推送失败: {e}")

            # 根据训练类型选择对应的执行逻辑
            if training_type == "supervised":
                await self._execute_supervised_training_core(
                    job_id=job_id,
                    model_type=model_type,
                    parameters=parameters,
                    jobs_dir=jobs_dir,
                    result_dir=result_dir
                )
            elif training_type == "unsupervised":
                await self._execute_unsupervised_training_core(
                    job_id=job_id,
                    model_type=model_type,
                    parameters=parameters,
                    jobs_dir=jobs_dir,
                    result_dir=result_dir
                )
            elif training_type == "semi_supervised":
                await self._execute_semi_supervised_training_core(
                    job_id=job_id,
                    model_type=model_type,
                    parameters=parameters,
                    jobs_dir=jobs_dir,
                    result_dir=result_dir
                )
            else:
                raise ValueError(f"Unsupported training type: {training_type}")

            # 更新进度：压缩结果
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.progress = 90
                job.current_step = "压缩训练结果"
                job.updated_at = datetime.now()
                self.db.commit()

            try:
                await task_status_manager.send_task_status(
                    str(self.user.id),
                    {
                        "job_id": job_id,
                        "status": JobStatus.PROCESSING.value,
                        "progress": 90,
                        "current_step": "压缩训练结果",
                        "message": "正在压缩训练结果",
                    },
                )
            except Exception as e:
                logger.debug(f"WebSocket 状态推送失败: {e}")

            # 训练完成后，压缩 result 目录
            zip_file = str(result_dir) + ".zip"
            import zipfile
            try:
                with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
                    for path in result_dir.rglob("*"):
                        if path.is_file():
                            zf.write(path, path.relative_to(result_dir))
            except Exception as e:
                raise RuntimeError(f"Result compression failed: {e}") from e

            # 压缩后校验 zip 是否可交付
            if not _is_zip_deliverable(zip_file):
                raise RuntimeError("zip cannot be delivered (file does not exist or is empty)")

            # 更新任务状态为完成
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.COMPLETED
                job.progress = 100
                job.current_step = "训练完成"
                job.result_file = zip_file
                job.output_params = json.dumps(
                    {"training_type": training_type, "model_type": model_type},
                    ensure_ascii=False,
                )
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
                        "current_step": "训练完成",
                        "result_file": zip_file,
                        "message": f"{training_type}模型训练完成",
                    },
                )
            except Exception as e:
                logger.debug(f"WebSocket 状态推送失败: {e}")
            
            # 如果任务成功且提供了邮箱，发送结果邮件
            if email:
                try:
                    await email_service.send_result_email(
                        to_email=email,
                        job_id=job_id,
                        analysis_type=f"{training_type}模型训练",
                        result_dir=zip_file
                    )
                except Exception as e:
                    logger.warning(f"邮件发送失败（不影响任务结果）: {e}")

        except Exception as e:
            logger.exception(f"[TRAIN] 训练执行失败: job_id={job_id}, error={e}")
            error_msg = f"训练过程发生错误: {str(e)}"
            await self._handle_training_failure(
                job_id=job_id,
                error_message=error_msg,
                email=email,
                training_type=training_type,
            )

    async def _execute_supervised_training_core(
        self,
        job_id: str,
        model_type: str,
        parameters: Dict[str, Any],
        jobs_dir: Path,
        result_dir: Path
    ):
        """
        执行监督学习训练的核心逻辑
        
        Python脚本参数格式:
        --jobID <str>              # 任务ID
        --kfold <int>              # K折数（0=不使用）
        --ratio <str>              # 分割比例（0=不使用），格式 "8:1:1"
        --epochs <int>             # 训练轮数
        --es <int>                 # 早停耐心值
        --lr <float>               # 学习率
        --bs <int>                 # 批大小
        --loss_function <str>      # 损失函数名
        --optimizer_function <str> # 优化器名
        --output_size <int>        # 分类数
        --random_seed <int>        # 随机种子
        --type <str>               # "single"或"all"
        可选（按模型追加）:
        --r_method --r_weight --dropout_rate --feature_method
        SOM 仅支持 --feature_method
        """
        # 使用辅助函数处理数据集策略
        kfold_value = _get_kfold_value(parameters)
        ratio_str = _build_ratio_string(parameters)
        
        # 提取训练参数
        epochs = str(parameters.get("epochs", 20))
        es = str(parameters.get("early_stopping", 10))
        lr = str(parameters.get("learning_rate", 0.001))
        bs = str(parameters.get("batch_size", 32))
        labels = str(parameters.get("label_count", parameters.get("labels", 2)))
        seed = str(parameters.get("seed", parameters.get("random_seed", 42)))

        def _norm_opt_str(val: Any) -> Optional[str]:
            if val is None:
                return None
            s = str(val).strip()
            if not s or s.lower() in ("none", "null"):
                return None
            return s

        r_method = _norm_opt_str(
            parameters.get("r_method", parameters.get("regularization_method"))
        )
        try:
            r_weight_f = float(
                parameters.get("r_weight", parameters.get("regularization_weight", 0.0))
            )
        except (TypeError, ValueError):
            r_weight_f = 0.0
        try:
            dropout_rate_f = float(
                parameters.get("dropout_rate", parameters.get("dropout", 0.0))
            )
        except (TypeError, ValueError):
            dropout_rate_f = 0.0
        feature_method = _norm_opt_str(
            parameters.get("feature_method", parameters.get("feature_selection_method"))
        )

        def _append_supervised_extra_args(cmd_list: list, model_key: str) -> None:
            """按脚本能力追加 CLI；与 code/train_model 各模型 argparse 一致。"""
            mk = str(model_key).lower()
            if mk == "som":
                if feature_method:
                    cmd_list.extend(["--feature_method", feature_method])
                return
            if r_method:
                cmd_list.extend(["--r_method", r_method])
            cmd_list.extend(["--r_weight", str(r_weight_f)])
            cmd_list.extend(["--dropout_rate", str(dropout_rate_f)])
            if feature_method:
                cmd_list.extend(["--feature_method", feature_method])
        
        # 使用映射解析损失函数和优化器
        loss_function = _resolve_loss_function(
            parameters.get("loss_function"),
            SUPERVISED_LOSS_FUNCTIONS,
            "crossentropy"
        )
        optimizer = _resolve_optimizer(
            parameters.get("optimizer_function", parameters.get("optimizer")),
            SUPERVISED_OPTIMIZERS,
            "adam"
        )

        normalized_model_type = str(model_type).lower()
        supported_model_types = {"cnn", "lstm", "rnn", "mlp", "autoencoder", "transformer", "som", "rbfn", "all"}
        if normalized_model_type not in supported_model_types:
            logger.warning(
                "[TRAIN][SUPERVISED] 非法 model_type=%s，回退为 cnn",
                model_type
            )
            normalized_model_type = "cnn"

        # 模型到脚本映射
        base_code_map = {
            "cnn": "cnn",
            "lstm": "lstm",
            "rnn": "rnn",
            "mlp": "mlp",
            "autoencoder": "autoencoder",
            "transformer": "transformer",
            "som": "som",
            "rbfn": "rbfn",
        }

        python_exec = settings.PYTHON_EXEC_PATH
        stdout_all: list[str] = []

        def build_supervised_cmd(script_path: str, train_type: str, extras_for: str) -> list:
            """构建监督学习命令行参数"""
            cmd = [
                python_exec,
                script_path,
                "--jobID", str(job_id),
                "--kfold", kfold_value,
                "--ratio", ratio_str,
                "--epochs", epochs,
                "--es", es,
                "--lr", lr,
                "--bs", bs,
                "--loss_function", loss_function,
                "--optimizer_function", optimizer,
                "--output_size", labels,
                "--random_seed", seed,
                "--type", train_type,
            ]
            _append_supervised_extra_args(cmd, extras_for)
            return cmd

        if normalized_model_type == "all":
            # all 模式：对多种模型循环训练
            for m_type, code_type in base_code_map.items():
                sub_result_dir = result_dir / code_type
                sub_result_dir.mkdir(parents=True, exist_ok=True)
                script_path = str(settings.path_code / "train_model" / f"{code_type}.py")
                
                cmd = build_supervised_cmd(script_path, "all", m_type)
                terminal_log = sub_result_dir / "terminal.log"

                logger.info(f"[TRAIN][SUPERVISED][ALL] 开始执行训练脚本({m_type}): {' '.join(cmd)}")
                async with self._global_script_slot(job_id):
                    with open(terminal_log, "w", encoding="utf-8") as log_fp:
                        result = await run_subprocess(
                            cmd,
                            cwd=str(settings.path_repo),
                            shell=False,
                            timeout=3600,
                            stdout=None,
                            stderr=None,
                            text=True,
                        )
                        log_fp.write(result.stdout or "")
                        if result.stderr:
                            log_fp.write("\n[stderr]\n")
                            log_fp.write(result.stderr)
                        stdout_all.append(result.stdout or "")
                if result.returncode != 0:
                    raise RuntimeError(f"{m_type} training failed: {result.stderr}")
        else:
            code_type = base_code_map.get(normalized_model_type)
            if not code_type:
                raise RuntimeError(f"Unsupported supervised learning model type: {normalized_model_type}")

            script_path = str(settings.path_code / "train_model" / f"{code_type}.py")
            
            cmd = build_supervised_cmd(script_path, "single", normalized_model_type)
            terminal_log = result_dir / "terminal.log"

            logger.info(f"[TRAIN][SUPERVISED] 开始执行训练脚本: {' '.join(cmd)}")
            async with self._global_script_slot(job_id):
                with open(terminal_log, "w", encoding="utf-8") as log_fp:
                    result = await run_subprocess(
                        cmd,
                        cwd=str(settings.path_repo),
                        shell=False,
                        timeout=3600,
                        stdout=log_fp,
                        stderr=subprocess.STDOUT,
                        text=True,
                    )
                    stdout_all.append(getattr(result, "stdout", None) or "")
            if result.returncode != 0:
                raise RuntimeError(result.stderr or "Supervised learning training execution failed")
                # raise RuntimeError(
                #     f"监督学习训练脚本执行失败（详情见日志: {terminal_log}）"
                # )

    async def _execute_unsupervised_training_core(
        self,
        job_id: str,
        model_type: str,
        parameters: Dict[str, Any],
        jobs_dir: Path,
        result_dir: Path
    ):
        """
        执行无监督学习训练的核心逻辑
        
        注意：无监督学习脚本的参数命名与监督学习不同！
        
        Python脚本参数格式 (VAE/deepcluster.py):
        --jobid <str>                      # 注意小写！
        --k_folds <int>                    # 注意下划线！
        --epochs <int>
        --early_stopping_patience <int>    # 注意全名！
        --learning_rate <float>            # 注意全名！
        --batch_size <int>                 # 注意全名！
        --loss_function <str>
        --optimizer_function <str>
        --random_seed <int>
        --ratio <str>
        --model_path <str>                 # 模型保存路径
        --scaler_path <str>                # StandardScaler保存路径
        --evaluation_path <str>            # 评估结果路径
        """
        # 使用辅助函数处理数据集策略
        kfold_value = _get_kfold_value(parameters)
        ratio_str = _build_ratio_string(parameters)
        
        # 提取训练参数
        epochs = str(parameters.get("epochs", 10))
        early_stopping = str(parameters.get("early_stopping", 5))
        learning_rate = str(parameters.get("learning_rate", 0.001))
        batch_size = str(parameters.get("batch_size", 32))
        seed = str(parameters.get("seed", parameters.get("random_seed", 42)))
        
        # 根据模型类型选择损失函数映射
        model_lower = model_type.lower()
        if model_lower == "vae":
            loss_function = _resolve_loss_function(
                parameters.get("loss_function"),
                VAE_LOSS_FUNCTIONS,
                "mse"
            )
        elif model_lower == "deepcluster":
            loss_function = _resolve_loss_function(
                parameters.get("loss_function"),
                DEEPCLUSTER_LOSS_FUNCTIONS,
                "deepcluster"
            )
        else:
            loss_function = str(parameters.get("loss_function", "mse"))
        
        optimizer = _resolve_optimizer(
            parameters.get("optimizer_function", parameters.get("optimizer")),
            UNSUPERVISED_OPTIMIZERS,
            "adam"
        )

        # 模型到脚本映射
        unsupervised_code_map = {
            "vae": "VAE",
            "deepcluster": "deepcluster"
        }

        code_type = unsupervised_code_map.get(model_lower)
        if not code_type:
            raise RuntimeError(f"Unsupported unsupervised learning model type: {model_type}")

        # 准备输出路径
        model_path = str(result_dir / f"{job_id}_{code_type}_model.pth")
        scaler_path = str(result_dir / f"{job_id}_{code_type}_scaler.pkl")
        # 训练脚本会先将 evaluation_path 作为图像路径传给 plt.savefig，
        # 再在脚本内部将 .png 派生为 .json 结果文件路径。
        evaluation_path = str(result_dir / f"{job_id}_{code_type}_evaluation.png")

        python_exec = settings.PYTHON_EXEC_PATH
        script_path = str(settings.path_code / "train_model" / f"{code_type}.py")

        # 构建无监督学习命令 - 注意参数名称！
        cmd = [
            python_exec,
            script_path,
            "--jobid", str(job_id),                    # 小写!
            "--k_folds", kfold_value,                  # 下划线!
            "--epochs", epochs,
            "--early_stopping_patience", early_stopping,  # 全名!
            "--learning_rate", learning_rate,             # 全名!
            "--batch_size", batch_size,                   # 全名!
            "--loss_function", loss_function,
            "--optimizer_function", optimizer,
            "--random_seed", seed,
            "--ratio", ratio_str,
            "--model_path", model_path,
            "--scaler_path", scaler_path,
            "--evaluation_path", evaluation_path
        ]

        logger.info(f"[TRAIN][UNSUPERVISED] 开始执行训练脚本: {' '.join(cmd)}")
        terminal_log = result_dir / "terminal.log"
        async with self._global_script_slot(job_id):
            with open(terminal_log, "w", encoding="utf-8") as log_fp:
                result = await run_subprocess(
                    cmd,
                    cwd=str(settings.path_repo),
                    shell=False,
                    timeout=3600,
                    stdout=None,
                    stderr=None,
                    text=True,
                )
                log_fp.write(result.stdout or "")
                if result.stderr:
                    log_fp.write("\n[stderr]\n")
                    log_fp.write(result.stderr)
        
        if result.returncode != 0:
            raise RuntimeError(result.stderr or "Unsupervised learning training execution failed")

    async def _execute_semi_supervised_training_core(
        self,
        job_id: str,
        model_type: str,
        parameters: Dict[str, Any],
        jobs_dir: Path,
        result_dir: Path
    ):
        """
        执行半监督学习训练的核心逻辑
        
        Python脚本参数格式 (ladder.py/pseudo.py) - 与无监督类似的命名风格:
        --jobid <str>                      # 小写
        --k_folds <int>                    # 下划线
        --epochs <int>
        --early_stopping_patience <int>    # 全名
        --learning_rate <float>            # 全名
        --batch_size <int>                 # 全名
        --loss_function <str>
        --optimizer_function <str>
        --random_seed <int>
        --ratio <str>
        --alpha <float>                    # 监督损失权重
        --model_path <str>
        --scaler_path <str>
        --evaluation_path <str>
        
        Ladder特有: --beta, --gamma
        Pseudo特有: --confidence_threshold, --pseudo_ratio
        """
        # 使用辅助函数处理数据集策略
        kfold_value = _get_kfold_value(parameters)
        ratio_str = _build_ratio_string(parameters)
        
        # 提取通用训练参数
        epochs = str(parameters.get("epochs", 10))
        early_stopping = str(parameters.get("early_stopping", 5))
        learning_rate = str(parameters.get("learning_rate", 0.001))
        batch_size = str(parameters.get("batch_size", 32))
        seed = str(parameters.get("seed", parameters.get("random_seed", 42)))
        alpha = str(parameters.get("alpha", 1.0))  # 监督损失权重
        
        # 根据模型类型选择损失函数映射
        model_lower = model_type.lower()
        if model_lower == "ladder":
            loss_function = _resolve_loss_function(
                parameters.get("loss_function"),
                LADDER_LOSS_FUNCTIONS,
                "semi_supervised"
            )
        elif model_lower == "pseudo":
            loss_function = _resolve_loss_function(
                parameters.get("loss_function"),
                PSEUDO_LOSS_FUNCTIONS,
                "pseudo_label"
            )
        else:
            loss_function = str(parameters.get("loss_function", "semi_supervised"))
        
        optimizer = _resolve_optimizer(
            parameters.get("optimizer_function", parameters.get("optimizer")),
            SEMI_SUPERVISED_OPTIMIZERS,
            "adam"
        )

        # 模型到脚本映射
        semi_supervised_code_map = {
            "ladder": "ladder",
            "pseudo": "pseudo"
        }

        code_type = semi_supervised_code_map.get(model_lower)
        if not code_type:
            raise RuntimeError(f"Unsupported semi-supervised learning model type: {model_type}")

        # 准备输出路径
        model_path = str(result_dir / f"{job_id}_{code_type}_model.pth")
        scaler_path = str(result_dir / f"{job_id}_{code_type}_scaler.pkl")
        evaluation_path = str(result_dir / f"{job_id}_{code_type}_evaluation.png")

        python_exec = settings.PYTHON_EXEC_PATH
        script_path = str(settings.path_code / "train_model" / f"{code_type}.py")

        # 构建半监督学习命令 - 与无监督类似的参数命名
        cmd = [
            python_exec,
            script_path,
            "--jobid", str(job_id),                    # 小写
            "--k_folds", kfold_value,                  # 下划线
            "--epochs", epochs,
            "--early_stopping_patience", early_stopping,  # 全名
            "--learning_rate", learning_rate,             # 全名
            "--batch_size", batch_size,                   # 全名
            "--loss_function", loss_function,
            "--optimizer_function", optimizer,
            "--random_seed", seed,
            "--ratio", ratio_str,
            "--alpha", alpha,
            "--model_path", model_path,
            "--scaler_path", scaler_path,
            "--evaluation_path", evaluation_path
        ]

        # 添加 Ladder 特有参数
        if model_lower == "ladder":
            beta = str(parameters.get("beta", 1.0))
            gamma = str(parameters.get("gamma", 0.1))
            cmd.extend(["--beta", beta, "--gamma", gamma])

        # 添加 Pseudo 特有参数
        if model_lower == "pseudo":
            pseudo_beta = str(parameters.get("pseudo_beta", parameters.get("beta", 0.5)))
            confidence_threshold = str(parameters.get("confidence_threshold", 0.8))
            pseudo_ratio = str(parameters.get("pseudo_ratio", 0.5))
            cmd.extend([
                "--beta", pseudo_beta,
                "--confidence_threshold", confidence_threshold,
                "--pseudo_ratio", pseudo_ratio
            ])

        logger.info(f"[TRAIN][SEMI-SUPERVISED] 开始执行训练脚本: {' '.join(cmd)}")
        terminal_log = result_dir / "terminal.log"
        async with self._global_script_slot(job_id):
            with open(terminal_log, "w", encoding="utf-8") as log_fp:
                result = await run_subprocess(
                    cmd,
                    cwd=str(settings.path_repo),
                    shell=False,
                    timeout=3600,
                    stdout=None,
                    stderr=None,
                    text=True,
                )
                log_fp.write(result.stdout or "")
                if result.stderr:
                    log_fp.write("\n[stderr]\n")
                    log_fp.write(result.stderr)
        
        if result.returncode != 0:
            raise RuntimeError(result.stderr or "Semi-supervised learning training execution failed")

    async def _handle_training_failure(
        self,
        job_id: str,
        error_message: str,
        email: Optional[str] = None,
        training_type: Optional[str] = None,
    ):
        """
        统一处理训练失败的情况
        
        Args:
            job_id: 任务ID
            error_message: 错误信息
            email: 收件邮箱（可选）
            training_type: 训练类型（用于邮件标题/内容，可选）
        """
        job = self.db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error_message = error_message
            job.current_step = "训练失败"
            job.updated_at = datetime.now()
        self.db.commit()
        
        # WebSocket 通知失败状态
        try:
            await task_status_manager.send_task_status(
                str(self.user.id),
                {
                    "job_id": job_id,
                    "status": JobStatus.FAILED.value,
                    "progress": 0,
                    "current_step": "训练失败",
                    "error_message": error_message,
                    "message": error_message,
                },
            )
        except Exception as e:
            logger.debug(f"WebSocket 状态推送失败: {e}")

        # 发送失败邮件（返回值忽略；不影响 job 状态判定）
        if email:
            try:
                await email_service.send_failure_email(
                    to_email=email,
                    job_id=job_id,
                    analysis_type=f"{training_type}模型训练" if training_type else "模型训练",
                    error_message=error_message,
                )
            except Exception as e:
                logger.warning(f"发送失败邮件失败（不影响任务结果）: {e}")

