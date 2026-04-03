"""
数据分析相关工具
提供 PCA 分析、火山图、差异表达分析等功能
"""
import logging
import json
import uuid
import asyncio
from typing import Optional, Annotated
from datetime import datetime
from pathlib import Path
from langchain_core.tools import tool, InjectedToolArg
from langchain_core.runnables import RunnableConfig

from config.database import SessionLocal
from config.settings import settings
from api.models.job import Job, JobType, JobStatus
from api.models.file import File

logger = logging.getLogger(__name__)

# 路径配置（与 analysis_service.py 保持一致）
RSCRIPT_PATH = settings.RSCRIPT_PATH
RSCRIPT_OPTIONS = "--no-save"
R_SCRIPTS_DIR = settings.path_data_analysis_plot
JOBS_BASE_DIR = settings.path_jobs


def _generate_job_id() -> str:
    """生成任务 ID"""
    return f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _create_job_dirs(job_id: str) -> tuple:
    """创建任务目录和结果目录"""
    job_dir = JOBS_BASE_DIR / job_id
    result_dir = job_dir / "result"
    job_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)
    return job_dir, result_dir


def _get_user_file(db, file_id: str, user_id: int) -> Optional[File]:
    """获取用户文件记录"""
    return db.query(File).filter(
        File.id == file_id,
        File.uploaded_by == user_id,
        File.delete_marked_at.is_(None)
    ).first()


@tool
def run_pca_analysis(
    file_id: str,
    confidence: float = 0.95,
    boundary: bool = False,
    permanova: bool = False,
    method: Optional[str] = None,
    config: Annotated[RunnableConfig, InjectedToolArg] = {}
) -> str:
    """
    执行 PCA 主成分分析。
    
    对上传的数据文件执行 PCA 分析，生成主成分图和统计结果。
    
    参数说明：
    - file_id: 要分析的文件 ID（必填）。可以通过 list_user_files 工具获取用户文件列表
    - confidence: 置信区间，默认 0.95（范围 0-1）
    - boundary: 是否显示边界，默认 False
    - permanova: 是否执行 PERMANOVA 分析，默认 False
    - method: PERMANOVA 方法，仅当 permanova=True 时有效
    
    返回：作业提交结果，包含 job_id 用于查询分析进度
    
    Args:
        file_id: 数据文件 ID
        confidence: 置信区间
        boundary: 是否显示边界
        permanova: 是否执行 PERMANOVA
        method: PERMANOVA 方法
        config: LangChain 运行配置
        
    Returns:
        JSON 格式的作业提交结果
    """
    logger.info(f"[Analysis Tools] run_pca_analysis 调用, file_id={file_id}")
    
    db = None
    try:
        # 从配置中获取用户 ID
        configurable = config.get("configurable", {}) if config else {}
        user_id = configurable.get("user_id")
        tool_context = configurable.get("tool_context", {})
        
        if not user_id:
            logger.warning("[Analysis Tools] user_id 为空，config 内容: %s", configurable)
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 确保 user_id 为整数（数据库字段为 Integer）
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"[Analysis Tools] user_id 类型转换失败: {user_id}")
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 创建数据库会话
        db = SessionLocal()
        should_close_db = True
        
        # 获取用户文件
        file_record = _get_user_file(db, file_id, user_id)
        if not file_record:
            if should_close_db:
                db.close()
            return json.dumps({
                "error": f"文件不存在或无权访问: {file_id}",
                "hint": "请使用 list_user_files 工具查看可用文件"
            }, ensure_ascii=False)
        
        # 验证文件存在
        source_file = Path(file_record.file_path)
        if not source_file.exists():
            if should_close_db:
                db.close()
            return json.dumps({"error": "文件物理不存在，可能已被删除"}, ensure_ascii=False)
        
        # 生成任务 ID 和目录
        job_id = _generate_job_id()
        job_dir, result_dir = _create_job_dirs(job_id)
        
        # 复制源文件到任务目录
        import shutil
        data_file = job_dir / f"{job_id}_data.txt"
        shutil.copy2(source_file, data_file)
        
        # 创建任务记录
        job = Job(
            job_id=job_id,
            user_id=user_id,
            job_type=JobType.DATA_ANALYSIS,
            status=JobStatus.SUBMITTED,
            input_params=json.dumps({
                "analysis_type": "pca",
                "source_file_id": file_id,
                "confidence": confidence,
                "boundary": boundary,
                "permanova": permanova,
                "method": method,
                "original_filename": file_record.original_name
            }, ensure_ascii=False),
            created_at=datetime.now()
        )
        db.add(job)
        db.commit()
        
        # 构建 R 脚本命令
        boundary_str = "TRUE" if boundary else "FALSE"
        permanova_str = "TRUE" if permanova else "FALSE"
        
        cmd_args = [
            f"-i {data_file}",
            f"-j {job_id}",
            f"-c {confidence}",
            f"-b {boundary_str}",
            f"-p {permanova_str}"
        ]
        if permanova and method:
            cmd_args.append(f"-m {method}")
        
        r_script_path = str(R_SCRIPTS_DIR / "pca.R")
        cmd = f"{RSCRIPT_PATH} {RSCRIPT_OPTIONS} {r_script_path} {' '.join(cmd_args)}"
        
        # 保存命令到 config 文件
        config_file = job_dir / "config.txt"
        with open(config_file, "w") as f:
            f.write(f"command: {cmd}\n")
        
        # 异步执行 R 脚本（在后台执行）
        _schedule_r_script_execution(job_id, cmd, job_dir, user_id, "PCA分析")
        
        result = {
            "success": True,
            "message": "PCA 分析任务已提交",
            "job_id": job_id,
            "status": "Submitted",
            "hint": f"可以使用 get_job_detail 工具查询任务进度，job_id: {job_id}"
        }
        
        logger.info(f"[Analysis Tools] PCA 分析任务已提交: {job_id}")
        
        if should_close_db:
            db.close()
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"[Analysis Tools] run_pca_analysis 失败: {e}")
        if db:
            db.rollback()
            db.close()
        return json.dumps({"error": f"提交 PCA 分析失败: {str(e)}"}, ensure_ascii=False)


