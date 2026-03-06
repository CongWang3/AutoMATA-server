"""
用户模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class User(Base):
    """用户表"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户 ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    avatar_url = Column(String(500), comment="头像 URL")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_admin = Column(Boolean, default=False, comment="是否管理员")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        comment="更新时间"
    )
    last_login_at = Column(DateTime, comment="最后登录时间")
    
    # 关联关系
    jobs = relationship("Job", back_populates="creator", cascade="all, delete-orphan")
    files = relationship("File", back_populates="uploader", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
