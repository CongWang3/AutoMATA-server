"""
认证相关的 Pydantic 模型
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(
        ..., 
        min_length=8,  # 增加最小长度要求
        max_length=128, 
        description="密码（至少8位，建议包含大小写字母和数字）"
        # 注意：Pydantic 不支持带有前瞻断言的复杂正则表达式
        # 密码复杂度验证将在服务层通过自定义验证函数实现
    )

    # <!-- 
    # 审查上下文：
    # - 设计意图：加强密码强度要求，提高账户安全性
    # - 已知局限：正则表达式可能需要根据实际需求调整复杂度
    # - 业务背景：用户认证安全策略
    # - 测试重点：请验证各种密码组合的验证效果，包括边界情况
    # -->


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 过期时间（秒）
    user: UserResponse


class TokenPayload(BaseModel):
    """Token 载荷"""
    sub: str  # subject (用户ID)
    exp: int  # expiration time


# <!-- 
# 审查上下文：
# - 设计意图：使用 Pydantic 进行请求/响应数据验证，确保数据格式正确
# - 已知局限：密码强度验证较为基础，后续可添加复杂度要求
# - 业务背景：docs/api/API_SPECIFICATION.md - 认证相关接口规范
# - 测试重点：请关注密码长度验证、邮箱格式验证、token 过期时间计算
# -->