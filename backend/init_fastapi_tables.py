#!/usr/bin/env python3
"""
初始化FastAPI后端所需的数据库表结构
"""

from sqlalchemy import create_engine, text
from config.database import Base
from config.settings import settings
import sys

def create_fastapi_tables():
    """创建FastAPI后端所需的表"""
    print("🔧 初始化FastAPI数据库表结构")
    print("=" * 50)
    
    try:
        # 创建引擎
        engine = create_engine(settings.DATABASE_URL, echo=True)
        print(f"✅ 连接到数据库: {settings.DB_NAME}")
        
        # 检查现有表
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            existing_tables = [row[0] for row in result.fetchall()]
            print(f"📋 现有表: {existing_tables}")
            
            # 检查是否已有users表
            if 'users' in existing_tables:
                print("⚠️  users表已存在")
                response = input("是否要重建表结构？(y/N): ")
                if response.lower() != 'y':
                    print("取消操作")
                    return False
            else:
                print("✅ users表不存在，将创建新表")
        
        # 创建所有表
        print("\n🏗️  创建表结构...")
        Base.metadata.create_all(bind=engine)
        print("✅ 表结构创建完成")
        
        # 验证创建的表
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            print(f"\n📋 当前表结构: {tables}")
            
            # 检查关键表是否存在
            required_tables = ['users', 'jobs', 'files', 'job_files', 'job_logs']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ 缺少表: {missing_tables}")
                return False
            else:
                print("✅ 所有必需表都已创建")
                return True
                
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False

def create_sample_data():
    """创建示例数据"""
    print("\n📝 创建示例数据...")
    
    try:
        from sqlalchemy.orm import sessionmaker
        from api.models.user import User
        from api.models.job import Job, JobType
        from datetime import datetime
        
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 创建示例用户
        sample_user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S",  # bcrypt hash of "password123"
            is_active=True,
            is_admin=False
        )
        db.add(sample_user)
        db.commit()
        print("✅ 示例用户创建成功")
        
        # 创建示例作业
        sample_job = Job(
            job_id="TEST_JOB_001",
            job_type=JobType.MODEL_TRAIN,
            created_by=sample_user.id,
            status="pending",
            progress=0
        )
        db.add(sample_job)
        db.commit()
        print("✅ 示例作业创建成功")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 创建示例数据失败: {e}")
        return False

if __name__ == "__main__":
    print("AutoMATA FastAPI数据库初始化工具")
    print("=" * 50)
    
    # 创建表结构
    if create_fastapi_tables():
        # 创建示例数据
        if create_sample_data():
            print("\n🎉 数据库初始化完成!")
            print("现在可以运行测试了。")
            sys.exit(0)
        else:
            print("\n⚠️  表结构创建成功，但示例数据创建失败。")
            sys.exit(1)
    else:
        print("\n❌ 数据库初始化失败。")
        sys.exit(1)