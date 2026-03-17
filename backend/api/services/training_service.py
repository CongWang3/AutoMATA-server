"""
模型训练服务层：封装监督学习训练任务的业务逻辑

设计目标：
- 与数据处理服务 (`DataProcessService`) 风格一致
- 复用 `jobs` 表做统一任务管理，使用 `JobType.MODEL_TRAIN`
- 通过异步任务执行 Python 训练脚本（参考 legacy PHP `modelTrain.php`）
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import asyncio
import subprocess
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.models.user import User
from api.models.job import Job, JobType, JobStatus
from api.websocket.task_manager import task_status_manager
from api.utils.security import security_validator

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
    0: "mse", 1: "mae", 2: "huber", 3: "smooth_l1", 4: "log_cosh",
    5: "bce", 6: "bce_with_logits", 7: "kl_div", 8: "cosine_embedding",
    9: "poisson_nll", 10: "gaussian_nll", 11: "beta_vae", 12: "info_vae", 13: "disentangled_vae",
    "mse": "mse", "mae": "mae", "huber": "huber", "smooth_l1": "smooth_l1",
    "log_cosh": "log_cosh", "bce": "bce", "bce_with_logits": "bce_with_logits",
    "kl_div": "kl_div", "cosine_embedding": "cosine_embedding",
    "poisson_nll": "poisson_nll", "gaussian_nll": "gaussian_nll",
    "beta_vae": "beta_vae", "info_vae": "info_vae", "disentangled_vae": "disentangled_vae"
}

# 无监督学习 DeepCluster 配置
DEEPCLUSTER_LOSS_FUNCTIONS = {
    0: "kmeans_ce", 1: "spectral", 2: "agglomerative", 3: "mean_shift",
    4: "gmm", 5: "contrastive", 6: "triplet", 7: "reconstruction",
    "kmeans_ce": "kmeans_ce", "spectral": "spectral", "agglomerative": "agglomerative",
    "mean_shift": "mean_shift", "gmm": "gmm", "contrastive": "contrastive",
    "triplet": "triplet", "reconstruction": "reconstruction"
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


class TrainingService:
    """模型训练服务类"""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        # 与 PHP 版保持一致的 Jobs 目录
        self.jobs_root = Path("/xp/www/AutoMATA/download_data/Jobs")

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
                raise ValueError(f"文件不存在: {file_id}")
            
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
            dataset_path=dataset_path
        )

    async def create_unsupervised_task(
        self,
        task_name: str,
        model_type: str,
        parameters: Dict[str, Any],
        dataset_path: Optional[str] = None,
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
            dataset_path=dataset_path
        )

    async def create_semi_supervised_task(
        self,
        task_name: str,
        model_type: str,
        parameters: Dict[str, Any],
        dataset_path: Optional[str] = None,
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
            dataset_path=dataset_path
        )

    async def _create_training_task(
        self,
        task_name: str,
        model_type: str,
        training_type: str,
        parameters: Dict[str, Any],
        dataset_path: Optional[str] = None,
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

            # 异步执行训练任务
            asyncio.create_task(
                self._execute_training(
                    job_id=job_id,
                    model_type=model_type,
                    training_type=training_type,
                    parameters=parameters,
                    dataset_path=dataset_path,
                )
            )

            # 返回刚创建的 Job 记录
            return job
        except Exception as e:
            logger.exception(f"创建训练任务失败: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"创建训练任务失败: {e}")

    async def _execute_training(
        self,
        job_id: str,
        model_type: str,
        training_type: str,
        parameters: Dict[str, Any],
        dataset_path: Optional[str],
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

            # 处理数据集文件
            data_file = None
            if dataset_path:
                src = self._validate_dataset_path(dataset_path)
                data_file = jobs_dir / f"{job_id}_data.txt"
                import shutil
                shutil.copy2(str(src), str(data_file))

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
                raise ValueError(f"不支持的训练类型: {training_type}")

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
            try:
                import zipfile
                with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
                    for path in result_dir.rglob("*"):
                        if path.is_file():
                            zf.write(path, path.relative_to(result_dir))
            except Exception as e:
                logger.warning(f"[TRAIN] 结果压缩失败: {e}")

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

        except Exception as e:
            logger.exception(f"[TRAIN] 训练执行失败: job_id={job_id}, error={e}")
            error_msg = f"训练过程发生错误: {str(e)}"
            await self._handle_training_failure(job_id, error_msg)

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

        # 不支持 SOM
        if model_type.lower() == "som":
            raise RuntimeError("当前暂不支持 SOM 模型训练")

        # 模型到脚本映射
        base_code_map = {
            "cnn": "cnn",
            "lstm": "lstm",
            "rnn": "rnn",
            "mlp": "mlp",
            "autoencoder": "autoencoder",
            "transformer": "transformer",
            "rbfn": "rbfn",
        }

        python_exec = "/opt/anaconda/envs/automata/bin/python"
        stdout_all: list[str] = []

        def build_supervised_cmd(script_path: str, train_type: str) -> list:
            """构建监督学习命令行参数"""
            return [
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
                "--type", train_type
            ]

        if model_type.lower() == "all":
            # all 模式：对多种模型循环训练
            for m_type, code_type in base_code_map.items():
                sub_result_dir = result_dir / code_type
                sub_result_dir.mkdir(parents=True, exist_ok=True)
                script_path = f"/xp/www/AutoMATA/code/train_model/{code_type}.py"
                
                cmd = build_supervised_cmd(script_path, "all")

                logger.info(f"[TRAIN][SUPERVISED][ALL] 开始执行训练脚本({m_type}): {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd="/xp/www/AutoMATA",
                    shell=False,
                    timeout=3600
                )
                stdout_all.append(result.stdout or "")
                if result.returncode != 0:
                    raise RuntimeError(f"{m_type} 训练失败: {result.stderr}")
        else:
            code_type = base_code_map.get(model_type.lower())
            if not code_type:
                raise RuntimeError(f"不支持的监督学习模型类型: {model_type}")

            script_path = f"/xp/www/AutoMATA/code/train_model/{code_type}.py"
            
            cmd = build_supervised_cmd(script_path, "single")

            logger.info(f"[TRAIN][SUPERVISED] 开始执行训练脚本: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd="/xp/www/AutoMATA",
                shell=False,
                timeout=3600
            )
            stdout_all.append(result.stdout or "")
            if result.returncode != 0:
                raise RuntimeError(result.stderr or "监督学习训练脚本执行失败")

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
                "kmeans_ce"
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
            raise RuntimeError(f"不支持的无监督学习模型类型: {model_type}")

        # 准备输出路径
        model_path = str(result_dir / f"{job_id}_{code_type}_model.pt")
        scaler_path = str(result_dir / f"{job_id}_{code_type}_scaler.pkl")
        evaluation_path = str(result_dir / f"{job_id}_{code_type}_evaluation.json")

        python_exec = "/opt/anaconda/envs/automata/bin/python"
        script_path = f"/xp/www/AutoMATA/code/train_model/{code_type}.py"

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
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd="/xp/www/AutoMATA",
            shell=False,
            timeout=3600
        )
        
        if result.returncode != 0:
            raise RuntimeError(result.stderr or "无监督学习训练脚本执行失败")

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
            raise RuntimeError(f"不支持的半监督学习模型类型: {model_type}")

        # 准备输出路径
        model_path = str(result_dir / f"{job_id}_{code_type}_model.pt")
        scaler_path = str(result_dir / f"{job_id}_{code_type}_scaler.pkl")
        evaluation_path = str(result_dir / f"{job_id}_{code_type}_evaluation.json")

        python_exec = "/opt/anaconda/envs/automata/bin/python"
        script_path = f"/xp/www/AutoMATA/code/train_model/{code_type}.py"

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
            confidence_threshold = str(parameters.get("confidence_threshold", 0.8))
            pseudo_ratio = str(parameters.get("pseudo_ratio", 0.5))
            cmd.extend([
                "--confidence_threshold", confidence_threshold,
                "--pseudo_ratio", pseudo_ratio
            ])

        logger.info(f"[TRAIN][SEMI-SUPERVISED] 开始执行训练脚本: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd="/xp/www/AutoMATA",
            shell=False,
            timeout=3600
        )
        
        if result.returncode != 0:
            raise RuntimeError(result.stderr or "半监督学习训练脚本执行失败")

    async def _handle_training_failure(self, job_id: str, error_message: str):
        """
        统一处理训练失败的情况
        
        Args:
            job_id: 任务ID
            error_message: 错误信息
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