@tool
def run_volcano_plot(
    file_id: str,
    fc_threshold: float = 1.0,
    padj_threshold: float = 0.05,
    top: int = 10,
    config: Annotated[RunnableConfig, InjectedToolArg] = {}
) -> str:
    """
    生成火山图（Volcano Plot）。
    
    对差异表达分析结果生成火山图，展示基因表达变化和显著性。
    
    参数说明：
    - file_id: 差异表达数据文件 ID（必填）。文件应包含 log2FC 和 p-value 列
    - fc_threshold: log2 Fold Change 阈值，默认 1.0
    - padj_threshold: 调整后 P 值阈值，默认 0.05
    - top: 标注的 Top 基因数量，默认 10
    
    返回：作业提交结果，包含 job_id 用于查询分析进度
    
    Args:
        file_id: 数据文件 ID
        fc_threshold: FC 阈值
        padj_threshold: 调整后 P 值阈值
        top: Top 基因数量
        config: LangChain 运行配置
        
    Returns:
        JSON 格式的作业提交结果
    """
    logger.info(f"[Analysis Tools] run_volcano_plot 调用, file_id={file_id}")
    
    db = None
    try:
        # 从配置中获取用户 ID
        configurable = config.get("configurable", {}) if config else {}
        user_id = configurable.get("user_id")
        tool_context = configurable.get("tool_context", {})
        
        if not user_id:
            logger.warning("[Analysis Tools] user_id 为空，config 内容: %s", configurable)
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 确保 user_id 为整数（数据库字段为 Integer）
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"[Analysis Tools] user_id 类型转换失败: {user_id}")
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 创建数据库会话
        db = SessionLocal()
        should_close_db = True
        
        # 获取用户文件
        file_record = _get_user_file(db, file_id, user_id)
        if not file_record:
            if should_close_db:
                db.close()
            return json.dumps({
                "error": f"文件不存在或无权访问: {file_id}",
                "hint": "请使用 list_user_files 工具查看可用文件"
            }, ensure_ascii=False)
        
        # 验证文件存在
        source_file = Path(file_record.file_path)
        if not source_file.exists():
            if should_close_db:
                db.close()
            return json.dumps({"error": "文件物理不存在，可能已被删除"}, ensure_ascii=False)
        
        # 生成任务 ID 和目录
        job_id = _generate_job_id()
        job_dir, result_dir = _create_job_dirs(job_id)
        
        # 复制源文件到任务目录
        import shutil
        data_file = job_dir / f"{job_id}_data.txt"
        shutil.copy2(source_file, data_file)
        
        # 创建任务记录
        job = Job(
            job_id=job_id,
            user_id=user_id,
            job_type=JobType.DATA_ANALYSIS,
            status=JobStatus.SUBMITTED,
            input_params=json.dumps({
                "analysis_type": "volcano",
                "source_file_id": file_id,
                "fc_threshold": fc_threshold,
                "padj_threshold": padj_threshold,
                "top": top,
                "original_filename": file_record.original_name
            }, ensure_ascii=False),
            created_at=datetime.now()
        )
        db.add(job)
        db.commit()
        
        # 构建 R 脚本命令
        cmd_args = [
            f"-i {data_file}",
            f"-j {job_id}",
            "-g none",  # GMT 文件路径
            f"--fc_thr {fc_threshold}",
            f"--padj_thr {padj_threshold}",
            f"--top {top}",
            f"--top_fc_thr {fc_threshold}",
            f"--top_padj_thr {padj_threshold}"
        ]
        
        r_script_path = str(R_SCRIPTS_DIR / "volcano_gsea_padj.R")
        cmd = f"{RSCRIPT_PATH} {RSCRIPT_OPTIONS} {r_script_path} {' '.join(cmd_args)}"
        
        # 保存命令到 config 文件
        config_file = job_dir / "config.txt"
        with open(config_file, "w") as f:
            f.write(f"command: {cmd}\n")
        
        # 异步执行 R 脚本
        _schedule_r_script_execution(job_id, cmd, job_dir, user_id, "火山图分析")
        
        result = {
            "success": True,
            "message": "火山图分析任务已提交",
            "job_id": job_id,
            "status": "Submitted",
            "hint": f"可以使用 get_job_detail 工具查询任务进度，job_id: {job_id}"
        }
        
        logger.info(f"[Analysis Tools] 火山图分析任务已提交: {job_id}")
        
        if should_close_db:
            db.close()
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"[Analysis Tools] run_volcano_plot 失败: {e}")
        if db:
            db.rollback()
            db.close()
        return json.dumps({"error": f"提交火山图分析失败: {str(e)}"}, ensure_ascii=False)


