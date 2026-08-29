"""
FastAPI Email Service Architecture (Global Standards)
- Resend Python SDK official client integration
- Asynchronous non-blocking dispatch with FastAPI BackgroundTasks
- Pydantic v2 payload validation
- Domain transactional methods (OTP, Password Reset)
- Detailed telemetry logging & error handling
"""

import asyncio
import logging
import os
import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Union

from fastapi import BackgroundTasks
from pydantic import BaseModel, EmailStr, Field

from core.config import settings
from services.email_templates import get_otp_template, get_password_reset_template

logger = logging.getLogger("fastui.email")


# ============================================================================
# Schemas & DTOs
# ============================================================================

class EmailTag(BaseModel):
    name: str
    value: str


class EmailPayload(BaseModel):
    to: Union[EmailStr, List[EmailStr]]
    subject: str
    html: str
    text: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    tags: Optional[List[EmailTag]] = None
    headers: Optional[Dict[str, str]] = None


class EmailResult(BaseModel):
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    provider: str


# Legacy compatibility alias
class EmailMessage(BaseModel):
    to_email: str
    subject: str
    body: str
    html_body: Optional[str] = None
    from_name: Optional[str] = None
    from_email: Optional[str] = None
    reply_to: Optional[str] = None
    variables: Optional[Dict[str, str]] = None


# ============================================================================
# Providers (Protocol / Abstract Class)
# ============================================================================

class BaseEmailProvider(ABC):
    @abstractmethod
    async def send(self, payload: EmailPayload) -> EmailResult:
        """Asynchronously send an email."""
        pass


class ResendEmailProvider(BaseEmailProvider):
    """
    Production-grade Resend provider using the official Resend Python SDK.
    Dispatches within a threadpool worker to avoid blocking the event loop.
    """

    def __init__(self, api_key: str):
        import resend
        self.resend = resend
        self.api_key = api_key
        self.resend.api_key = api_key

    def _sync_send(self, payload: EmailPayload) -> EmailResult:
        self.resend.api_key = self.api_key
        
        # Build standard From header (e.g., "fastui <team@yourdomain.com>")
        from_name = payload.from_name or settings.EMAIL_FROM_NAME or "FastUI"
        from_email = payload.from_email or settings.EMAIL_FROM_ADDRESS or "onboarding@resend.dev"
        from_header = f"{from_name} <{from_email}>" if from_name else from_email
        
        recipients = [payload.to] if isinstance(payload.to, str) else list(payload.to)
        
        logger.info(f"[EMAIL:DISPATCH] Starting Resend API call | Sender='{from_header}' | To={recipients} | Subject='{payload.subject}'")
        
        params: Dict[str, Any] = {
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
            logger.debug(f"[EMAIL:TAGS] Attached metadata tags: {params['tags']}")
        if payload.headers:
            params["headers"] = payload.headers

        try:
            logger.info(f"[EMAIL:API_REQ] Sending payload to Resend REST endpoint...")
            res = self.resend.Emails.send(params)
            msg_id = res.get("id") if isinstance(res, dict) else getattr(res, "id", str(res))
            logger.info(f"[EMAIL:SUCCESS] ✅ Resend delivered email to {recipients} successfully! (Resend ID: {msg_id})")
            return EmailResult(success=True, message_id=msg_id, provider="resend")
        except Exception as e:
            logger.error(f"[EMAIL:ERROR] ❌ Resend dispatch failed for recipient(s) {recipients}: {e}", exc_info=True)
            return EmailResult(success=False, error=str(e), provider="resend")

    async def send(self, payload: EmailPayload) -> EmailResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_send, payload)


class MockEmailProvider(BaseEmailProvider):
    """Local / Testing Mock Provider that logs payloads without external calls."""
    async def send(self, payload: EmailPayload) -> EmailResult:
        logger.info(f"[EMAIL:MOCK] Simulated email sent | To: {payload.to} | Subject: '{payload.subject}'")
        return EmailResult(success=True, message_id="mock_msg_0000", provider="mock")


class SMTPEmailProvider(BaseEmailProvider):
    """Standard SMTP Provider for environments requiring direct mail transport."""
    def __init__(self, host: str, port: int, user: Optional[str], password: Optional[str], use_tls: bool = True):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.use_tls = use_tls

    def _sync_send(self, payload: EmailPayload) -> EmailResult:
        try:
            msg = MIMEMultipart()
            from_name = payload.from_name or settings.EMAIL_FROM_NAME
            from_email = payload.from_email or settings.EMAIL_FROM_ADDRESS
            msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
            recipients = [payload.to] if isinstance(payload.to, str) else list(payload.to)
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = payload.subject
            if payload.reply_to or settings.EMAIL_REPLY_TO:
                msg["Reply-To"] = payload.reply_to or settings.EMAIL_REPLY_TO
                
            if payload.html:
                msg.attach(MIMEText(payload.html, "html"))
            elif payload.text:
                msg.attach(MIMEText(payload.text, "plain"))

            logger.info(f"[EMAIL:SMTP] Connecting to SMTP server {self.host}:{self.port}...")
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.send_message(msg)
            logger.info(f"[EMAIL:SUCCESS] ✅ SMTP delivered email to {recipients}")
            return EmailResult(success=True, message_id="smtp_sent", provider="smtp")
        except Exception as e:
            logger.error(f"[EMAIL:ERROR] ❌ SMTP dispatch error to {payload.to}: {e}", exc_info=True)
            return EmailResult(success=False, error=str(e), provider="smtp")

    async def send(self, payload: EmailPayload) -> EmailResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_send, payload)


