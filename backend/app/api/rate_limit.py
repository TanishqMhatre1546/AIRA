"""In-memory sliding window rate limiter and daily model budget tracking.

Architecture Note:
The in-memory rate limiter and model-call budget tracker are stateful single-process
constructs designed for a single instance deployment. They maintain thread-safe
sliding windows and daily quotas without requiring external key-value stores.
"""

import math
import threading
import time
from datetime import UTC, date, datetime

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Extract client IP address safely behind reverse proxies such as Render.

    If X-Forwarded-For is present, the leftmost address is extracted as the client IP.
    Otherwise, the direct socket client host is returned.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
        if client_ip:
            return client_ip

    if request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter per client IP.

    Note: This rate limiter is designed for a single instance deployment.
    """

    def __init__(self, default_limit: int = 20, window_seconds: float = 60.0) -> None:
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check_rate_limit(
        self,
        client_ip: str,
        limit: int | None = None,
    ) -> tuple[bool, int]:
        """Check if request is within rate limit.

        Returns:
            A tuple of (is_allowed, retry_after_seconds).
        """
        max_requests = limit if limit is not None else self.default_limit
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            timestamps = self._requests.get(client_ip, [])
            # Purge expired timestamps
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= max_requests:
                oldest_ts = valid_timestamps[0]
                retry_after = max(1, int(math.ceil(oldest_ts + self.window_seconds - now)))
                self._requests[client_ip] = valid_timestamps
                return False, retry_after

            valid_timestamps.append(now)
            self._requests[client_ip] = valid_timestamps
            return True, 0

    def reset(self) -> None:
        """Clear all recorded request timestamps."""
        with self._lock:
            self._requests.clear()


class ModelCallBudget:
    """Thread-safe daily model invocation counter to protect API quota caps.

    When the daily cap is exceeded, downstream generation safely degrades
    to deterministic extractive summary mode.
    """

    def __init__(self, limit: int = 1000) -> None:
        self.limit = limit
        self._date: date = datetime.now(UTC).date()
        self._count: int = 0
        self._lock = threading.Lock()

    def _sync_date(self) -> None:
        today = datetime.now(UTC).date()
        if today != self._date:
            self._date = today
            self._count = 0

    def can_call(self) -> bool:
        """Check if daily model invocation budget has remaining quota."""
        with self._lock:
            self._sync_date()
            return self._count < self.limit

    def record_call(self) -> None:
        """Increment the daily model invocation counter."""
        with self._lock:
            self._sync_date()
            self._count += 1

    def get_count(self) -> int:
        """Get the current count of model invocations today."""
        with self._lock:
            self._sync_date()
            return self._count

    def reset(self, count: int = 0) -> None:
        """Reset the daily counter for testing or administrative purposes."""
        with self._lock:
            self._date = datetime.now(UTC).date()
            self._count = count
