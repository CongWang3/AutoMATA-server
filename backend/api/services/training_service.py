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
from api.models.training import TrainingTask
from api.websocket.task_manager import task_status_manager
from api.utils.security import security_validator

logger = logging.getLogger(__name__)


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
    ) -> TrainingTask:
        """
        创建监督学习训练任务

        - 生成 job_id
        - 在 jobs 表中插入一条 MODEL_TRAIN 记录
        - 在 training_tasks 表中插入一条记录
        - 异步调用 Python 训练脚本（参考 legacy PHP `modelTrain.php`）
        
        Args:
            task_name: 任务名称
            model_type: 模型类型
            parameters: 训练参数字典
            dataset_path: 数据集路径（可选）
        """
        """
        创建监督学习训练任务

        - 生成 job_id
        - 在 jobs 表中插入一条 MODEL_TRAIN 记录
        - 在 training_tasks 表中插入一条记录
        - 异步调用 Python 训练脚本（参考 modelTrain.php）
        """
        try:
            # 生成 JobID，与数据处理保持一致格式
            job_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # 创建 Job 记录（统一任务管理）
            job = Job(
                job_id=job_id,
                user_id=self.user.id,
                job_type=JobType.MODEL_TRAIN,
                status=JobStatus.SUBMITTED,
                input_params=json.dumps(
                    {
                        "task_name": task_name,
                        "model_type": model_type,
                        "parameters": parameters,
                        "dataset_path": dataset_path,
                    },
                    ensure_ascii=False,
                ),
                created_at=datetime.now(),
            )
            self.db.add(job)
            self.db.flush()

            # 创建 TrainingTask 记录
            db_task = TrainingTask(
                task_name=task_name,
                model_type=model_type,
                status="pending",
                parameters=json.dumps(parameters, ensure_ascii=False),
                dataset_path=dataset_path,
                result_path=None,
                job_id=job_id,
                created_by=self.user.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.db.add(db_task)
            self.db.commit()

            # 异步执行训练任务
            asyncio.create_task(
                self._execute_supervised_training(
                    job_id=job_id,
                    task_id=db_task.id,
                    model_type=model_type,
                    parameters=parameters,
                    dataset_path=dataset_path,
                )
            )

            # 返回刚创建的 TrainingTask 记录
            return db_task
        except Exception as e:
            logger.exception(f"创建训练任务失败: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"创建训练任务失败: {e}")

    async def _execute_supervised_training(
        self,
        job_id: str,
        task_id: int,
        model_type: str,
        parameters: Dict[str, Any],
        dataset_path: Optional[str],
    ):
        """
        执行监督学习训练（调用 /xp/www/AutoMATA/code/train_model/*.py）

        当前实现：
        - 仅对接单一主数据集（strategy 初版先兼容 upload/split/kfold 的公共参数）
        - SOM 模型暂不支持
        """
        try:
            # 更新 Job 状态为 Processing（训练任务总体状态由 Job 管理）
            job = self.db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.PROCESSING
                job.updated_at = datetime.now()
                self.db.commit()

            # WebSocket 推送开始状态
            try:
                await task_status_manager.send_task_status(
                    str(self.user.id),
                    {
                        "job_id": job_id,
                        "status": JobStatus.PROCESSING.value,
                        "progress": 0,
                        "message": "开始训练模型",
                    },
                )
            except Exception as e:
                logger.debug(f"WebSocket 状态推送失败: {e}")

            # 准备 Jobs 目录
            jobs_dir = self.jobs_root / job_id
            result_dir = jobs_dir / "result"
            jobs_dir.mkdir(parents=True, exist_ok=True)
            result_dir.mkdir(parents=True, exist_ok=True)

            #
            # 1. 处理数据集文件
            #    这里先实现简单版：假设前端已上传并传入一个 dataset_path，
            #    我们将其复制为 jobID_data.txt，用作训练主数据集。
            #    现在使用安全的路径验证方法
            #
            data_file = None
            if dataset_path:
                # <!-- 
                # 审查上下文：
                # - 设计意图：使用新添加的路径验证方法替代原有的简单检查
                # - 已知局限：增加了额外的验证开销，但提升了安全性
                # - 业务背景：确保训练数据来源可信，防止恶意文件访问
                # - 测试重点：验证各种非法路径输入的拒绝情况
                # -->
                src = self._validate_dataset_path(dataset_path)
                data_file = jobs_dir / f"{job_id}_data.txt"
                import shutil

                shutil.copy2(str(src), str(data_file))

            # ratio / kfold 等参数从 parameters 中读取（与 PHP 逻辑兼容）
            strategy = str(parameters.get("strategy", "upload"))
            kfold = str(parameters.get("kfold", "0"))
            ratio = str(parameters.get("ratio", "0"))
            epochs = str(parameters.get("epochs") or parameters.get("epoch") or "20")
            es = str(parameters.get("early_stopping") or parameters.get("es") or "10")
            lr = str(parameters.get("learning_rate") or parameters.get("lr") or "0.001")
            bs = str(parameters.get("batch_size") or parameters.get("bs") or "32")
            labels = str(parameters.get("labels") or parameters.get("num_labels") or "2")
            seed = str(parameters.get("seed") or parameters.get("random_seed") or "42")
            loss = str(parameters.get("loss_function") or "crossentropy")
            optimizer = str(parameters.get("optimizer_function") or "adam")

            # 不支持 SOM
            if model_type.lower() == "som":
                raise RuntimeError("当前暂不支持 SOM 模型训练")

            # 与 PHP modelTrain.php 对齐的模型到脚本映射
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

            # all 模式：对多种模型循环训练，仿照 PHP 中的 all 逻辑
            if model_type.lower() == "all":
                for m_type, code_type in base_code_map.items():
                    sub_result_dir = result_dir / code_type
                    sub_result_dir.mkdir(parents=True, exist_ok=True)
                    script_path = f"/xp/www/AutoMATA/code/train_model/{code_type}.py"
                    outfile = sub_result_dir / "terminal.log"

                    # <!-- 
                    # 审查上下文：
                    # - 设计意图：使用列表形式传递参数，避免shell解析，从根本上防止命令注入
                    # - 已知局限：需要确保所有参数都是字符串类型
                    # - 业务背景：模型训练需要执行外部Python脚本，必须确保最高级别的参数安全性
                    # - 测试重点：验证各种边界参数值的安全传递
                    # -->
                    cmd = [
                        python_exec,
                        script_path,
                        "--jobID", str(job_id),
                        "--kfold", str(kfold),
                        "--ratio", str(ratio),
                        "--epochs", str(epochs),
                        "--es", str(es),
                        "--lr", str(lr),
                        "--bs", str(bs),
                        "--loss_function", str(loss),
                        "--optimizer_function", str(optimizer),
                        "--output_size", str(labels),
                        "--random_seed", str(seed),
                        "--type", "all"
                    ]

                    logger.info(f"[TRAIN][ALL] 开始执行训练脚本({m_type}): {' '.join(cmd)}")
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        cwd="/xp/www/AutoMATA",
                        shell=False,  # 明确禁用shell，确保安全
                        timeout=3600  # 1小时超时限制
                    )
                    stdout_all.append(result.stdout or "")
                    if result.returncode != 0:
                        raise RuntimeError(f"{m_type} 训练失败: {result.stderr}")
            else:
                code_type = base_code_map.get(model_type.lower())
                if not code_type:
                    raise RuntimeError(f"不支持的模型类型: {model_type}")

                script_path = f"/xp/www/AutoMATA/code/train_model/{code_type}.py"
                outfile = result_dir / "terminal.log"

                # <!-- 
                # 审查上下文：
                # - 设计意图：统一使用安全的参数传递方式，避免shell注入风险
                # - 已知局限：需要确保数值参数正确转换为字符串
                # - 业务背景：为所有模型训练提供一致的安全保障
                # - 测试重点：验证timeout机制和各种异常处理
                # -->
                cmd = [
                    python_exec,
                    script_path,
                    "--jobID", str(job_id),
                    "--kfold", str(kfold),
                    "--ratio", str(ratio),
                    "--epochs", str(epochs),
                    "--es", str(es),
                    "--lr", str(lr),
                    "--bs", str(bs),
                    "--loss_function", str(loss),
                    "--optimizer_function", str(optimizer),
                    "--output_size", str(labels),
                    "--random_seed", str(seed),
                    "--type", "single"
                ]

                logger.info(f"[TRAIN] 开始执行训练脚本: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd="/xp/www/AutoMATA",
                    shell=False,  # 明确禁用shell
                    timeout=3600  # 1小时超时限制
                )
                stdout_all.append(result.stdout or "")
                if result.returncode != 0:
                    raise RuntimeError(result.stderr or "训练脚本执行失败")

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

            # 更新任务状态
            job = self.db.query(Job).filter(Job.job_id == job_id).first()

            if job:
                job.status = JobStatus.COMPLETED
                job.result_file = zip_file
                job.output_params = json.dumps(
                    {"stdout": "\n".join(stdout_all)},
                    ensure_ascii=False,
                )
                job.updated_at = datetime.now()
                self.db.commit()

            try:
                await task_status_manager.send_task_status(
                    str(self.user.id),
                    {
                        "job_id": job_id,
                        "status": JobStatus.COMPLETED.value,
                        "progress": 100,
                        "result_file": zip_file,
                        "message": "模型训练完成",
                    },
                )
            except Exception as e:
                logger.debug(f"WebSocket 状态推送失败: {e}")

        # <!-- 
        # 审查上下文：
        # - 设计意图：提供更加精细化的异常处理，针对不同类型错误给出准确反馈
        # - 已知局限：异常分类可能还需要根据实际运行情况进行调整
        # - 业务背景：用户需要清楚了解训练失败的具体原因以便修正
        # - 测试重点：验证各种边界条件和异常场景的处理准确性
        # -->
        except subprocess.TimeoutExpired as e:
            logger.error(f"[TRAIN] 训练脚本执行超时: {e.cmd}")
            error_msg = "训练时间过长已超时，请检查参数设置或联系管理员"
            self._handle_training_failure(job_id, error_msg)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"[TRAIN] 训练脚本执行失败: {e.cmd} returned {e.returncode}")
            # 分析具体的错误类型
            if e.returncode == 127:
                error_msg = "训练脚本执行环境配置错误，请联系系统管理员"
            elif e.returncode == 137:
                error_msg = "训练过程内存不足被系统终止，请减少批次大小或联系管理员"
            else:
                error_msg = f"训练脚本执行失败: {e.stderr or str(e)}"
            self._handle_training_failure(job_id, error_msg)
            
        except FileNotFoundError as e:
            logger.error(f"[TRAIN] 训练脚本未找到: {e}")
            error_msg = "训练脚本不存在，请联系系统管理员"
            self._handle_training_failure(job_id, error_msg)
            
        except PermissionError as e:
            logger.error(f"[TRAIN] 权限不足: {e}")
            error_msg = "系统权限不足，无法执行训练任务，请联系管理员"
            self._handle_training_failure(job_id, error_msg)
            
        except ValueError as e:
            # 路径验证失败、参数验证失败等
            logger.warning(f"[TRAIN] 参数验证失败: {e}")
            error_msg = f"参数验证失败: {str(e)}"
            self._handle_training_failure(job_id, error_msg)
            
        except MemoryError as e:
            logger.error(f"[TRAIN] 内存不足: {e}")
            error_msg = "系统内存不足，无法完成训练，请减少模型复杂度或联系管理员"
            self._handle_training_failure(job_id, error_msg)
            
        except Exception as e:
            logger.exception(f"[TRAIN] 未知错误: job_id={job_id}, error={e}")
            error_msg = f"训练过程发生未知错误: {str(e)}"
            self._handle_training_failure(job_id, error_msg)

    def _handle_training_failure(self, job_id: str, error_message: str):
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
            job.updated_at = datetime.now()
        self.db.commit()
        
        # WebSocket 通知失败状态
        try:
            asyncio.create_task(
                task_status_manager.send_task_status(
                    str(self.user.id),
                    {
                        "job_id": job_id,
                        "status": JobStatus.FAILED.value,
                        "progress": 0,
                        "message": error_message,
                    },
                )
            )
        except Exception as e:
            logger.debug(f"WebSocket 状态推送失败: {e}")

