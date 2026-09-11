"""FastUI Email Provider Architecture.

- Resend Python SDK client integration (dispatched in worker threads)
- Asynchronous non-blocking dispatch
- Pydantic v2 payload validation
- Domain transactional methods (OTP, Password Reset)
"""

import asyncio
import logging
import os
import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from pydantic import BaseModel, EmailStr

from app.config.settings import settings
from app.infrastructure.email.templates import (
    get_otp_template,
    get_password_reset_template,
)

logger = logging.getLogger("fastui.email")


class EmailTag(BaseModel):
    name: str
    value: str


class EmailPayload(BaseModel):
    to: EmailStr | list[EmailStr]
    subject: str
    html: str
    text: str | None = None
    from_email: str | None = None
    from_name: str | None = None
    reply_to: str | None = None
    tags: list[EmailTag] | None = None
    headers: dict[str, str] | None = None


class EmailResult(BaseModel):
    success: bool
    message_id: str | None = None
    error: str | None = None
    provider: str


class BaseEmailProvider(ABC):
    @abstractmethod
    async def send(self, payload: EmailPayload) -> EmailResult:
        """Asynchronously send an email."""


class ResendEmailProvider(BaseEmailProvider):
    """Production-grade Resend provider using official Resend Python SDK.

    Dispatches within a threadpool worker to avoid blocking the event loop.
    """

    def __init__(self, api_key: str):
        import resend

        self.resend = resend
        self.api_key = api_key
        self.resend.api_key = api_key

    def _sync_send(self, payload: EmailPayload) -> EmailResult:
        self.resend.api_key = self.api_key

        from_name = payload.from_name or settings.EMAIL_FROM_NAME or "FastUI"
        from_email = payload.from_email or settings.EMAIL_FROM_ADDRESS or "onboarding@resend.dev"
        from_header = f"{from_name} <{from_email}>" if from_name else from_email

        recipients = [payload.to] if isinstance(payload.to, str) else list(payload.to)

        logger.info(
            f"[EMAIL:DISPATCH] Resend API call | Sender='{from_header}' | To={recipients} | "
            f"Subject='{payload.subject}'"
        )

        params: dict[str, Any] = {
            "from": from_header,
            "to": recipients,
            "subject": payload.subject,
            "html": payload.html,
        }

        if payload.text:
            params["text"] = payload.text
        if payload.reply_to or settings.EMAIL_REPLY_TO:
            params["reply_to"] = payload.reply_to or settings.EMAIL_REPLY_TO
        if payload.tags:
            params["tags"] = [t.model_dump() for t in payload.tags]
        if payload.headers:
            params["headers"] = payload.headers

        try:
            res = self.resend.Emails.send(params)
            msg_id = res.get("id") if isinstance(res, dict) else getattr(res, "id", str(res))
            logger.info(f"[EMAIL:SUCCESS] Delivered email to {recipients} (Resend ID: {msg_id})")
            return EmailResult(success=True, message_id=msg_id, provider="resend")
        except Exception as e:
            logger.error(
                f"[EMAIL:ERROR] Resend dispatch failed for {recipients}: {e}", exc_info=True
            )
            return EmailResult(success=False, error=str(e), provider="resend")

    async def send(self, payload: EmailPayload) -> EmailResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_send, payload)


class MockEmailProvider(BaseEmailProvider):
    """Local / Testing Mock Provider that logs payloads without external calls."""

    async def send(self, payload: EmailPayload) -> EmailResult:
        logger.info(
            f"[EMAIL:MOCK] Simulated email sent | To: {payload.to} | Subject: '{payload.subject}'"
        )
        return EmailResult(success=True, message_id="mock_msg_0000", provider="mock")


class SMTPEmailProvider(BaseEmailProvider):
    """Standard SMTP Provider for environments requiring direct mail transport."""

    def __init__(
        self,
        host: str | None,
        port: int,
        user: str | None,
        password: str | None,
        use_tls: bool = True,
    ):
        self.host = host or "localhost"
        self.port = port
        self.user = user
        self.password = password
        self.use_tls = use_tls

    def _sync_send(self, payload: EmailPayload) -> EmailResult:
        try:
            msg = MIMEMultipart()
            from_name = payload.from_name or settings.EMAIL_FROM_NAME
            from_email = payload.from_email or settings.EMAIL_FROM_ADDRESS
            msg["From"] = (
                f"{from_name} <{from_email}>" if from_name else (from_email or "fastui@local")
            )
            recipients = [payload.to] if isinstance(payload.to, str) else list(payload.to)
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = payload.subject
            if payload.reply_to or settings.EMAIL_REPLY_TO:
                msg["Reply-To"] = str(payload.reply_to or settings.EMAIL_REPLY_TO)

            if payload.html:
                msg.attach(MIMEText(payload.html, "html"))
            elif payload.text:
                msg.attach(MIMEText(payload.text, "plain"))

            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.send_message(msg)
            logger.info(f"[EMAIL:SUCCESS] SMTP delivered email to {recipients}")
            return EmailResult(success=True, message_id="smtp_sent", provider="smtp")
        except Exception as e:
            logger.error(f"[EMAIL:ERROR] SMTP dispatch error to {payload.to}: {e}", exc_info=True)
            return EmailResult(success=False, error=str(e), provider="smtp")

    async def send(self, payload: EmailPayload) -> EmailResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_send, payload)


class EmailService:
    """Central email service managing provider resolution and domain transactional workflows."""

    def get_provider(self) -> BaseEmailProvider:
        provider_name = settings.EMAIL_PROVIDER.lower() if settings.EMAIL_PROVIDER else ""
        resend_key = (
            settings.RESEND_API_KEY
            or settings.EMAIL_API_KEY
            or os.getenv("RESEND_API_KEY")
            or os.getenv("EMAIL_API_KEY")
        )

        if provider_name == "smtp":
            return SMTPEmailProvider(
                host=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                user=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS,
            )
        elif resend_key:
            return ResendEmailProvider(api_key=resend_key)
        elif provider_name == "resend":
            logger.warning("EMAIL_PROVIDER is 'resend' but RESEND_API_KEY is not set. Using Mock.")
            return MockEmailProvider()

        return MockEmailProvider()

    async def send_email(self, payload: EmailPayload) -> EmailResult:
        provider = self.get_provider()
        return await provider.send(payload)

    async def send_verification_otp(
        self,
        to_email: str,
        otp_code: str,
        verify_url: str | None = None,
    ) -> EmailResult:
        """Sends the 6-digit email verification OTP."""
        payload = EmailPayload(
            to=to_email,
            subject="Your fastui Verification Code",
            html=get_otp_template(otp_code, verify_url=verify_url, email=to_email),
            text=f"Your fastui verification code is: {otp_code}. Valid for 10 minutes.",
            tags=[
                EmailTag(name="category", value="authentication"),
                EmailTag(name="type", value="otp_verification"),
            ],
        )
        return await self.send_email(payload)

    async def send_password_reset(
        self,
        to_email: str,
        reset_link: str,
    ) -> EmailResult:
        """Sends the password reset email with secure action link."""
        payload = EmailPayload(
            to=to_email,
            subject="Reset your fastui password",
            html=get_password_reset_template(reset_link),
            text=f"Reset your fastui password by clicking: {reset_link}",
            tags=[
                EmailTag(name="category", value="authentication"),
                EmailTag(name="type", value="password_reset"),
            ],
        )
        return await self.send_email(payload)


email_service = EmailService()
