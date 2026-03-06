"""
用户服务层 - 处理用户相关的业务逻辑
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from api.models.user import User
from typing import Optional, List


class UserService:
    """用户服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, username: str, email: str, password: str) -> Optional[User]:
        """
        创建新用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码（实际应用中应该先哈希）
            
        Returns:
            创建的用户对象，如果失败返回 None
        """
        try:
            # 检查用户名是否已存在
            existing_user = self.get_user_by_username(username)
            if existing_user:
                raise ValueError(f"用户名 {username} 已存在")
            
            # 检查邮箱是否已存在
            existing_email = self.get_user_by_email(email)
            if existing_email:
                raise ValueError(f"邮箱 {email} 已被注册")
            
            # 创建新用户
            user = User(
                username=username,
                email=email,
                password_hash=f"hashed_{password}"  # 简化处理，实际应用使用 bcrypt
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            raise e
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """通过 ID 获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取所有用户（分页）"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """
        更新用户信息
        
        Args:
            user_id: 用户 ID
            **kwargs: 要更新的字段
            
        Returns:
            更新后的用户对象
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        验证用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            验证成功的用户对象，失败返回 None
        """
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        # 简化验证，实际应用应该比较哈希值
        if f"hashed_{password}" == user.password_hash:
            return user
        
        return None