# ============================================================================
# High-Level Email Service
# ============================================================================

class EmailService:
    """
    Central email service managing provider resolution and domain transactional workflows.
    """

    def get_provider(self) -> BaseEmailProvider:
        provider_name = settings.EMAIL_PROVIDER.lower()
        resend_key = (
            settings.RESEND_API_KEY 
            or settings.EMAIL_API_KEY 
            or os.getenv("RESEND_API_KEY") 
            or os.getenv("EMAIL_API_KEY")
        )

        if provider_name == "resend":
            if not resend_key:
                logger.warning("[EMAIL:CONFIG] ⚠️ EMAIL_PROVIDER is 'resend' but RESEND_API_KEY / EMAIL_API_KEY is not set. Falling back to Mock.")
                return MockEmailProvider()
            return ResendEmailProvider(api_key=resend_key)
        elif provider_name == "smtp":
            return SMTPEmailProvider(
                host=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                user=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS
            )
        return MockEmailProvider()

    async def _execute_background_send(self, payload: EmailPayload):
        """Worker task executed in FastAPI BackgroundTasks."""
        logger.info(f"[EMAIL:BACKGROUND_TASK] 🚀 Starting background dispatch for {payload.to}")
        provider = self.get_provider()
        await provider.send(payload)

    async def send_email(
        self,
        payload: EmailPayload,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> EmailResult:
        """
        Dispatches email. If background_tasks is supplied, adds to queue for non-blocking API response.
        """
        provider = self.get_provider()
        logger.info(f"[EMAIL:REQUEST] Target='{payload.to}' | Subject='{payload.subject}' | Provider='{provider.__class__.__name__}'")
        
        if background_tasks is not None:
            # Add to FastAPI background tasks (returns immediately to client)
            background_tasks.add_task(self._execute_background_send, payload)
            logger.info(f"[EMAIL:QUEUED] ⏳ Added to FastAPI BackgroundTasks for non-blocking response to client.")
            return EmailResult(success=True, message_id="queued_background_task", provider=settings.EMAIL_PROVIDER)
        
        # Direct async send
        return await provider.send(payload)

    async def send_verification_otp(
        self,
        to_email: str,
        otp_code: str,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> EmailResult:
        """Sends the 6-digit email verification OTP."""
        logger.info(f"[EMAIL:OTP] Preparing verification OTP email for recipient: {to_email}")
        payload = EmailPayload(
            to=to_email,
            subject="Your fastui Verification Code",
            html=get_otp_template(otp_code),
            text=f"Your fastui verification code is: {otp_code}. Valid for 10 minutes.",
            tags=[
                EmailTag(name="category", value="authentication"),
                EmailTag(name="type", value="otp_verification")
            ]
        )
        return await self.send_email(payload, background_tasks=background_tasks)

    async def send_password_reset(
        self,
        to_email: str,
        reset_link: str,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> EmailResult:
        """Sends the password reset email with secure action link."""
        logger.info(f"[EMAIL:RESET] Preparing password reset email for recipient: {to_email}")
        payload = EmailPayload(
            to=to_email,
            subject="Reset your fastui password",
            html=get_password_reset_template(reset_link),
            text=f"Reset your fastui password by clicking: {reset_link}",
            tags=[
                EmailTag(name="category", value="authentication"),
                EmailTag(name="type", value="password_reset")
            ]
        )
        return await self.send_email(payload, background_tasks=background_tasks)


# Global singleton instance
email_service = EmailService()


# Backward compatibility wrapper for legacy callers
def get_email_provider() -> BaseEmailProvider:
    return email_service.get_provider()


async def send_sales_email(message: EmailMessage, background_tasks: Optional[BackgroundTasks] = None) -> bool:
    payload = EmailPayload(
        to=message.to_email,
        subject=message.subject,
        html=message.html_body or message.body,
        text=message.body,
        from_email=message.from_email,
        from_name=message.from_name,
        reply_to=message.reply_to
    )
    result = await email_service.send_email(payload, background_tasks=background_tasks)
    return result.success
