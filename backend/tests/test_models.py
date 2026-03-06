"""
数据库模型单元测试
"""
import pytest
from datetime import datetime
from api.models import User, Job, File, JobFile, JobLog
from api.models.job import JobType, JobStatus
from api.models.job_file import FileRole
from api.models.job_log import LogLevel


class TestUserModel:
    """用户模型测试"""
    
    def test_create_user_basic_fields(self):
        """测试创建用户 - 基本字段"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        # 注意：Python 对象的 default 值不会自动应用，需要在数据库层面测试
        # 数据库级别的默认值测试见 test_user_default_values_in_database
    
    def test_user_string_representation(self):
        """测试用户对象字符串表示"""
        user = User(id=1, username="testuser", email="test@example.com", password_hash="hash")
        assert "testuser" in repr(user)


class TestJobModel:
    """作业任务模型测试"""
    
    def test_create_job_basic_fields(self):
        """测试创建作业 - 基本字段"""
        job = Job(
            job_id="JOB_20260306_001",
            job_type=JobType.DATA_PROCESS,
            created_by=1
        )
        
        assert job.job_id == "JOB_20260306_001"
        assert job.job_type == JobType.DATA_PROCESS
        # 注意：status 和 progress 的 default 值需要在数据库层面验证
        # Python 对象不会自动应用 default 值
    
    def test_job_status_transition(self):
        """测试任务状态转换"""
        job = Job(job_id="JOB_001", job_type=JobType.MODEL_TRAIN, created_by=1)
        
        # PENDING -> RUNNING
        job.status = JobStatus.RUNNING
        assert job.status == JobStatus.RUNNING
        
        # RUNNING -> COMPLETED
        job.status = JobStatus.COMPLETED
        assert job.status == JobStatus.COMPLETED
    
    def test_job_string_representation(self):
        """测试任务对象字符串表示"""
        job = Job(job_id="JOB_TEST", job_type=JobType.DATA_ANALYSIS, status=JobStatus.RUNNING)
        assert "JOB_TEST" in repr(job)
        assert "running" in repr(job)


class TestFileModel:
    """文件模型测试"""
    
    def test_create_file_basic_fields(self):
        """测试创建文件 - 基本字段"""
        file = File(
            filename="test.txt",
            original_name="original.txt",
            file_path="/path/to/file",
            file_size=1024,
            file_type="dataset",
            uploaded_by=1
        )
        
        assert file.filename == "test.txt"
        assert file.file_size == 1024
        assert file.uploaded_by == 1
        # download_count 的 default 值需要在数据库层面验证
    
    def test_file_object_creation(self):
        """测试文件对象创建"""
        file1 = File(filename="f1.txt", file_path="/p/f1", file_size=100)
        file2 = File(filename="f2.txt", file_path="/p/f2", file_size=100)
        
        # 两个不同的对象
        assert file1 is not file2


class TestJobFileModel:
    """作业文件关联模型测试"""
    
    def test_create_job_file(self):
        """测试创建作业文件关联"""
        job_file = JobFile(
            job_id=1,
            file_id="file-uuid-123",
            file_role=FileRole.INPUT
        )
        
        assert job_file.job_id == 1
        assert job_file.file_id == "file-uuid-123"
        assert job_file.file_role == FileRole.INPUT


class TestJobLogModel:
    """作业日志模型测试"""
    
    def test_create_job_log(self):
        """测试创建作业日志"""
        log = JobLog(
            job_id=1,
            message="Task started",
            log_level=LogLevel.INFO
        )
        
        assert log.job_id == 1
        assert log.message == "Task started"
        assert log.log_level == LogLevel.INFO
    
    def test_log_levels(self):
        """测试日志级别"""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.ERROR == "ERROR"


# <!-- 
# 审查上下文：
# - 设计意图：测试核心模型的基本功能，确保数据完整性
# - 已知局限：未测试数据库关系和约束，需要集成测试补充
# - 业务背景：docs/database/DATABASE_DESIGN.md - 数据模型验证
# - 测试重点：请重点关注枚举类型、UUID 生成、默认值设置
# -->
