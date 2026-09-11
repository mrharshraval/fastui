from app.infrastructure.email.provider import (
    BaseEmailProvider,
    EmailPayload,
    EmailResult,
    EmailService,
    EmailTag,
    MockEmailProvider,
    ResendEmailProvider,
    SMTPEmailProvider,
    email_service,
)
from app.infrastructure.email.templates import (
    get_otp_template,
    get_password_reset_template,
)

__all__ = [
    "BaseEmailProvider",
    "EmailPayload",
    "EmailResult",
    "EmailService",
    "EmailTag",
    "MockEmailProvider",
    "ResendEmailProvider",
    "SMTPEmailProvider",
    "email_service",
    "get_otp_template",
    "get_password_reset_template",
]
