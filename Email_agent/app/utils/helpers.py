import time
import logging

logger = logging.getLogger(__name__)


def retry_function(func, max_retries=3, initial_delay=1.0, backoff_factor=2.0, **kwargs):
    last_exception = None
    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            return func(**kwargs) if kwargs else func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt+1}/{max_retries+1} failed for {func.__name__}: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_retries+1} attempts failed for {func.__name__}: {e}")
    raise last_exception
