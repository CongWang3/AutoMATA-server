from sqlalchemy.orm import Session
from models.training_job import TrainingJob, TrainingLog
from schemas.training_job import TrainingJobCreate, TrainingJobUpdate, TrainingLogCreate
from typing import List, Optional
import json
import threading
import logging

logger = logging.getLogger(__name__)
from models_integration import ModelTrainer, ModelPredictor, validate_model_type, get_model_description


def create_training_task(db: Session, task: TrainingJobCreate):
    """
    创建新的训练任务
    """
    # 验证模型类型
    if not validate_model_type(task.model_type):
        raise ValueError(f"不支持的模型类型: {task.model_type}")
    
    # 解析参数
    parameters = {}
    if task.parameters:
        try:
            parameters = json.loads(task.parameters)
        except json.JSONDecodeError:
            parameters = {}
    
    # 提取数据文件信息
    # 处理两种数据格式：1) parameters中的文件字段 2) dataset_path字段
    train_file = parameters.get('train_file', '')
    val_file = parameters.get('val_file', '')
    test_file = parameters.get('test_file', '')
    
    # 如果parameters中没有文件字段，但有dataset_path，则使用dataset_path并自动生成其他文件名
    if not train_file and task.dataset_path:
        train_file = task.dataset_path
        
        # 自动生成验证和测试文件名
        if train_file.endswith('_train.txt'):
            base_name = train_file.replace('_train.txt', '')
            if not val_file:  # 如果没有指定验证文件
                val_file = f"{base_name}_val.txt"
            if not test_file:  # 如果没有指定测试文件
                test_file = f"{base_name}_test.txt"
    
    data_config = {
        'train_file': train_file,
        'val_file': val_file,
        'test_file': test_file,
        'integration_needed': parameters.get('integration_needed', False),
        'pheno_file': parameters.get('pheno_file', ''),
        'file_1': parameters.get('file_1', ''),
        'file_2': parameters.get('file_2', ''),
        'file_3': parameters.get('file_3', '')
    }
    
    db_task = TrainingJob(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # 自动关联文件（如果提供了文件ID）
    if task.dataset_path and task.dataset_path.startswith('file://'):
        try:
            file_id = task.dataset_path.replace('file://', '')
            logger.info(f"开始自动关联文件: {file_id} 到任务 {db_task.id}")
            
            # 检查文件是否存在
            from models.file_upload import TrainingFile
            file_record = db.query(TrainingFile).filter(TrainingFile.id == file_id).first()
            
            if file_record:
                logger.info(f"找到文件记录: {file_record.original_filename}")
                
                # 检查是否已有关联
                from models.file_upload import TaskFile
                existing_assoc = db.query(TaskFile).filter(
                    TaskFile.task_id == db_task.id,
                    TaskFile.file_id == file_id
                ).first()
                
                if not existing_assoc:
                    # 创建关联记录
                    task_file = TaskFile(
                        task_id=db_task.id,
                        file_id=file_id,
                        file_type='train'  # 默认为训练文件
                    )
                    db.add(task_file)
                    db.commit()
                    logger.info(f"✅ 自动关联成功: 文件 {file_id} 已关联到任务 {db_task.id}")
                else:
                    logger.info(f"ℹ️  文件 {file_id} 已经关联到任务 {db_task.id}")
            else:
                logger.warning(f"⚠️  文件 {file_id} 不存在，无法关联")
                
        except Exception as e:
            logger.error(f"❌ 自动关联文件失败: {str(e)}")
            db.rollback()
    
    # 异步启动模型训练
    thread = threading.Thread(target=start_model_training_sync, args=(db_task.id, parameters))
    thread.daemon = True
    thread.start()
    
    return db_task


def get_training_task(db: Session, task_id: int):
    """
    根据ID获取训练任务
    """
    return db.query(TrainingJob).filter(TrainingJob.id == task_id).first()


def get_training_tasks(db: Session, skip: int = 0, limit: int = 100):
    """
    获取训练任务列表，支持分页
    """
    return db.query(TrainingJob).offset(skip).limit(limit).all()


def update_training_task(db: Session, task_id: int, task_update: TrainingJobUpdate):
    """
    更新训练任务
    """
    db_task = db.query(TrainingJob).filter(TrainingJob.id == task_id).first()
    
    if not db_task:
        return None
    
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_training_task(db: Session, task_id: int):
    """
    删除训练任务及其关联的日志
    """
    db_task = db.query(TrainingJob).filter(TrainingJob.id == task_id).first()
    
    if not db_task:
        return False
    
    # 先删除关联的训练日志
    logs_to_delete = db.query(TrainingLog).filter(TrainingLog.task_id == task_id).all()
    for log in logs_to_delete:
        db.delete(log)
    
    # 再删除训练任务
    db.delete(db_task)
    db.commit()
    return True


def get_training_logs(db: Session, task_id: int):
    """
    获取特定任务的日志
    """
    return db.query(TrainingLog).filter(TrainingLog.task_id == task_id).all()


def create_training_log(db: Session, log: TrainingLogCreate):
    """
    创建训练日志
    """
    db_log = TrainingLog(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def start_model_training_sync(task_id: int, parameters: dict):
    """
    异步启动模型训练
    """
    from config.database import SessionLocal
    
    db = SessionLocal()
    try:
        # 获取任务信息
        task = db.query(TrainingJob).filter(TrainingJob.id == task_id).first()
        if not task:
            return
        
        # 更新任务状态为运行中
        task.status = "running"
        db.commit()
        
        # 创建训练器
        trainer = ModelTrainer(job_id=f"task_{task_id}_{task.task_name}", model_type=task.model_type)
        
        # 准备训练数据
        create_training_log(db, TrainingLogCreate(
            task_id=task_id,
            log_level="INFO",
            message="开始准备训练数据"
        ))
        
        # 从parameters中获取数据配置
        # 处理两种数据格式：1) parameters中的文件字段 2) 从任务信息中提取
        train_file = parameters.get('train_file', '')
        val_file = parameters.get('val_file', '')
        test_file = parameters.get('test_file', '')
        
        # 如果parameters中没有文件字段，但有dataset_path，则使用dataset_path并自动生成其他文件名
        if not train_file and task.dataset_path:
            train_file = task.dataset_path
            
            # 自动生成验证和测试文件名
            if train_file.endswith('_train.txt'):
                base_name = train_file.replace('_train.txt', '')
                if not val_file:  # 如果没有指定验证文件
                    val_file = f"{base_name}_val.txt"
                if not test_file:  # 如果没有指定测试文件
                    test_file = f"{base_name}_test.txt"
        
        data_config = {
            'train_file': train_file,
            'val_file': val_file,
            'test_file': test_file,
            'integration_needed': parameters.get('integration_needed', False),
            'pheno_file': parameters.get('pheno_file', ''),
            'file_1': parameters.get('file_1', ''),
            'file_2': parameters.get('file_2', ''),
            'file_3': parameters.get('file_3', '')
        }
        
        if trainer.prepare_training_data(data_config):
            create_training_log(db, TrainingLogCreate(
                task_id=task_id,
                log_level="INFO",
                message="训练数据准备完成"
            ))
            
            # 开始训练
            create_training_log(db, TrainingLogCreate(
                task_id=task_id,
                log_level="INFO",
                message="开始模型训练"
            ))
            
            training_result = trainer.train_model(parameters)
            
            # 训练完成
            task.status = "completed"
            task.result_path = training_result.get('result_path', '')
            db.commit()
            
            create_training_log(db, TrainingLogCreate(
                task_id=task_id,
                log_level="INFO",
                message="模型训练完成"
            ))
        else:
            # 数据准备失败
            task.status = "failed"
            db.commit()
            
            create_training_log(db, TrainingLogCreate(
                task_id=task_id,
                log_level="ERROR",
                message="训练数据准备失败"
            ))
            
    except Exception as e:
        # 训练失败
        task = db.query(TrainingJob).filter(TrainingJob.id == task_id).first()
        if task:
            task.status = "failed"
            db.commit()
        
        create_training_log(db, TrainingLogCreate(
            task_id=task_id,
            log_level="ERROR",
            message=f"模型训练失败: {str(e)}"
        ))
    
    finally:
        db.close()


def get_available_models_info():
    """
    获取可用模型信息
    """
    from models_integration import get_available_models, get_model_description
    
    models_info = []
    for model_type in get_available_models():
        models_info.append({
            'model_type': model_type,
            'description': get_model_description(model_type),
            'supported': True
        })
    
    return models_info