"""
模型训练相关的 Pydantic 模型

设计风格尽量与数据处理模块 (`schemas.data_process`) 保持一致：
- 仅提供 Request / Response 两类模型用于创建任务和返回结果
"""
from typing import Any, Optional, Dict
from datetime import datetime
import re

from pydantic import BaseModel, Field, validator, ConfigDict


# 支持的模型类型映射
SUPPORTED_MODELS = {
    # 监督学习模型
    "supervised": ["cnn", "lstm", "rnn", "mlp", "autoencoder", "transformer", "rbfn", "som", "all"],
    # 无监督学习模型
    "unsupervised": ["vae", "deepcluster"],
    # 半监督学习模型
    "semi_supervised": ["ladder", "pseudo"]
}
ALL_MODELS = SUPPORTED_MODELS["supervised"] + SUPPORTED_MODELS["unsupervised"] + SUPPORTED_MODELS["semi_supervised"]
MODEL_TYPE_PATTERN = f"^({'|'.join(ALL_MODELS)})$"


class TrainingTaskBase(BaseModel):
    """训练任务基础字段（Request 共用）"""
    
    # 解决 Pydantic 警告
    model_config = ConfigDict(protected_namespaces=())

    task_name: str = Field(..., min_length=1, max_length=200, description="任务名称")
    model_type: str = Field(
        ..., 
        description="模型类型：监督 (cnn/lstm/rnn/mlp/autoencoder/transformer/rbfn/som/all)、无监督 (vae/deepcluster)、半监督 (ladder/pseudo)"
    )
    parameters: Dict[str, Any] = Field(..., description="训练参数字典")
    dataset_path: Optional[str] = Field(None, max_length=500, description="主数据集路径或目录")
    email: Optional[str] = Field(None, max_length=200, description="通知邮箱地址")

    @validator('dataset_path')
    def validate_dataset_path(cls, v):
        """验证数据集路径格式"""
        if v is not None:
            # 支持 file:// 协议前缀（前端上传文件后返回的格式）
            if v.startswith('file://'):
                # 提取 file:// 后面的部分进行验证
                path_part = v[7:]  # 去掉 'file://' 前缀
                if not re.match(r'^[\w\-_.]+$', path_part):
                    raise ValueError('file:// 后的路径包含非法字符')
            else:
                # 传统路径格式检查
                if not re.match(r'^[/\w\-_.]+$', v):
                    raise ValueError('数据集路径包含非法字符')
            # 检查是否包含路径遍历字符
            if '..' in v or '~' in v:
                raise ValueError('数据集路径不能包含相对路径符号')
        return v

    @validator('model_type')
    def validate_model_type(cls, v):
        """验证模型类型"""
        if v.lower() not in ALL_MODELS:
            raise ValueError(f'不支持的模型类型: {v}，支持的类型: {ALL_MODELS}')
        return v.lower()

    @validator('parameters', pre=True)
    def parse_parameters(cls, v):
        """解析参数（支持JSON字符串或字典）"""
        import json
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('parameters 必须是有效的JSON字符串或字典')
        if not isinstance(v, dict):
            raise ValueError('参数必须是字典类型')
        return v

    @validator('parameters')
    def validate_parameters(cls, v, values):
        """验证训练参数"""
        if not isinstance(v, dict):
            raise ValueError('参数必须是字典类型')
        
        # 检查必需参数 - strategy 是必须的
        if 'strategy' not in v:
            raise ValueError('缺少必需参数: strategy')
        
        # 验证策略参数
        strategy = v.get('strategy')
        if strategy not in ['split', 'upload', 'kfold']:
            raise ValueError('strategy 必须是 split, upload 或 kfold')
        
        # 根据策略验证必需参数
        if strategy == 'split':
            if 'split_ratio' not in v:
                # 使用默认值 7:2:1
                v['split_ratio'] = {'train': 7, 'validation': 2, 'test': 1}
        elif strategy == 'kfold':
            if 'kfold' not in v:
                v['kfold'] = 5  # 默认5折交叉验证
            
        # 验证数值参数范围（更宽松，允许更多场景）
        numeric_params = {
            'epochs': (1, 10000),
            'batch_size': (1, 2048),
            'learning_rate': (0.000001, 10.0),
            'kfold': (2, 20),
            'early_stopping': (1, 1000),
            'seed': (0, 2147483647),
            'label_count': (2, 1000),
            # 半监督特有参数
            'alpha': (0.0, 100.0),
            'beta': (0.0, 100.0),
            'gamma': (0.0, 100.0),
            'confidence_threshold': (0.0, 1.0),
            'pseudo_ratio': (0.0, 1.0)
        }
        
        for param, (min_val, max_val) in numeric_params.items():
            if param in v and v[param] is not None:
                try:
                    value = float(v[param])
                    if not (min_val <= value <= max_val):
                        raise ValueError(f'参数 {param} 超出有效范围 [{min_val}, {max_val}]')
                except (ValueError, TypeError):
                    raise ValueError(f'参数 {param} 必须是数值类型')
            
        return v


class TrainingTaskCreate(TrainingTaskBase):
    """创建训练任务请求模型"""
    # 与数据处理模块的 *ProcessRequest 类似，仅用于提交参数


class TrainingTaskResponse(BaseModel):
    """
    训练任务响应模型

    对应数据处理模块中的 *ProcessResponse：
    - 返回 job_id / status / message / created_at
    - 为了前端方便，这里额外包含 task_name / model_type / parameters 等字段
    """

    task_name: str
    model_type: str
    status: str
    job_id: str
    created_at: datetime
    message: str = Field("训练任务已提交", description="简单的提示信息")
    parameters: Optional[Any] = Field(None, description="训练参数（JSON解析后的字典或原始字符串）")
    progress: Optional[int] = Field(0, description="进度百分比 (0-100)")
    current_step: Optional[str] = Field(None, description="当前执行步骤描述")
    result_file: Optional[str] = Field(None, description="结果文件路径")
    error_message: Optional[str] = Field(None, description="错误信息")

    class Config:
        from_attributes = True