@tool
def run_diff_expression(
    expression_file_id: str,
    group_file_id: str,
    fc_threshold: float = 1.0,
    padj_threshold: float = 0.05,
    data_type: str = "read_counts",
    correction: str = "BH",
    config: Annotated[RunnableConfig, InjectedToolArg] = {}
) -> str:
    """
    执行差异表达分析。
    
    使用 DESeq2（read counts）或 limma（FPKM/TPM）进行差异表达分析。
    
    参数说明：
    - expression_file_id: 表达矩阵文件 ID（必填）。行为基因，列为样本
    - group_file_id: 分组信息文件 ID（必填）。包含样本名和分组信息
    - fc_threshold: log2 Fold Change 阈值，默认 1.0
    - padj_threshold: 调整后 P 值阈值，默认 0.05
    - data_type: 数据类型，可选值：
        - read_counts: 原始 read counts（使用 DESeq2）
        - fpkm: FPKM/TPM 标准化数据（使用 limma）
    - correction: P 值校正方法，默认 "BH"（Benjamini-Hochberg）
    
    返回：作业提交结果，包含 job_id 用于查询分析进度
    
    Args:
        expression_file_id: 表达矩阵文件 ID
        group_file_id: 分组信息文件 ID
        fc_threshold: FC 阈值
        padj_threshold: 调整后 P 值阈值
        data_type: 数据类型
        correction: P 值校正方法
        config: LangChain 运行配置
        
    Returns:
        JSON 格式的作业提交结果
    """
    logger.info(f"[Analysis Tools] run_diff_expression 调用, expression_file={expression_file_id}, group_file={group_file_id}")
    
    db = None
    try:
        # 从配置中获取用户 ID
        configurable = config.get("configurable", {}) if config else {}
        user_id = configurable.get("user_id")
        tool_context = configurable.get("tool_context", {})
        
        if not user_id:
            logger.warning("[Analysis Tools] user_id 为空，config 内容: %s", configurable)
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 确保 user_id 为整数（数据库字段为 Integer）
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"[Analysis Tools] user_id 类型转换失败: {user_id}")
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 创建数据库会话
        db = SessionLocal()
        should_close_db = True
        
        # 获取表达矩阵文件
        expr_file_record = _get_user_file(db, expression_file_id, user_id)
        if not expr_file_record:
            if should_close_db:
                db.close()
            return json.dumps({
                "error": f"表达矩阵文件不存在或无权访问: {expression_file_id}",
                "hint": "请使用 list_user_files 工具查看可用文件"
            }, ensure_ascii=False)
        
        # 获取分组信息文件
        group_file_record = _get_user_file(db, group_file_id, user_id)
        if not group_file_record:
            if should_close_db:
                db.close()
            return json.dumps({
                "error": f"分组信息文件不存在或无权访问: {group_file_id}",
                "hint": "请使用 list_user_files 工具查看可用文件"
            }, ensure_ascii=False)
        
        # 验证文件存在
        expr_source = Path(expr_file_record.file_path)
        group_source = Path(group_file_record.file_path)
        
        if not expr_source.exists():
            if should_close_db:
                db.close()
            return json.dumps({"error": "表达矩阵文件物理不存在"}, ensure_ascii=False)
        
        if not group_source.exists():
            if should_close_db:
                db.close()
            return json.dumps({"error": "分组信息文件物理不存在"}, ensure_ascii=False)
        
        # 验证 data_type
        if data_type not in ["read_counts", "fpkm"]:
            if should_close_db:
                db.close()
            return json.dumps({
                "error": f"无效的数据类型: {data_type}",
                "valid_types": ["read_counts", "fpkm"]
            }, ensure_ascii=False)
        
        # 生成任务 ID 和目录
        job_id = _generate_job_id()
        job_dir, result_dir = _create_job_dirs(job_id)
        
        # 复制源文件到任务目录
        import shutil
        data_file = job_dir / f"{job_id}_data.txt"
        info_file = job_dir / f"{job_id}_info.txt"
        shutil.copy2(expr_source, data_file)
        shutil.copy2(group_source, info_file)
        
        # 创建任务记录
        job = Job(
            job_id=job_id,
            user_id=user_id,
            job_type=JobType.DATA_ANALYSIS,
            status=JobStatus.SUBMITTED,
            input_params=json.dumps({
                "analysis_type": "differential_expression",
                "expression_file_id": expression_file_id,
                "group_file_id": group_file_id,
                "fc_threshold": fc_threshold,
                "padj_threshold": padj_threshold,
                "data_type": data_type,
                "correction": correction,
                "expression_filename": expr_file_record.original_name,
                "group_filename": group_file_record.original_name
            }, ensure_ascii=False),
            created_at=datetime.now()
        )
        db.add(job)
        db.commit()
        
        # 根据数据类型选择 R 脚本
        if data_type == "read_counts":
            r_script = "DESeq2_read_count.R"
        else:
            r_script = "limma_fpkm_df.R"
        
        # 构建 R 脚本命令
        cmd_args = [
            f"-i {data_file}",
            f"-k {info_file}",
            f"-j {job_id}",
            f"-c {fc_threshold}",
            f"-d {padj_threshold}",
            f"-e {correction}"
        ]
        
        r_script_path = str(settings.path_code / r_script)
        cmd = f"{RSCRIPT_PATH} {RSCRIPT_OPTIONS} {r_script_path} {' '.join(cmd_args)}"
        
        # 保存命令到 config 文件
        config_file = job_dir / "config.txt"
        with open(config_file, "w") as f:
            f.write(f"command: {cmd}\n")
        
        # 异步执行 R 脚本
        _schedule_r_script_execution(job_id, cmd, job_dir, user_id, "差异表达分析")
        
        result = {
            "success": True,
            "message": "差异表达分析任务已提交",
            "job_id": job_id,
            "status": "Submitted",
            "analysis_method": "DESeq2" if data_type == "read_counts" else "limma",
            "hint": f"可以使用 get_job_detail 工具查询任务进度，job_id: {job_id}"
        }
        
        logger.info(f"[Analysis Tools] 差异表达分析任务已提交: {job_id}")
        
        if should_close_db:
            db.close()
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"[Analysis Tools] run_diff_expression 失败: {e}")
        if db:
            db.rollback()
            db.close()
        return json.dumps({"error": f"提交差异表达分析失败: {str(e)}"}, ensure_ascii=False)


