#!/usr/bin/env python3
"""
数据库表结构创建脚本
执行此脚本来创建文件上传功能所需的数据库表
"""

import pymysql
import sys
from config.database import DATABASE_URL

def create_database_tables():
    """创建文件上传相关的数据库表"""
    
    # 解析数据库连接信息
    import re
    db_match = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if not db_match:
        print("❌ 无法解析数据库连接URL")
        return False
    
    username, password, host, port, database = db_match.groups()
    
    # SQL语句
    sql_statements = [
        # 文件信息表
        """
        CREATE TABLE IF NOT EXISTS training_files (
            id VARCHAR(36) PRIMARY KEY COMMENT '文件唯一标识符(UUID)',
            original_filename VARCHAR(255) NOT NULL COMMENT '原始文件名',
            stored_filename VARCHAR(255) NOT NULL COMMENT '存储文件名(带UUID)',
            file_path VARCHAR(500) NOT NULL COMMENT '文件存储路径',
            file_size BIGINT NOT NULL COMMENT '文件大小(字节)',
            mime_type VARCHAR(100) COMMENT 'MIME类型',
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
            created_by INT COMMENT '上传用户ID',
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
        ) COMMENT='训练文件信息表'
        """,
        
        # 任务文件关联表
        """
        CREATE TABLE IF NOT EXISTS task_files (
            task_id INT NOT NULL COMMENT '训练任务ID',
            file_id VARCHAR(36) NOT NULL COMMENT '文件ID',
            file_type ENUM('dataset', 'train', 'validation', 'test', 'kfold_dataset') NOT NULL COMMENT '文件类型',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '关联时间',
            PRIMARY KEY (task_id, file_id, file_type),
            FOREIGN KEY (task_id) REFERENCES training_tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (file_id) REFERENCES training_files(id) ON DELETE CASCADE
        ) COMMENT='任务文件关联表'
        """,
        
        # 添加索引
        "CREATE INDEX idx_training_files_created_by ON training_files(created_by)",
        "CREATE INDEX idx_training_files_upload_time ON training_files(upload_time)",
        "CREATE INDEX idx_task_files_task_id ON task_files(task_id)",
        "CREATE INDEX idx_task_files_file_id ON task_files(file_id)",
        
        # 确保training_tasks表的parameters字段支持TEXT类型
        "ALTER TABLE training_tasks MODIFY COLUMN parameters TEXT COMMENT '训练参数(JSON格式)'"
    ]
    
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
            
            for i, sql in enumerate(sql_statements, 1):
                print(f"执行语句 {i}/{len(sql_statements)}...")
                cursor.execute(sql)
            
            connection.commit()
            print("✅ 数据库表创建完成!")
            
            # 验证表创建
            cursor.execute("SHOW TABLES LIKE 'training_files'")
            if cursor.fetchone():
                print("✅ training_files 表创建成功")
            else:
                print("❌ training_files 表创建失败")
                
            cursor.execute("SHOW TABLES LIKE 'task_files'")
            if cursor.fetchone():
                print("✅ task_files 表创建成功")
            else:
                print("❌ task_files 表创建失败")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("🔧 AutoMATA 文件上传功能数据库初始化")
    print("=" * 50)
    
    success = create_database_tables()
    
    if success:
        print("\n🎉 数据库初始化成功!")
        print("\n下一步:")
        print("1. 重启FastAPI服务以加载新的路由")
        print("2. 测试文件上传API端点")
        print("3. 验证文件存储和关联功能")
    else:
        print("\n💥 数据库初始化失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()