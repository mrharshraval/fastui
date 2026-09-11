"""FastUI API Entry Point Delegator.

Delegates execution to the modern canonical application assembly in app.main.
"""

from app.main import app

__all__ = ["app"]
