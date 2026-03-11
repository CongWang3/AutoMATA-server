#!/usr/bin/env python3
"""
创建系统清理用户脚本
用于解决定时清理任务中"系统清理用户不存在"的错误
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from config.database import SessionLocal
from api.models.user import User
from api.utils.security import get_password_hash
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_system_cleaner_user():
    """创建系统清理用户"""
    db = SessionLocal()
    
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == "system_cleaner").first()
        if existing_user:
            logger.info("✅ system_cleaner 用户已存在")
            logger.info(f"  ID: {existing_user.id}")
            logger.info(f"  邮箱: {existing_user.email}")
            logger.info(f"  管理员: {existing_user.is_admin}")
            return existing_user
        
        # 创建系统清理用户
        system_user = User(
            username="system_cleaner",
            email="system@automata.local",
            password_hash=get_password_hash("system_cleaner_password_123456"),  # 生成安全密码哈希
            is_active=True,
            is_admin=True,  # 设置为管理员权限以便执行清理任务
            avatar_url=None
        )
        
        db.add(system_user)
        db.commit()
        db.refresh(system_user)
        
        logger.info("✅ 成功创建 system_cleaner 用户")
        logger.info(f"  ID: {system_user.id}")
        logger.info(f"  用户名: {system_user.username}")
        logger.info(f"  邮箱: {system_user.email}")
        logger.info(f"  管理员: {system_user.is_admin}")
        
        return system_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 创建 system_cleaner 用户失败: {e}")
        raise
    finally:
        db.close()

def verify_system_user():
    """验证系统用户是否存在且配置正确"""
    db = SessionLocal()
    
    try:
        system_user = db.query(User).filter(User.username == "system_cleaner").first()
        
        if not system_user:
            logger.error("❌ system_cleaner 用户不存在")
            return False
            
        logger.info("🔍 系统用户验证:")
        logger.info(f"  ID: {system_user.id}")
        logger.info(f"  用户名: {system_user.username}")
        logger.info(f"  邮箱: {system_user.email}")
        logger.info(f"  激活状态: {system_user.is_active}")
        logger.info(f"  管理员权限: {system_user.is_admin}")
        logger.info(f"  创建时间: {system_user.created_at}")
        
        # 检查必要条件
        checks = [
            (system_user.is_active, "用户处于激活状态"),
            (system_user.is_admin, "用户具有管理员权限"),
            (system_user.email, "用户有有效邮箱")
        ]
        
        all_passed = True
        for check, description in checks:
            status = "✅" if check else "❌"
            logger.info(f"  {status} {description}")
            if not check:
                all_passed = False
                
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ 验证系统用户时出错: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 AutoMATA 系统用户创建工具")
    print("=" * 50)
    
    try:
        # 创建系统用户
        user = create_system_cleaner_user()
        
        # 验证用户
        print("\n🔍 验证系统用户配置...")
        is_valid = verify_system_user()
        
        if is_valid:
            print("\n🎉 系统用户创建和验证成功！")
            print("✅ 定时清理任务现在应该能够正常运行")
        else:
            print("\n⚠️  系统用户存在但配置可能有问题")
            
    except Exception as e:
        print(f"\n❌ 操作失败: {e}")
        sys.exit(1)
