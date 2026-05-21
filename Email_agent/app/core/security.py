import re
import time
import html
from collections import defaultdict
from typing import Tuple

from fastapi import Request, HTTPException

_rate_limit_storage = defaultdict(list)
_rate_limit_cleanup_interval = 300
_last_cleanup = time.time()


def sanitize_input(text: str, max_length: int = 10000) -> str:
    if not isinstance(text, str):
        return ""
    if len(text) > max_length:
        text = text[:max_length]
    text = text.replace('\x00', '')
    text = html.escape(text)
    return text.strip()


def validate_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


def sanitize_sql_input(text: str) -> str:
    if not isinstance(text, str):
        return ""
    dangerous_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"('|;|\\)",
    ]
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return text.strip()


def check_rate_limit(identifier: str, max_requests: int, window: int) -> Tuple[bool, dict]:
    global _last_cleanup
    current_time = time.time()
    if current_time - _last_cleanup > _rate_limit_cleanup_interval:
        _cleanup_rate_limits(window)
        _last_cleanup = current_time
    now = time.time()
    requests_list = _rate_limit_storage[identifier]
    requests_list[:] = [t for t in requests_list if now - t < window]
    if len(requests_list) >= max_requests:
        retry_after = int(window - (now - requests_list[0]) if requests_list else window)
        return False, {
            'error': 'Rate limit exceeded',
            'message': f'Maximum {max_requests} requests per {window} seconds allowed',
            'retry_after': retry_after
        }
    requests_list.append(now)
    return True, {}


def rate_limit_check(request: Request, max_requests: int = 60, window: int = 60):
    identifier = request.client.host
    allowed, error = check_rate_limit(identifier, max_requests, window)
    if not allowed:
        raise HTTPException(status_code=429, detail=error)


def _cleanup_rate_limits(window: int):
    now = time.time()
    for identifier in list(_rate_limit_storage.keys()):
        requests_list = _rate_limit_storage[identifier]
        requests_list[:] = [t for t in requests_list if now - t < window]
        if not requests_list:
            del _rate_limit_storage[identifier]
