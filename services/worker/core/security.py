"""
FastUI Worker Security & Authentication
=======================================
Enforces application-level authentication for incoming HTTP requests to the Worker.
Uses constant-time token comparison without logging secrets.
"""

import secrets
from typing import Optional

from fastapi import Header, HTTPException, status
from core.config import settings


class WorkerTokenVerifier:
    """
    Class-based dependency for validating the X-Worker-Token request header.
    """

    def __init__(self, required_token: Optional[str] = None) -> None:
        self._configured_token = required_token

    @property
    def configured_token(self) -> Optional[str]:
        return self._configured_token or settings.WORKER_TOKEN

    async def __call__(
        self,
        x_worker_token: Optional[str] = Header(default=None, alias="X-Worker-Token"),
    ) -> bool:
        """
        Validates the incoming X-Worker-Token header against WORKER_TOKEN.
        Returns True on successful verification.
        Raises 401 Unauthorized if the header is missing, invalid, or worker token is unset.
        """
        expected_token = self.configured_token

        if not expected_token:
            # If the worker requires token authentication but no token was configured in env
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Worker authentication is not configured",
            )

        if not x_worker_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-Worker-Token authentication header",
            )

        # Constant-time comparison to prevent timing attacks
        is_valid = secrets.compare_digest(
            x_worker_token.encode("utf-8"),
            expected_token.encode("utf-8"),
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid X-Worker-Token authentication token",
            )

        return True


# Default reusable dependency instance
verify_worker_token = WorkerTokenVerifier()
