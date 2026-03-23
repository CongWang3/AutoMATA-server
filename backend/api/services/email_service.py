"""
邮件通知服务：在任务完成后发送结果邮件给用户
"""
import os
import logging
import smtplib
import zipfile
import html as html_module
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)


class EmailService:
    """邮件通知服务"""
    
    def __init__(self):
        # 从环境变量读取 SMTP 配置
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.163.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '465'))
        self.smtp_user = os.getenv('SMTP_USER', 'wanger0808@163.com')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.smtp_ssl = os.getenv('SMTP_SSL', 'true').lower() == 'true'
        self.from_name = os.getenv('SMTP_FROM_NAME', 'AutoMATA')
        self.enabled = os.getenv('EMAIL_ENABLED', 'true').lower() == 'true'
    
    async def send_result_email(
        self,
        to_email: str,
        job_id: str,
        analysis_type: str,
        result_dir: Optional[str] = None
    ) -> bool:
        """
        发送分析结果邮件
        
        Args:
            to_email: 收件人邮箱
            job_id: 任务ID
            analysis_type: 分析类型名称
            result_dir: 结果目录路径（如果有，将打包为附件）
            
        Returns:
            是否发送成功
        """
        if not self.enabled or not to_email:
            logger.debug(f"邮件服务未启用或收件人为空: enabled={self.enabled}, to_email={to_email}")
            return False
        
        if not self.smtp_password:
            logger.warning("SMTP密码未配置，无法发送邮件")
            return False
            
        try:
            # 在线程池中执行同步SMTP操作避免阻塞
            return await asyncio.get_event_loop().run_in_executor(
                None, self._send_email_sync, to_email, job_id, analysis_type, result_dir
            )
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False

    @staticmethod
    def _format_failure_error_html(error_message: str, max_chars: int = 2000) -> str:
        """将失败的错误信息安全地格式化为 HTML（截断 + 转义 + 换行换成 <br/>）。"""
        if error_message is None:
            error_message = ""

        # 按 Unicode 字符截断，而非按字节
        truncated = error_message[:max_chars]
        escaped = html_module.escape(truncated)
        return escaped.replace("\n", "<br/>")

    def _send_failure_email_sync(
        self,
        to_email: str,
        job_id: str,
        analysis_type: str,
        error_message: str,
    ) -> bool:
        """同步发送失败邮件（用于线程池执行）。"""
        try:
            msg = MIMEMultipart()
            msg["From"] = f"{self.from_name} <{self.smtp_user}>"
            msg["To"] = to_email
            msg["Subject"] = f"AutoMATA Failure - {analysis_type}"

            formatted_error = self._format_failure_error_html(error_message, max_chars=2000)

            # 仅发送失败摘要 HTML；不附带任何 zip/result 附件
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <p>Dear user,</p>
                <p>Your <b>{analysis_type}</b> task has <b>failed</b>.</p>
                <p><b>Job ID:</b> {job_id}</p>
                <hr style="border: none; border-top: 1px solid #ccc;"/>
                <p><b>Error message:</b></p>
                <div style="white-space: normal; word-break: break-word; font-family: monospace;">
                    {formatted_error}
                </div>
                <br/>
                <p>Best regards,<br/><b>AutoMATA Platform</b></p>
                <p style="font-size: 12px; color: #888;">
                    This is an automated email. Please do not reply directly.
                </p>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, "html", "utf-8"))

            if self.smtp_ssl:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

            logger.info(f"失败邮件已发送至 {to_email}, JobID: {job_id}, Type: {analysis_type}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP认证失败: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP发送失败: {e}")
            return False
        except Exception as e:
            logger.error(f"失败邮件发送异常: {e}")
            return False

    async def send_failure_email(
        self,
        to_email: str,
        job_id: str,
        analysis_type: str,
        error_message: str,
    ) -> bool:
        """
        发送失败邮件给用户（用于任务失败后的错误通知）。

        强约束：任何 SMTP/mail 异常都只在内部捕获（仅记录日志并返回 False），不向调用方抛出异常。
        """
        if not self.enabled or not to_email:
            logger.debug(f"邮件服务未启用或收件人为空: enabled={self.enabled}, to_email={to_email}")
            return False

        if not self.smtp_password:
            logger.warning("SMTP密码未配置，无法发送邮件")
            return False

        try:
            # 在线程池中执行同步 SMTP 操作避免阻塞
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None,
                self._send_failure_email_sync,
                to_email,
                job_id,
                analysis_type,
                error_message,
            )
        except Exception as e:
            logger.error(f"发送失败邮件失败: {e}")
            return False
    
    def _send_email_sync(
        self,
        to_email: str,
        job_id: str,
        analysis_type: str,
        result_dir: Optional[str]
    ) -> bool:
        """同步发送邮件"""
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.smtp_user}>"
            msg['To'] = to_email
            msg['Subject'] = f'AutoMATA Result - {analysis_type}'
            
            # HTML 邮件正文
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <p>Dear user,</p>
                <p>Your <b>{analysis_type}</b> task has been completed.</p>
                <p><b>Job ID:</b> {job_id}</p>
                <p>The results are attached to this email.</p>
                <br/>
                <p>Best regards,<br/><b>AutoMATA Platform</b></p>
                <hr style="border: none; border-top: 1px solid #ccc;"/>
                <p style="font-size: 12px; color: #888;">
                    This is an automated email. Please do not reply directly.
                </p>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # 如果有结果目录，压缩并添加为附件
            zip_path = None
            if result_dir:
                result_path = Path(result_dir)
                if result_path.exists():
                    # 检查是否已经是 zip 文件
                    if result_path.suffix == '.zip' and result_path.is_file():
                        zip_path = str(result_path)
                    elif result_path.is_dir():
                        # 压缩目录
                        zip_path = f"{result_dir}.zip"
                        self._create_zip(result_dir, zip_path)
                    elif result_path.is_file():
                        # 单个结果文件，也打包成 zip
                        zip_path = f"{result_dir}.zip"
                        self._create_single_file_zip(str(result_path), zip_path)
            
            # 添加附件
            if zip_path and Path(zip_path).exists():
                with open(zip_path, 'rb') as f:
                    part = MIMEBase('application', 'zip')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="result_{job_id}.zip"'
                    )
                    msg.attach(part)
            
            # 发送邮件
            if self.smtp_ssl:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            
            logger.info(f"邮件已发送至 {to_email}, JobID: {job_id}, Type: {analysis_type}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP认证失败: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP发送失败: {e}")
            return False
        except Exception as e:
            logger.error(f"邮件发送异常: {e}")
            return False
    
    @staticmethod
    def _create_zip(source_dir: str, zip_path: str) -> None:
        """压缩目录为zip文件"""
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                source = Path(source_dir)
                for file in source.rglob('*'):
                    if file.is_file():
                        zipf.write(file, file.relative_to(source))
        except Exception as e:
            logger.error(f"压缩目录失败: {e}")
    
    @staticmethod
    def _create_single_file_zip(file_path: str, zip_path: str) -> None:
        """将单个文件压缩为zip"""
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(file_path, Path(file_path).name)
        except Exception as e:
            logger.error(f"压缩文件失败: {e}")


# 全局单例
email_service = EmailService()
