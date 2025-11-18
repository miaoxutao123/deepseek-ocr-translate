import asyncio
import time
import logging
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, max_requests: int, time_window: int):
        """
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait until a request can be made"""
        async with self._lock:
            now = time.time()

            # Remove old requests outside the time window
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()

            # If at capacity, wait
            if len(self.requests) >= self.max_requests:
                sleep_time = self.requests[0] + self.time_window - now
                if sleep_time > 0:
                    logger.warning(f"速率限制：已达到 {self.max_requests} 请求/{self.time_window}秒 的限制")
                    logger.warning(f"等待 {sleep_time:.1f} 秒后继续...")
                    await asyncio.sleep(sleep_time)
                    return await self.acquire()

            # Add current request
            self.requests.append(now)


class ConcurrencyLimiter:
    """Semaphore-based concurrency limiter"""

    def __init__(self, max_concurrent: int):
        """
        Args:
            max_concurrent: Maximum number of concurrent operations
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def __aenter__(self):
        await self.semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.semaphore.release()


class APILimiter:
    """Combined rate and concurrency limiter for API calls"""

    def __init__(
        self,
        max_requests_per_minute: int = 20,
        max_concurrent: int = 3
    ):
        """
        Args:
            max_requests_per_minute: Maximum requests per minute
            max_concurrent: Maximum concurrent requests
        """
        self.rate_limiter = RateLimiter(max_requests_per_minute, 60)
        self.concurrency_limiter = ConcurrencyLimiter(max_concurrent)

    async def __aenter__(self):
        await self.rate_limiter.acquire()
        await self.concurrency_limiter.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.concurrency_limiter.__aexit__(exc_type, exc_val, exc_tb)


# Global limiters (can be configured per user in production)
# 根据硅基流动 L0 限制: RPM 1,000, TPM 80,000
# 保守设置为 60 RPM，避免触发限制
ocr_limiter = APILimiter(max_requests_per_minute=60, max_concurrent=5)
translate_limiter = APILimiter(max_requests_per_minute=60, max_concurrent=5)
embedding_limiter = APILimiter(max_requests_per_minute=100, max_concurrent=10)
