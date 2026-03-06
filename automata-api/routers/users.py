from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from config.database import get_db
from models.user import User
from schemas.user import UserCreate, UserUpdate, User
from services.user_service import create_user, get_users, get_user, update_user, delete_user, get_user_by_username, get_user_by_email

router = APIRouter(prefix="/api/users")


@router.post("/", response_model=User)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    """
    创建新用户
    """
    # 检查用户名和邮箱是否已存在
    existing_user = get_user_by_username(db, username=user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    existing_email = get_user_by_email(db, email=user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return create_user(db=db, user=user)


@router.get("/", response_model=List[User])
def get_users_endpoint(
    skip: int = 0, 
    limit: int = 100, 
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    获取用户列表，支持分页和激活状态过滤
    """
    users = get_users(db, skip=skip, limit=limit, active_only=active_only)
    return users


@router.get("/{user_id}", response_model=User)
def get_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取单个用户
    """
    user = get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=User)
def update_user_endpoint(
    user_id: int, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db)
):
    """
    更新用户信息
    """
    updated_user = update_user(
        db, 
        user_id=user_id, 
        user_update=user_update
    )
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.delete("/{user_id}")
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    """
    删除用户
    """
    deleted = delete_user(db, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}