"""
AI Agent 工具模块
导出所有可用工具供 Agent 使用
"""
from api.agent.tools.job_tools import query_jobs, get_job_detail
from api.agent.tools.file_tools import list_user_files, get_file_info
from api.agent.tools.analysis_tools import (
    run_pca_analysis,
    run_volcano_plot,
    run_diff_expression
)


def get_all_tools() -> list:
    """
    获取所有可用的 Agent 工具
    
    Returns:
        工具函数列表，供 LangGraph Agent 使用
    """
    return [
        # 作业查询工具
        query_jobs,
        get_job_detail,
        # 文件管理工具
        list_user_files,
        get_file_info,
        # 分析工具
        run_pca_analysis,
        run_volcano_plot,
        run_diff_expression,
    ]


__all__ = [
    "get_all_tools",
    "query_jobs",
    "get_job_detail",
    "list_user_files",
    "get_file_info",
    "run_pca_analysis",
    "run_volcano_plot",
    "run_diff_expression",
]
