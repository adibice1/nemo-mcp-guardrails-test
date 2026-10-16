"""Bound expensive management operations in the single-process API deployment."""

from collections import deque
from hashlib import sha256
from threading import Lock
from time import monotonic
import math

from fastapi import HTTPException, Request


class RateLimiter:
    """Keep bounded sliding windows; refuse new keys when active capacity is full."""

    def __init__(self, capacity: int = 10000, clock=monotonic):
        """Set the state bound and injectable monotonic clock."""
        self.capacity = capacity
        self.clock = clock
        self.buckets = {}
        self.lock = Lock()

    def check(self, key: str, limit: int, seconds: int) -> None:
        """Charge every attempt without retaining raw identity or request content."""
        key = sha256(key.encode()).digest()
        with self.lock:
            now = self.clock()
            if key not in self.buckets and len(self.buckets) >= self.capacity:
                self.buckets = {k: v for k, v in self.buckets.items() if v[0] > now}
                if len(self.buckets) >= self.capacity:
                    self._reject(seconds)
            _, attempts = self.buckets.get(key, (now, deque()))
            while attempts and attempts[0] <= now - seconds:
                attempts.popleft()
            if len(attempts) >= limit:
                self._reject(max(1, math.ceil(attempts[0] + seconds - now)))
            attempts.append(now)
            self.buckets[key] = (now + seconds, attempts)

    @staticmethod
    def _reject(seconds: int) -> None:
        """Return one generic, non-cacheable retry response."""
        raise HTTPException(429, "Too many attempts. Try again later.", headers={
            "Retry-After": str(seconds), "Cache-Control": "no-store",
        })


limiter = RateLimiter()


def limit_operation(request: Request, operation: str, subject: str, limit: int, seconds: int) -> None:
    """Use the transport peer, never untrusted forwarded headers, plus actor scope."""
    peer = request.client.host if request.client else "unknown"
    limiter.check(f"{operation}:peer:{peer}", max(60, limit), seconds)
    limiter.check(f"{operation}:subject:{subject}", limit, seconds)
