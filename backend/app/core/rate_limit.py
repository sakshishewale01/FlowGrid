"""Small in-process request limiter for sensitive endpoints."""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from typing import Deque, Dict

from fastapi import HTTPException, Request, status

from app.core.config import settings


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> int:
        now = monotonic()
        window_start = now - settings.auth_rate_limit_window_seconds
        with self._lock:
            timestamps = self._requests[key]
            while timestamps and timestamps[0] <= window_start:
                timestamps.popleft()
            if len(timestamps) >= settings.auth_rate_limit_requests:
                retry_after = max(
                    1,
                    int(timestamps[0] + settings.auth_rate_limit_window_seconds - now),
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many authentication attempts. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )
            timestamps.append(now)
        return len(timestamps)

    def clear(self) -> None:
        with self._lock:
            self._requests.clear()


auth_rate_limiter = InMemoryRateLimiter()


def rate_limit_authentication(request: Request, identity: str) -> None:
    """Record a failed authentication attempt and reject excessive retries."""
    client_host = request.client.host if request.client else "unknown"
    auth_key = f"{request.url.path}:{client_host}:{identity.lower().strip()}"
    auth_rate_limiter.check(auth_key)
