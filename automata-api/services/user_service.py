from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate, UserUpdate
from typing import List, Optional
from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_user(db: Session, user: UserCreate):
    """
    创建新用户
    """
    hashed_password = hash_password(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int):
    """
    根据ID获取用户
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    """
    根据用户名获取用户
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str):
    """
    根据邮箱获取用户
    """
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True):
    """
    获取用户列表，支持分页和激活状态过滤
    """
    query = db.query(User)
    
    if active_only:
        query = query.filter(User.is_active == True)
    
    return query.offset(skip).limit(limit).all()


def update_user(db: Session, user_id: int, user_update: UserUpdate):
    """
    更新用户
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    """
    删除用户
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True