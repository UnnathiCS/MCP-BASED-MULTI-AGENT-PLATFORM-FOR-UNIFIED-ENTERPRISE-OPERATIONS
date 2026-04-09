"""
Retry logic utilities for handling transient failures.
"""

import time
import logging

logger = logging.getLogger(__name__)


def retry_function(func, max_retries=3, initial_delay=1.0, backoff_factor=2.0, **kwargs):
    """
    Retry a function call with exponential backoff.

    Args:
        func: The function to call
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        **kwargs: Arguments to pass to the function

    Returns:
        The result of the function call

    Raises:
        The last exception if all retries fail
    """
    last_exception = None
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            return func(**kwargs) if kwargs else func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")

    raise last_exception
