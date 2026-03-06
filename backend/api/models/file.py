"""
文件模型
"""
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from config.database import Base


class File(Base):
    """文件表"""
    
    __tablename__ = "files"
    
    id = Column(
        String(50), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()), 
        comment="文件 ID(UUID)"
    )
    filename = Column(String(255), nullable=False, index=True, comment="文件名")
    original_name = Column(String(255), comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_size = Column(BigInteger, nullable=False, comment="文件大小 (字节)")
    file_type = Column(String(50), index=True, comment="文件类型")
    mime_type = Column(String(100), comment="MIME 类型")
    md5_hash = Column(String(32), comment="MD5 哈希值")
    # 用户删除时其上传文件也应删除，因此使用 CASCADE
    uploaded_by = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True, 
        comment="上传用户 ID"
    )
    download_count = Column(Integer, default=0, comment="下载次数")
    is_public = Column(Boolean, default=False, comment="是否公开")
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="创建时间")
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        comment="更新时间"
    )
    
    # 关联关系
    uploader = relationship("User", back_populates="files")
    job_files = relationship("JobFile", back_populates="file")
    
    def __repr__(self):
        return f"<File(id={self.id}, filename={self.filename})>"
