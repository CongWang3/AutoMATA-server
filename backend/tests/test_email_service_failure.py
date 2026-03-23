import asyncio
import html
from unittest.mock import MagicMock, patch

import pytest

from api.services.email_service import EmailService


def _extract_html_body(mime_msg) -> str:
    """从 MIMEMultipart 中提取 text/html 部分内容。"""
    for part in mime_msg.walk():
        if part.is_multipart():
            continue
        if part.get_content_type() == "text/html":
            payload = part.get_payload(decode=True)
            if isinstance(payload, (bytes, bytearray)):
                return payload.decode("utf-8", errors="replace")
            # 某些实现可能不返回 decode 后的 bytes
            return part.get_payload()
    raise AssertionError("未找到 text/html 部分")


def test_format_failure_error_html_escape_newline_and_truncate():
    assert hasattr(EmailService, "_format_failure_error_html")

    raw = "<x>\n" + ("A" * 3000)
    formatted = EmailService._format_failure_error_html(raw, max_chars=2000)

    expected = html.escape(raw[:2000]).replace("\n", "<br/>")
    assert formatted == expected
    assert "<x>" not in formatted
    assert "&lt;x&gt;" in formatted
    assert "<br/>" in formatted
    assert len(formatted) <= len(expected)


def test_format_failure_error_html_normalizes_crlf_to_br():
    assert hasattr(EmailService, "_format_failure_error_html")

    raw = "<x>\r\n" + ("A" * 50) + "\r" + ("B" * 50)
    formatted = EmailService._format_failure_error_html(raw, max_chars=2000)

    normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
    expected = html.escape(normalized).replace("\n", "<br/>")
    assert formatted == expected


def test_format_failure_error_html_handles_none_and_negative_max_chars():
    assert hasattr(EmailService, "_format_failure_error_html")

    # None 应被当作空字符串处理
    assert EmailService._format_failure_error_html(None, max_chars=10) == ""
    # max_chars < 0 按当前实现应归一为 0，结果为空
    assert EmailService._format_failure_error_html("abc\n<d>", max_chars=-1) == ""


def test_send_result_email_sanitizes_subject_and_from_headers() -> None:
    service = EmailService()
    service.enabled = True
    service.smtp_ssl = True
    service.smtp_password = "test-password"
    service.from_name = "AutoMATA\r\nBcc:evil@example.com"

    raw_from_name = service.from_name
    analysis_type = "Gene\r\nX-Injected: yes"

    with patch("api.services.email_service.smtplib.SMTP_SSL") as mock_smtp_ssl:
        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        ok = service._send_email_sync(
            to_email="user@example.com",
            job_id="job-1",
            analysis_type=analysis_type,
            result_dir=None,
        )

        assert ok is True
        mock_server.send_message.assert_called_once()
        msg = mock_server.send_message.call_args[0][0]

        subject = str(msg["Subject"])
        from_header = str(msg["From"])

        # Subject 中不应保留 CR/LF 或注入片段
        assert "\r" not in subject and "\n" not in subject
        assert "GeneX-Injected: yes" in subject

        # From 中同样应做 header-safe 清洗，避免额外头字段注入
        assert "\r" not in from_header and "\n" not in from_header
        expected_from_name = EmailService._sanitize_header_value(raw_from_name)
        assert expected_from_name in from_header


def test_send_failure_email_formats_safe_html_and_sends_once() -> None:
    assert hasattr(EmailService, "send_failure_email")

    service = EmailService()
    service.enabled = True
    service.smtp_ssl = True  # 该用例仅 mock SMTP_SSL
    service.smtp_password = "test-password"

    to_email = "user@example.com"
    job_id = "job-123"
    analysis_type = "Auto<Encoder>"

    # 构造超长错误信息：确保前 2000 字符可验证，2000 字符后的哨兵不会出现在正文中
    sentinel = "<SENTINEL_AFTER_2000>&"
    prefix_len = 2000 - len("<bad>\n")
    prefix = "<bad>\n" + ("A" * prefix_len)  # prefix 的长度严格为 2000
    error_message = prefix + sentinel + ("B" * 1000)

    truncated = error_message[:2000]
    expected_escaped = html.escape(truncated).replace("\n", "<br/>")
    sentinel_escaped = html.escape(sentinel)

    with patch("api.services.email_service.smtplib.SMTP_SSL") as mock_smtp_ssl:
        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        result = asyncio.run(
            service.send_failure_email(
                to_email=to_email,
                job_id=job_id,
                analysis_type=analysis_type,
                error_message=error_message,
            )
        )

        assert isinstance(result, bool)
        assert result is True
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

        sent_msg = mock_server.send_message.call_args[0][0]

        # 不应附带任何 zip attachment 部分
        for part in sent_msg.walk():
            if part.is_multipart():
                continue
            content_type = part.get_content_type()
            content_disp = (part.get("Content-Disposition") or "").lower()
            assert not (
                content_type == "application/zip"
                or ("attachment" in content_disp and "zip" in content_disp)
            )

        html_body = _extract_html_body(sent_msg)

        assert job_id in html_body
        assert html.escape(analysis_type) in html_body
        assert expected_escaped in html_body
        assert "<br/>" in html_body
        assert sentinel not in html_body
        assert sentinel_escaped not in html_body


def test_send_failure_email_catches_smtp_exception_and_returns_false() -> None:
    service = EmailService()
    service.enabled = True
    service.smtp_ssl = True
    service.smtp_password = "test-password"

    with patch("api.services.email_service.smtplib.SMTP_SSL") as mock_smtp_ssl:
        mock_smtp_ssl.side_effect = RuntimeError("smtp boom")
        result = asyncio.run(
            service.send_failure_email(
                to_email="user@example.com",
                job_id="job-err",
                analysis_type="FailCase",
                error_message="error text",
            )
        )

    assert isinstance(result, bool)
    assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

