"""API 依赖模块"""
from .auth import (
    get_auth_service,
    get_current_user,
    get_current_active_user,
    get_current_admin_user
)

__all__ = [
    "get_auth_service",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user"
]