def _schedule_r_script_execution(job_id: str, cmd: str, job_dir: Path, user_id: int, analysis_name: str):
    """
    调度 R 脚本执行（在后台线程中执行）
    
    Args:
        job_id: 任务 ID
        cmd: 完整的 R 脚本命令
        job_dir: 任务目录
        user_id: 用户 ID
        analysis_name: 分析名称
    """
    import threading
    
    def run_script():
        import subprocess
        
        db = None
        try:
            db = SessionLocal()
            
            # 更新状态为处理中
            job = db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.now()
                job.updated_at = datetime.now()
                db.commit()
            
            # 执行 R 脚本
            terminal_log = job_dir / "terminal_msg.txt"
            full_cmd = f"{cmd} > {terminal_log} 2>&1"
            
            logger.info(f"[Analysis Tools] 执行 R 脚本: {full_cmd}")
            
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            
            # 更新任务结果
            job = db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                result_dir = job_dir / "result"
                if result.returncode == 0:
                    job.status = JobStatus.COMPLETED
                    job.result_file = str(result_dir)
                    job.output_params = json.dumps({
                        "result_dir": str(result_dir),
                        "terminal_log": str(terminal_log)
                    }, ensure_ascii=False)
                else:
                    # 读取错误日志
                    error_msg = ""
                    if terminal_log.exists():
                        with open(terminal_log, "r") as f:
                            error_msg = f.read()[-1000:]
                    job.status = JobStatus.FAILED
                    job.error_message = error_msg or "R脚本执行失败"
                
                job.completed_at = datetime.now()
                job.updated_at = datetime.now()
                db.commit()
                
                logger.info(f"[Analysis Tools] {analysis_name}完成: job_id={job_id}, status={job.status}")
                
        except Exception as e:
            logger.error(f"[Analysis Tools] {analysis_name}执行失败: job_id={job_id}, error={str(e)}")
            if db:
                try:
                    job = db.query(Job).filter(Job.job_id == job_id).first()
                    if job:
                        job.status = JobStatus.FAILED
                        job.error_message = str(e)
                        job.updated_at = datetime.now()
                        db.commit()
                except:
                    pass
        finally:
            if db:
                db.close()
    
    # 在后台线程中执行
    thread = threading.Thread(target=run_script, daemon=True)
    thread.start()
