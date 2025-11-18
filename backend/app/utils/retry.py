import asyncio
import logging
from typing import Callable, Any, Optional, List
from functools import wraps

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts fail"""
    pass


async def async_retry(
    func: Callable,
    max_retries: int = 3,
    delays: Optional[List[int]] = None,
    exceptions: tuple = (Exception,),
) -> Any:
    """
    Retry an async function with exponential backoff

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        delays: List of delays in seconds between retries
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Result of the function call

    Raises:
        RetryError: If all retries fail
    """
    if delays is None:
        delays = [2, 4, 8]

    last_exception = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}")
            result = await func()
            return result
        except exceptions as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")

            if attempt < max_retries - 1:
                delay = delays[min(attempt, len(delays) - 1)]
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries} attempts failed")

    raise RetryError(f"Failed after {max_retries} attempts: {str(last_exception)}")


def retry_on_failure(max_retries: int = 3, delays: Optional[List[int]] = None):
    """
    Decorator for automatic retry with exponential backoff

    Usage:
        @retry_on_failure(max_retries=3, delays=[2, 4, 8])
        async def my_function():
            # Your code here
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async def _func():
                return await func(*args, **kwargs)
            return await async_retry(_func, max_retries, delays)
        return wrapper
    return decorator
