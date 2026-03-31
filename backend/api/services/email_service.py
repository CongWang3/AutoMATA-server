"""
邮件通知服务：在任务完成后发送结果邮件给用户
"""
import os
import logging
import smtplib
import tempfile
import zipfile
import html as html_module
import re
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, Tuple
import asyncio

logger = logging.getLogger(__name__)


class EmailService:
    """邮件通知服务"""
    
    def __init__(self):
        try:
            from config.settings import settings as app_settings  # local project config
        except Exception:
            app_settings = None

        # 优先使用 config.settings（pydantic 已从 backend/.env 读取），
        # 避免 os.getenv 在当前进程中拿不到 .env 注入值导致 smtp_password_configured=false。
        if app_settings is not None:
            self.smtp_host = getattr(app_settings, "SMTP_HOST", "smtp.163.com")
            self.smtp_port = int(getattr(app_settings, "SMTP_PORT", 465))
            self.smtp_user = getattr(app_settings, "SMTP_USER", "wanger0808@163.com")
            self.smtp_password = getattr(app_settings, "SMTP_PASSWORD", "")
            self.smtp_ssl = bool(getattr(app_settings, "SMTP_SSL", False))
            self.from_name = getattr(app_settings, "SMTP_FROM_NAME", "AutoMATA")
            self.enabled = bool(getattr(app_settings, "EMAIL_ENABLED", True))
        else:
            # 回退：从环境变量读取 SMTP 配置
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
            loop = asyncio.get_running_loop()
            # SMTP 重试（指数退避）：应对偶发网络抖动/服务端瞬时断连
            max_attempts = 3
            base_delay_seconds = 1
            for attempt in range(1, max_attempts + 1):
                ok, category = await loop.run_in_executor(
                    None, self._send_email_sync_with_category, to_email, job_id, analysis_type, result_dir
                )
                if ok:
                    return True

                logger.warning(
                    f"结果邮件发送失败（第{attempt}/{max_attempts}次，分类={category}），job_id={job_id}, to={to_email}"
                )

                # 认证失败通常不是瞬时问题，避免无意义重试
                if category == "auth":
                    break

                if attempt < max_attempts:
                    await asyncio.sleep(base_delay_seconds * (2 ** (attempt - 1)))
            return False
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False

    @staticmethod
    def _format_failure_error_html(error_message: str, max_chars: int = 2000) -> str:
        """将失败的错误信息安全地格式化为 HTML（截断 + 转义 + 换行换成 <br/>）。"""
        if error_message is None:
            error_message = ""

        if max_chars < 0:
            max_chars = 0

        # 按 Unicode 字符截断，而非按字节
        truncated = error_message[:max_chars]
        # 统一行结束符，避免 \r\n 或 \r 不能被正确转成 <br/>
        normalized = truncated.replace("\r\n", "\n").replace("\r", "\n")
        escaped = html_module.escape(normalized)
        return escaped.replace("\n", "<br/>")

    @staticmethod
    def _sanitize_header_value(value: str) -> str:
        """
        清洗邮件头字段，防止 CR/LF 注入导致的 header splitting。
        仅移除头敏感字符（\\r / \\n），不改变调用方错误捕获语义。
        """
        if value is None:
            return ""
        return str(value).replace("\r", "").replace("\n", "")

    @staticmethod
    def _sanitize_attachment_job_id(job_id: str, max_len: int = 80) -> str:
        """
        清洗用于附件 filename 参数拼接的 job_id，防止：
        - CR/LF 导致 header splitting
        - 引号破坏 Content-Disposition 的 quoted-string
        - 路径/控制字符破坏或越界
        """
        s = "" if job_id is None else str(job_id)

        # Header splitting 防护
        s = s.replace("\r", "").replace("\n", "")
        # quoted-string 防护：Content-Disposition 使用 filename="..."; 需要移除引号
        s = s.replace('"', '').replace("'", "")
        # 路径/转义字符防护
        s = s.replace("\\", "")
        s = s.replace("/", "_")
        # 移除不可见控制字符
        s = re.sub(r"[\x00-\x1f\x7f]", "", s)
        # 限定为较安全的文件名字符；其余字符用 '_' 替换
        s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
        s = s.strip("_")

        if not s:
            s = "unknown"
        if max_len and max_len > 0:
            s = s[:max_len]
        return s

    # 成功/失败邮件主题与 HTML 正文中任务类型的英文展示
    _EMAIL_ANALYSIS_TYPE_EN = {
        "分析并训练": "Analyze and Train",
        "supervised模型训练": "Supervised model training",
        "unsupervised模型训练": "Unsupervised model training",
        "semi_supervised模型训练": "Semi-supervised model training",
        "模型训练": "Model training",
        "综合分析": "Comprehensive analysis",
        "基因组数据处理": "Genomic data processing",
        "转录组数据处理": "Transcriptomic data processing",
        "蛋白质数据处理": "Proteomic data processing",
        "多组学数据整合": "Multi-omics integration",
        "pvalue多组学整合": "P-value multi-omics integration",
    }
    _EMAIL_UNKNOWN_ANALYSIS_TYPE_EN = "Task"

    @staticmethod
    def _email_analysis_type_display_en(analysis_type: str) -> str:
        """
        将邮件中的任务类型转为英文展示：精确映射；`模型应用(x)` → Model use (x)；
        含中文但未映射则用固定英文；不含中日韩统一表意文字则保留原字符串。
        """
        raw = (analysis_type or "").strip()
        if not raw:
            return EmailService._EMAIL_UNKNOWN_ANALYSIS_TYPE_EN
        mapped = EmailService._EMAIL_ANALYSIS_TYPE_EN.get(raw)
        if mapped is not None:
            return mapped
        m = re.fullmatch(r"模型应用\((.*)\)\s*", raw)
        if m:
            inner = (m.group(1) or "").strip()
            return f"Model use ({inner})" if inner else "Model use"
        for ch in raw:
            if "\u4e00" <= ch <= "\u9fff":
                return EmailService._EMAIL_UNKNOWN_ANALYSIS_TYPE_EN
        return raw

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
            safe_from_name = self._sanitize_header_value(self.from_name)
            safe_smtp_user = self._sanitize_header_value(self.smtp_user)
            safe_to_email = self._sanitize_header_value(to_email)
            msg["From"] = f"{safe_from_name} <{safe_smtp_user}>"
            msg["To"] = safe_to_email
            display_type_en = self._email_analysis_type_display_en(analysis_type)
            safe_analysis_type_header = self._sanitize_header_value(display_type_en)
            msg["Subject"] = f"AutoMATA Failure - {safe_analysis_type_header}"

            safe_job_id = html_module.escape(str(job_id))
            safe_analysis_type = html_module.escape(display_type_en)
            formatted_error = self._format_failure_error_html(error_message, max_chars=2000)

            # 仅发送失败摘要 HTML；不附带任何 zip/result 附件
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <p>Dear user,</p>
                <p>Your <b>{safe_analysis_type}</b> task has <b>failed</b>.</p>
                <p><b>Job ID:</b> {safe_job_id}</p>
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
    
    def _send_email_sync_with_category(
        self,
        to_email: str,
        job_id: str,
        analysis_type: str,
        result_dir: Optional[str]
    ) -> Tuple[bool, str]:
        """同步发送邮件，并返回失败分类"""
        try:
            msg = MIMEMultipart()
            safe_from_name = self._sanitize_header_value(self.from_name)
            safe_smtp_user = self._sanitize_header_value(self.smtp_user)
            safe_to_email = self._sanitize_header_value(to_email)
            msg['From'] = f"{safe_from_name} <{safe_smtp_user}>"
            msg['To'] = safe_to_email
            display_type_en = self._email_analysis_type_display_en(analysis_type)
            safe_analysis_type_header = self._sanitize_header_value(display_type_en)
            msg['Subject'] = f'AutoMATA Result - {safe_analysis_type_header}'
            safe_analysis_type_html = html_module.escape(display_type_en)
            safe_job_id_html = html_module.escape(str(job_id))
            
            # HTML 邮件正文
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <p>Dear user,</p>
                <p>Your <b>{safe_analysis_type_html}</b> task has been completed.</p>
                <p><b>Job ID:</b> {safe_job_id_html}</p>
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

            temp_zip_paths: list[Path] = []

            def _mk_temp_zip_path() -> str:
                fd, zp = tempfile.mkstemp(suffix=".zip")
                os.close(fd)
                temp_zip_paths.append(Path(zp))
                return zp

            zip_path: Optional[str] = None
            if result_dir:
                result_path = Path(result_dir)
                if result_path.exists():
                    # 分析并训练：不附带完整 model_result.zip；从同级 result/ 打临时包（仅 png/txt/pth/pkl），发完删除
                    if self._is_analysis_train_mail_type(analysis_type):
                        result_subdir = (
                            result_path.parent / "result"
                            if result_path.suffix.lower() == ".zip"
                            else result_path
                        )
                        if result_subdir.is_dir():
                            zip_path = _mk_temp_zip_path()
                            self._create_zip(
                                str(result_subdir),
                                zip_path,
                                filter_func=lambda p: self._should_include_analysis_train_attachment_file(
                                    p
                                ),
                            )
                        elif result_path.suffix.lower() == ".zip" and result_path.is_file():
                            logger.warning(
                                "分析并训练邮件：未找到 result/ 目录，退化为附带传入的 zip: %s",
                                result_path,
                            )
                            zip_path = str(result_path)
                    elif result_path.suffix == ".zip" and result_path.is_file():
                        zip_path = str(result_path)
                    elif result_path.is_dir():
                        zip_path = f"{result_dir}.zip"
                        self._create_zip(
                            result_dir,
                            zip_path,
                            filter_func=lambda p: self._should_include_attachment_file(
                                analysis_type, p
                            ),
                        )
                    elif result_path.is_file():
                        zip_path = f"{result_dir}.zip"
                        self._create_single_file_zip(str(result_path), zip_path)

            try:
                if zip_path and Path(zip_path).exists():
                    with open(zip_path, "rb") as f:
                        part = MIMEBase("application", "zip")
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        safe_job_id = self._sanitize_attachment_job_id(job_id)
                        part.add_header(
                            "Content-Disposition",
                            f'attachment; filename="result_{safe_job_id}.zip"',
                        )
                        msg.attach(part)

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
                return True, "none"
            finally:
                for p in temp_zip_paths:
                    try:
                        p.unlink(missing_ok=True)
                    except OSError:
                        pass

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP认证失败（分类=auth）: {e}")
            return False, "auth"
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"SMTP连接失败（分类=connection，服务端断开）: {e}")
            return False, "connection"
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP连接失败（分类=connection，连接建立失败）: {e}")
            return False, "connection"
        except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused, smtplib.SMTPDataError, smtplib.SMTPHeloError) as e:
            logger.error(f"SMTP服务端拒绝（分类=refused）: {e}")
            return False, "refused"
        except (socket.timeout, TimeoutError) as e:
            logger.error(f"SMTP超时（分类=timeout）: {e}")
            return False, "timeout"
        except (ConnectionError, OSError) as e:
            logger.error(f"SMTP连接失败（分类=connection，网络/OSError）: {e}")
            return False, "connection"
        except smtplib.SMTPException as e:
            logger.error(f"SMTP发送失败（分类=smtp）: {e}")
            return False, "smtp"
        except Exception as e:
            logger.error(f"邮件发送异常（分类=unknown）: {e}")
            return False, "unknown"

    def _send_email_sync(
        self,
        to_email: str,
        job_id: str,
        analysis_type: str,
        result_dir: Optional[str]
    ) -> bool:
        """
        兼容旧调用：仅返回成功与否。
        新逻辑请优先使用 _send_email_sync_with_category。
        """
        ok, _ = self._send_email_sync_with_category(
            to_email=to_email,
            job_id=job_id,
            analysis_type=analysis_type,
            result_dir=result_dir
        )
        return ok
    
    @staticmethod
    def _create_zip(source_dir: str, zip_path: str, filter_func=None) -> None:
        """压缩目录为zip文件（支持按文件过滤）"""
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                source = Path(source_dir)
                for file in source.rglob('*'):
                    if file.is_file():
                        if filter_func and not filter_func(file):
                            continue
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

    @staticmethod
    def _is_analysis_train_mail_type(analysis_type: Optional[str]) -> bool:
        """分析并训练完成邮件：走 result/ 筛选附件分支（与 training/data_process/analysis 其它调用隔离）。"""
        if not analysis_type:
            return False
        if "分析并训练" in analysis_type:
            return True
        t = analysis_type.lower()
        if "analyze and train" in t:
            return True
        return "analyze" in t and "train" in t

    @staticmethod
    def _should_include_analysis_train_attachment_file(file_path: Path) -> bool:
        return file_path.suffix.lower() in {".png", ".txt", ".pth", ".pkl", "log"}

    @staticmethod
    def _should_include_attachment_file(analysis_type: str, file_path: Path) -> bool:
        """
        综合分析附件瘦身策略：
        - 仅保留 .png 与 .txt
        其它任务保持原样（全量文件）。
        """
        t = (analysis_type or "").lower()
        is_comprehensive = ("综合分析" in (analysis_type or "")) or ("comprehensive" in t)
        if not is_comprehensive:
            return True

        ext = file_path.suffix.lower()
        return ext in {".png", ".txt", ".log"}


# 全局单例
email_service = EmailService()
