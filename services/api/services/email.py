"""
Backward compatibility re-export module for services.email
"""
from services.email_service import (
    EmailMessage,
    EmailProvider,
    MockEmailProvider,
    get_email_provider,
    send_sales_email
)
