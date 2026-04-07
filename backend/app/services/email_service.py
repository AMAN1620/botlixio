"""
Botlixio — Email service via SMTP (smtplib).

Sends transactional emails: verification and password reset.
"""

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings


class EmailService:
    """Send transactional emails via SMTP."""

    def __init__(self) -> None:
        settings = get_settings()
        self._host = settings.SMTP_HOST
        self._port = settings.SMTP_PORT
        self._user = settings.SMTP_USER
        self._password = settings.SMTP_PASSWORD
        self._from_email = settings.EMAIL_FROM or settings.SMTP_USER
        self._frontend_url = settings.FRONTEND_URL

    def _send(self, *, to_email: str, subject: str, html: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._from_email
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(self._host, self._port) as server:
            server.ehlo()
            server.starttls()
            server.login(self._user, self._password)
            server.sendmail(self._from_email, to_email, msg.as_string())

    async def send_verification_email(
        self, *, to_email: str, token: str, full_name: str
    ) -> None:
        link = f"{self._frontend_url}/verify-email?token={token}"
        html = (
            f"<p>Hi {full_name},</p>"
            f"<p>Please verify your email by clicking the link below:</p>"
            f'<p><a href="{link}">{link}</a></p>'
            f"<p>This link expires in 24 hours.</p>"
        )
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._send(to_email=to_email, subject="Verify your Botlixio email", html=html)
        )

    async def send_password_reset_email(
        self, *, to_email: str, token: str, full_name: str
    ) -> None:
        link = f"{self._frontend_url}/reset-password?token={token}"
        html = (
            f"<p>Hi {full_name},</p>"
            f"<p>You requested a password reset. Click the link below:</p>"
            f'<p><a href="{link}">{link}</a></p>'
            f"<p>This link expires in 1 hour.</p>"
        )
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._send(to_email=to_email, subject="Reset your Botlixio password", html=html)
        )
