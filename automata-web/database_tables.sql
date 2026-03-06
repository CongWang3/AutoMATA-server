/*
AutoMATA训练文件管理数据库表
需要在MySQL数据库中执行这些SQL语句
*/

-- 文件信息表
CREATE TABLE IF NOT EXISTS training_files (
    id VARCHAR(36) PRIMARY KEY COMMENT '文件唯一标识符',
    original_filename VARCHAR(255) NOT NULL COMMENT '原始文件名',
    stored_filename VARCHAR(255) NOT NULL COMMENT '存储文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '文件存储路径',
    file_size BIGINT NOT NULL COMMENT '文件大小(字节)',
    mime_type VARCHAR(100) COMMENT 'MIME类型',
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    created_by INT COMMENT '上传用户ID',
    INDEX idx_created_by (created_by),
    INDEX idx_upload_time (upload_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='训练文件信息表';

-- 训练任务与文件关联表
CREATE TABLE IF NOT EXISTS task_files (
    task_id INT NOT NULL COMMENT '训练任务ID',
    file_id VARCHAR(36) NOT NULL COMMENT '文件ID',
    file_type ENUM('dataset', 'train', 'validation', 'test', 'kfold_dataset') NOT NULL COMMENT '文件类型',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '关联时间',
    PRIMARY KEY (task_id, file_id, file_type),
    FOREIGN KEY (task_id) REFERENCES training_tasks(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (file_id) REFERENCES training_files(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_task_id (task_id),
    INDEX idx_file_id (file_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='训练任务文件关联表';

-- 如果training_tasks表不存在，创建它
CREATE TABLE IF NOT EXISTS training_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '任务ID',
    task_name VARCHAR(255) NOT NULL COMMENT '任务名称',
    model_type VARCHAR(50) NOT NULL COMMENT '模型类型',
    language ENUM('python', 'r') DEFAULT 'python' COMMENT '编程语言',
    parameters JSON COMMENT '训练参数(JSON格式)',
    dataset_path VARCHAR(500) COMMENT '数据集路径',
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending' COMMENT '任务状态',
    created_by INT COMMENT '创建用户ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_model_type (model_type),
    INDEX idx_status (status),
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='训练任务表';

-- 训练日志表（如果不存在）
CREATE TABLE IF NOT EXISTS training_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    task_id INT NOT NULL COMMENT '任务ID',
    log_level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR') DEFAULT 'INFO' COMMENT '日志级别',
    message TEXT NOT NULL COMMENT '日志消息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (task_id) REFERENCES training_tasks(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_task_id (task_id),
    INDEX idx_log_level (log_level),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='训练日志表';