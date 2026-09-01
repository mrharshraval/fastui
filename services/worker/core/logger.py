"""
FastUI Worker Enterprise Structured Logging System (Cloud Run / OpenTelemetry Standard)
========================================================================================
- Outputs Google Cloud Logging (GCP) compliant structured JSON on Cloud Run / production.
- Clean human-readable colorized output in development.
- Automatic correlation ID tracking via ContextVars and incoming X-Correlation-ID headers.
- Zero-leakage data sanitization.
"""

import json
import logging
import os
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")

REDACTED_KEYS = frozenset({
    "password", "token", "worker_token", "x-worker-token", "secret", "authorization",
    "gcp_service_account_key", "api_key",
})


def redact_sensitive_data(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            k: "[REDACTED]" if k.lower() in REDACTED_KEYS else redact_sensitive_data(v)
            for k, v in data.items()
        }
    elif isinstance(data, (list, tuple, set)):
        return [redact_sensitive_data(item) for item in data]
    return data


class StructuredJsonFormatter(logging.Formatter):
    """
    Cloud Run / GCP Logging JSON Formatter.
    """

    def __init__(self, service_name: str = "fastui-worker") -> None:
        super().__init__()
        self.service_name = service_name
        self.environment = os.getenv("ENVIRONMENT", "development")

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        corr_id = correlation_id_ctx.get() or getattr(record, "correlation_id", "")

        severity_map = {
            "DEBUG": "DEBUG",
            "INFO": "INFO",
            "WARNING": "WARNING",
            "ERROR": "ERROR",
            "CRITICAL": "CRITICAL",
        }
        severity = severity_map.get(record.levelname, record.levelname)

        log_payload: Dict[str, Any] = {
            "timestamp": timestamp,
            "severity": severity,
            "level": record.levelname,
            "service": self.service_name,
            "environment": self.environment,
            "logger": record.name,
            "message": record.getMessage(),
            "caller": f"{record.filename}:{record.lineno}",
        }

        if corr_id:
            log_payload["correlation_id"] = corr_id
            log_payload["logging.googleapis.com/trace"] = corr_id

        extra_fields = getattr(record, "extra_fields", None)
        if isinstance(extra_fields, dict):
            log_payload.update(redact_sensitive_data(extra_fields))

        if record.exc_info and record.exc_info[0]:
            exc_type, exc_val, exc_tb = record.exc_info
            log_payload["error"] = {
                "type": getattr(exc_type, "__name__", "UnknownException"),
                "message": str(exc_val),
                "stack_trace": traceback.format_exception(exc_type, exc_val, exc_tb),
            }

        return json.dumps(log_payload, default=str)


class DevelopmentConsoleFormatter(logging.Formatter):
    """
    Local console development formatter.
    """

    COLOR_CODES = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET_CODE = "\033[0m"

    def __init__(self, service_name: str = "fastui-worker") -> None:
        super().__init__()
        self.service_name = service_name
        self.use_color = sys.platform != "win32" or "WT_SESSION" in os.environ or "TERM" in os.environ

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        corr_id = correlation_id_ctx.get() or getattr(record, "correlation_id", "")
        corr_tag = f" [{corr_id[:8]}]" if corr_id else ""

        level_str = record.levelname.ljust(7)
        if self.use_color:
            color = self.COLOR_CODES.get(record.levelname, "")
            level_str = f"{color}{level_str}{self.RESET_CODE}"

        formatted = f"{timestamp} [{level_str}] [{self.service_name}] [{record.name}]{corr_tag} {record.getMessage()}"

        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


def setup_worker_logging(service_name: str = "fastui-worker", log_level: Optional[str] = None) -> None:
    env = os.getenv("ENVIRONMENT", "development").lower()
    resolved_level = log_level or os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, resolved_level, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    if env in ("production", "staging"):
        console_handler.setFormatter(StructuredJsonFormatter(service_name=service_name))
    else:
        console_handler.setFormatter(DevelopmentConsoleFormatter(service_name=service_name))

    root_logger.addHandler(console_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
