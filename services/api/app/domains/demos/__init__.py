"""FastUI Demos Domain."""

from app.domains.demos.models import DemoEvent, ProspectDemo
from app.domains.demos.service import DemoService, is_bot

__all__ = ["DemoEvent", "DemoService", "ProspectDemo", "is_bot"]
