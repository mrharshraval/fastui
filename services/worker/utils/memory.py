"""
FastUI Worker Memory Tracker
============================
Instruments process RSS memory, child Chromium browser processes,
and enforces safety thresholds before reaching container memory limits.
"""

import gc
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger("fastui.worker.memory")

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False
    logger.warning("psutil not available; memory tracking will use fallback estimation.")


class MemoryTracker:
    """
    Monitors process and child subprocess Resident Set Size (RSS).
    Logs structured memory metrics and provides safety cutoff checks.
    """

    DEFAULT_SAFETY_LIMIT_MB = 800.0  # Safe threshold below Cloud Run 1024 MB / 2048 MB limit

    def __init__(self, safety_limit_mb: float = DEFAULT_SAFETY_LIMIT_MB) -> None:
        self.safety_limit_mb = safety_limit_mb
        self.peak_rss_mb: float = 0.0
        self._update_peak()

    def get_process_rss_mb(self) -> float:
        """Returns the current Python process RSS in Megabytes."""
        if not _PSUTIL_AVAILABLE:
            return 0.0
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024.0 * 1024.0)
        except Exception:
            return 0.0

    def get_total_rss_mb(self) -> float:
        """
        Returns total RSS including Python process and all child processes (Chromium).
        """
        if not _PSUTIL_AVAILABLE:
            return 0.0
        try:
            parent = psutil.Process(os.getpid())
            total_bytes = parent.memory_info().rss
            for child in parent.children(recursive=True):
                try:
                    total_bytes += child.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            total_mb = total_bytes / (1024.0 * 1024.0)
            if total_mb > self.peak_rss_mb:
                self.peak_rss_mb = total_mb
            return total_mb
        except Exception:
            return 0.0

    def _update_peak(self) -> float:
        rss = self.get_total_rss_mb()
        if rss > self.peak_rss_mb:
            self.peak_rss_mb = rss
        return rss

    def is_memory_safe(self) -> bool:
        """Returns False if total RSS approaches the safety threshold."""
        current_rss = self.get_total_rss_mb()
        if current_rss >= self.safety_limit_mb:
            logger.warning(
                f"MEMORY SAFETY WARNING: Total RSS {current_rss:.1f} MB exceeds "
                f"safety limit of {self.safety_limit_mb:.1f} MB. Graceful cutoff advised."
            )
            return False
        return True

    def log_stage(
        self,
        stage: str,
        source: Optional[str] = None,
        batch: Optional[int] = None,
        new_count: Optional[int] = None,
        active_contexts: Optional[int] = None,
        active_pages: Optional[int] = None,
        extra: Optional[Dict[str, str]] = None,
    ) -> float:
        """
        Logs structured memory instrumentation.
        Never logs sensitive business data, credentials, or URLs.
        """
        current_rss = self.get_total_rss_mb()
        parts: List[str] = [f"MEMORY {stage} rss_mb={current_rss:.2f}"]

        if source:
            parts.append(f"source={source}")
        if batch is not None:
            parts.append(f"batch={batch}")
        if new_count is not None:
            parts.append(f"new={new_count}")
        if active_contexts is not None:
            parts.append(f"contexts={active_contexts}")
        if active_pages is not None:
            parts.append(f"pages={active_pages}")
        if extra:
            for k, v in extra.items():
                parts.append(f"{k}={v}")

        parts.append(f"peak_rss_mb={self.peak_rss_mb:.2f}")
        msg = " ".join(parts)
        logger.info(msg)
        return current_rss

    @staticmethod
    def force_garbage_collection() -> None:
        """Forces immediate garbage collection and releases Python memory buffers."""
        gc.collect()


# Global default tracker instance
memory_tracker = MemoryTracker()
