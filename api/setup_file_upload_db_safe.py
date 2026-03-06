#!/usr/bin/env python3
"""
安全的数据库表结构创建脚本
"""

import pymysql
import sys
from config.database import DATABASE_URL

def create_database_tables_safe():
    """安全地创建数据库表（忽略已存在的表和索引）"""
    
    # 解析数据库连接信息
    import re
    db_match = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if not db_match:
        print("❌ 无法解析数据库连接URL")
        return False
    
    username, password, host, port, database = db_match.groups()
    
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            print("🚀 开始创建数据库表...")
            
            # 检查并创建training_files表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_files (
                    id VARCHAR(36) PRIMARY KEY,
                    original_filename VARCHAR(255) NOT NULL,
                    stored_filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_size BIGINT NOT NULL,
                    mime_type VARCHAR(100),
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INT,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            print("✅ training_files 表检查完成")
            
            # 检查并创建task_files表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_files (
                    task_id INT NOT NULL,
                    file_id VARCHAR(36) NOT NULL,
                    file_type ENUM('dataset', 'train', 'validation', 'test', 'kfold_dataset') NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (task_id, file_id, file_type),
                    FOREIGN KEY (task_id) REFERENCES training_tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY (file_id) REFERENCES training_files(id) ON DELETE CASCADE
                )
            """)
            print("✅ task_files 表检查完成")
            
            # 检查现有索引
            cursor.execute("SHOW INDEX FROM training_files")
            existing_indexes = {row[2] for row in cursor.fetchall()}
            
            # 创建缺失的索引
            needed_indexes = [
                ("idx_training_files_created_by", "training_files(created_by)"),
                ("idx_training_files_upload_time", "training_files(upload_time)")
            ]
            
            for index_name, column_def in needed_indexes:
                if index_name not in existing_indexes:
                    cursor.execute(f"CREATE INDEX {index_name} ON {column_def}")
                    print(f"✅ 索引 {index_name} 创建成功")
                else:
                    print(f"ℹ️  索引 {index_name} 已存在")
            
            # 检查task_files索引
            cursor.execute("SHOW INDEX FROM task_files")
            existing_task_indexes = {row[2] for row in cursor.fetchall()}
            
            task_indexes = [
                ("idx_task_files_task_id", "task_files(task_id)"),
                ("idx_task_files_file_id", "task_files(file_id)")
            ]
            
            for index_name, column_def in task_indexes:
                if index_name not in existing_task_indexes:
                    cursor.execute(f"CREATE INDEX {index_name} ON {column_def}")
                    print(f"✅ 索引 {index_name} 创建成功")
                else:
                    print(f"ℹ️  索引 {index_name} 已存在")
            
            # 确保training_tasks表的parameters字段支持TEXT类型
            try:
                cursor.execute("ALTER TABLE training_tasks MODIFY COLUMN parameters TEXT")
                print("✅ training_tasks.parameters 字段类型更新完成")
            except pymysql.err.OperationalError as e:
                if "Duplicate column" in str(e):
                    print("ℹ️  training_tasks.parameters 字段已是正确类型")
                else:
                    raise e
            
            connection.commit()
            print("✅ 数据库表结构检查完成!")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {str(e)}")
        return False

def verify_tables():
    """验证表是否创建成功"""
    import re
    db_match = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    username, password, host, port, database = db_match.groups()
    
    try:
        connection = pymysql.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 验证表存在
            cursor.execute("SHOW TABLES LIKE 'training_files'")
            has_training_files = cursor.fetchone() is not None
            
            cursor.execute("SHOW TABLES LIKE 'task_files'")
            has_task_files = cursor.fetchone() is not None
            
            print(f"\n📊 数据库验证结果:")
            print(f"   training_files 表: {'✅ 存在' if has_training_files else '❌ 不存在'}")
            print(f"   task_files 表: {'✅ 存在' if has_task_files else '❌ 不存在'}")
            
            if has_training_files and has_task_files:
                print("🎉 数据库初始化完全成功!")
                return True
            else:
                print("⚠️  部分表创建失败")
                return False
                
        connection.close()
        
    except Exception as e:
        print(f"❌ 验证失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("🔧 AutoMATA 文件上传功能数据库安全初始化")
    print("=" * 50)
    
    success = create_database_tables_safe()
    
    if success:
        verify_tables()
        print("\n🚀 下一步:")
        print("1. 重启FastAPI服务加载新路由")
        print("2. 运行测试脚本验证功能")
        print("3. 开始使用文件上传API")
    else:
        print("\n💥 数据库初始化失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()