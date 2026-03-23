"""
作业（Job）相关工具
提供查询用户作业列表和作业详情的功能
"""
import logging
import json
from typing import Optional, Annotated
from langchain_core.tools import tool, InjectedToolArg
from langchain_core.runnables import RunnableConfig

from config.database import SessionLocal
from api.models.job import Job, JobStatus, JobType

logger = logging.getLogger(__name__)


def _get_db_and_user_id(config: RunnableConfig) -> tuple:
    """
    从 RunnableConfig 中获取数据库会话和用户 ID
    
    Args:
        config: LangChain 运行配置
        
    Returns:
        (db_session, user_id) 元组
    """
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id")
    tool_context = configurable.get("tool_context", {})
    
    # 从 tool_context 获取数据库会话，或创建新的
    db = tool_context.get("db")
    if db is None:
        db = SessionLocal()
    
    return db, user_id


@tool
def query_jobs(
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    config: Annotated[RunnableConfig, InjectedToolArg] = {}
) -> str:
    """
    查询用户的作业列表。
    
    可以按作业类型和状态进行筛选，返回最近的作业记录。
    
    参数说明：
    - job_type: 作业类型，可选值：
        - genome_process: 基因组处理
        - transcriptome_process: 转录组处理
        - protein_process: 蛋白质处理
        - integration_process: 多组学整合
        - pvalue_integration: P值整合分析
        - model_train: 模型训练
        - data_analysis: 数据分析
    - status: 作业状态，可选值：
        - Submitted: 已提交
        - Processing: 处理中
        - Completed: 已完成
        - Failed: 失败
        - Cancelled: 已取消
    - limit: 返回的最大记录数，默认 10 条
    
    返回：JSON 格式的作业列表
    
    Args:
        job_type: 作业类型过滤
        status: 作业状态过滤
        limit: 返回数量限制
        config: LangChain 运行配置
        
    Returns:
        JSON 格式的作业列表字符串
    """
    logger.info(f"[Job Tools] query_jobs 调用, job_type={job_type}, status={status}, limit={limit}")
    
    db = None
    try:
        # 从配置中获取用户 ID
        configurable = config.get("configurable", {}) if config else {}
        user_id = configurable.get("user_id")
        tool_context = configurable.get("tool_context", {})
        
        if not user_id:
            logger.warning("[Job Tools] user_id 为空，config 内容: %s", configurable)
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 确保 user_id 为整数（数据库字段为 Integer）
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"[Job Tools] user_id 类型转换失败: {user_id}")
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 创建数据库会话
        db = SessionLocal()
        should_close_db = True
        
        # 构建查询
        query = db.query(Job).filter(Job.user_id == user_id)
        
        # 类型过滤
        if job_type:
            try:
                job_type_enum = JobType(job_type)
                query = query.filter(Job.job_type == job_type_enum)
            except ValueError:
                return json.dumps({
                    "error": f"无效的作业类型: {job_type}",
                    "valid_types": [jt.value for jt in JobType]
                }, ensure_ascii=False)
        
        # 状态过滤
        if status:
            try:
                status_enum = JobStatus(status)
                query = query.filter(Job.status == status_enum)
            except ValueError:
                return json.dumps({
                    "error": f"无效的作业状态: {status}",
                    "valid_statuses": [js.value for js in JobStatus]
                }, ensure_ascii=False)
        
        # 限制数量并排序
        jobs = query.order_by(Job.created_at.desc()).limit(limit).all()
        
        # 转换为可序列化格式
        result = {
            "total": len(jobs),
            "jobs": []
        }
        
        for job in jobs:
            job_dict = {
                "job_id": job.job_id,
                "job_type": job.job_type.value if job.job_type else None,
                "job_type_display": job.job_type.display_name if job.job_type else None,
                "status": job.status.value if job.status else None,
                "status_display": job.status.display_name if job.status else None,
                "progress": job.progress or 0,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            }
            
            # 解析输入参数获取更多信息
            if job.input_params:
                try:
                    params = json.loads(job.input_params)
                    job_dict["analysis_type"] = params.get("analysis_type")
                    job_dict["original_filename"] = params.get("original_filename")
                except:
                    pass
            
            result["jobs"].append(job_dict)
        
        logger.info(f"[Job Tools] 查询到 {len(jobs)} 个作业")
        
        if should_close_db:
            db.close()
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"[Job Tools] query_jobs 失败: {e}")
        if db:
            db.close()
        return json.dumps({"error": f"查询作业失败: {str(e)}"}, ensure_ascii=False)


@tool
def get_job_detail(
    job_id: str,
    config: Annotated[RunnableConfig, InjectedToolArg] = {}
) -> str:
    """
    获取指定作业的详细信息。
    
    返回作业的完整信息，包括输入参数、输出结果、错误信息等。
    
    Args:
        job_id: 作业 ID
        config: LangChain 运行配置
        
    Returns:
        JSON 格式的作业详情字符串
    """
    logger.info(f"[Job Tools] get_job_detail 调用, job_id={job_id}")
    
    db = None
    try:
        # 从配置中获取用户 ID
        configurable = config.get("configurable", {}) if config else {}
        user_id = configurable.get("user_id")
        tool_context = configurable.get("tool_context", {})
        
        if not user_id:
            logger.warning("[Job Tools] user_id 为空，config 内容: %s", configurable)
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 确保 user_id 为整数（数据库字段为 Integer）
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"[Job Tools] user_id 类型转换失败: {user_id}")
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 创建数据库会话
        db = SessionLocal()
        should_close_db = True
        
        # 查询作业
        job = db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == user_id
        ).first()
        
        if not job:
            if should_close_db:
                db.close()
            return json.dumps({"error": f"作业不存在: {job_id}"}, ensure_ascii=False)
        
        # 构建详细信息
        result = {
            "job_id": job.job_id,
            "job_type": job.job_type.value if job.job_type else None,
            "job_type_display": job.job_type.display_name if job.job_type else None,
            "status": job.status.value if job.status else None,
            "status_display": job.status.display_name if job.status else None,
            "progress": job.progress or 0,
            "current_step": job.current_step,
            "result_file": job.result_file,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
        
        # 解析输入参数
        if job.input_params:
            try:
                result["input_params"] = json.loads(job.input_params)
            except:
                result["input_params"] = job.input_params
        
        # 解析输出参数
        if job.output_params:
            try:
                result["output_params"] = json.loads(job.output_params)
            except:
                result["output_params"] = job.output_params
        
        logger.info(f"[Job Tools] 获取作业详情成功: {job_id}")
        
        if should_close_db:
            db.close()
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"[Job Tools] get_job_detail 失败: {e}")
        if db:
            db.close()
        return json.dumps({"error": f"获取作业详情失败: {str(e)}"}, ensure_ascii=False)
