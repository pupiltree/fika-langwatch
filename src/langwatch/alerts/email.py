"""
Email alert channel using SMTP.
Sends beautifully formatted HTML emails for API key failures.
"""

import logging
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .base import AlertChannel, AlertPayload

logger = logging.getLogger(__name__)


class EmailAlert(AlertChannel):
    """
    Email alert channel using SMTP (supports Gmail, SendGrid, etc.)

    Usage:
        alert = EmailAlert(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="alerts@company.com",
            password="app-password",  # Use Gmail App Password
            to=["ops@company.com"],
        )
    """

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        to: List[str],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        from_name: Optional[str] = "LangWatch Alerts",
        use_tls: bool = True,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.to = to
        self.cc = cc or []
        self.bcc = bcc or []
        self.from_name = from_name
        self.use_tls = use_tls

    @property
    def name(self) -> str:
        return "email"

    async def send_async(self, payload: AlertPayload) -> bool:
        """Send email alert asynchronously."""
        try:
            import aiosmtplib
        except ImportError:
            logger.error("aiosmtplib not installed. Install with: pip install langwatch[email]")
            return False

        try:
            html_body = self._build_html(payload)

            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.username}>"
            message["To"] = ", ".join(self.to)
            message["Subject"] = self._build_subject(payload)

            if self.cc:
                message["Cc"] = ", ".join(self.cc)

            html_part = MIMEText(html_body, "html")
            message.attach(html_part)

            await aiosmtplib.send(
                message,
                hostname=self.smtp_server,
                port=self.smtp_port,
                start_tls=self.use_tls,
                username=self.username,
                password=self.password,
            )

            logger.info(f"Email alert sent to {len(self.to)} recipient(s)")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False

    def _build_subject(self, payload: AlertPayload) -> str:
        severity_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}
        emoji = severity_emoji.get(payload.severity.lower(), "🔔")
        return f"{emoji} {payload.title}"

    def _build_html(self, payload: AlertPayload) -> str:
        from ..templates.email_templates import EmailTemplates
        return EmailTemplates.build_alert_email(payload)
