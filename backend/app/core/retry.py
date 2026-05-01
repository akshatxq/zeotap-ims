"""
Exponential backoff retry logic for database operations
"""

import asyncio
import logging
from functools import wraps
from typing import Callable, Any, TypeVar, Optional

T = TypeVar('T')
logger = logging.getLogger(__name__)

async def retry_with_backoff(
    func: Callable[..., Any],
    max_attempts: int = 3,
    base_delay: float = 0.5,
    *args,
    **kwargs
) -> Any:
    """
    Execute a function with exponential backoff retry
    
    Args:
        func: Async function to execute
        max_attempts: Maximum number of attempts (default 3)
        base_delay: Initial delay in seconds (default 0.5)
        *args, **kwargs: Arguments to pass to the function
    
    Returns:
        Result of the function call
    
    Raises:
        The last exception encountered after all attempts fail
    """
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            result = await func(*args, **kwargs)
            if attempt > 1:
                logger.info(f"✅ Retry successful on attempt {attempt} for {func.__name__}")
            return result
        except Exception as e:
            last_exception = e
            if attempt == max_attempts:
                logger.error(f"❌ All {max_attempts} attempts failed for {func.__name__}: {e}")
                raise
            
            # Calculate delay with exponential backoff: 0.5, 1.0, 2.0 seconds
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                f"⚠️ Attempt {attempt}/{max_attempts} failed for {func.__name__}: {str(e)[:100]}. "
                f"Retrying in {delay}s..."
            )
            await asyncio.sleep(delay)
    
    raise last_exception

def retry_decorator(max_attempts: int = 3, base_delay: float = 0.5):
    """
    Decorator version for retry logic
    
    Usage:
        @retry_decorator(max_attempts=3, base_delay=0.5)
        async def my_db_call():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(func, max_attempts, base_delay, *args, **kwargs)
        return wrapper
    return decorator