"""
模型训练相关的 Pydantic 模型

设计风格尽量与数据处理模块 (`schemas.data_process`) 保持一致：
- 仅提供 Request / Response 两类模型用于创建任务和返回结果
"""
from typing import Any, Optional, Dict
from datetime import datetime
import re

from pydantic import BaseModel, Field, validator


class TrainingTaskBase(BaseModel):
    """训练任务基础字段（Request 共用）"""

    task_name: str = Field(..., min_length=1, max_length=200, description="任务名称")
    model_type: str = Field(..., pattern=r"^(cnn|lstm|rnn|mlp|autoencoder|transformer|rbfn|all)$", 
                           description="模型类型，如 cnn、lstm、mlp 等")
    parameters: Dict[str, Any] = Field(..., min_items=1, description="训练参数字典")
    dataset_path: Optional[str] = Field(None, max_length=500, description="主数据集路径或目录")

    @validator('dataset_path')
    def validate_dataset_path(cls, v):
        """验证数据集路径格式"""
        if v is not None:
            # 基本路径格式检查
            if not re.match(r'^[/\w\-_.]+$', v):
                raise ValueError('数据集路径包含非法字符')
            # 检查是否包含路径遍历字符
            if '..' in v or '~' in v:
                raise ValueError('数据集路径不能包含相对路径符号')
        return v

    @validator('parameters')
    def validate_parameters(cls, v):
        """验证训练参数"""
        if not isinstance(v, dict):
            raise ValueError('参数必须是字典类型')
        
        # 检查必需参数
        required_params = ['strategy']
        for param in required_params:
            if param not in v:
                raise ValueError(f'缺少必需参数: {param}')
        
        # 验证策略参数
        strategy = v.get('strategy')
        if strategy not in ['split', 'upload', 'kfold']:
            raise ValueError('strategy 必须是 split, upload 或 kfold')
            
        return v


class TrainingTaskCreate(TrainingTaskBase):
    """创建训练任务请求模型"""
    # 与数据处理模块的 *ProcessRequest 类似，仅用于提交参数


class TrainingTaskResponse(BaseModel):
    """
    训练任务响应模型

    对应数据处理模块中的 *ProcessResponse：
    - 返回 job_id / status / message / created_at
    - 为了前端方便，这里额外包含 task_name / model_type 等字段
    """

    task_name: str
    model_type: str
    status: str
    job_id: str
    created_at: datetime
    message: str = Field("训练任务已提交", description="简单的提示信息")

    class Config:
        from_attributes = True
