"""
自定义异常类
"""
from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    """资源未找到异常"""
    
    def __init__(self, detail: str = "资源未找到"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class PermissionError(HTTPException):
    """权限不足异常"""
    
    def __init__(self, detail: str = "权限不足"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ValidationError(HTTPException):
    """数据验证异常"""
    
    def __init__(self, detail: str = "数据验证失败"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class AuthenticationError(HTTPException):
    """认证失败异常"""
    
    def __init__(self, detail: str = "认证失败"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)