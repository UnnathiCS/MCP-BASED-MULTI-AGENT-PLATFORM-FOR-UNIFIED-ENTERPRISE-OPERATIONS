"""
Security utilities for input validation, sanitization, and rate limiting.
"""

import re
import time
from functools import wraps
from flask import request, jsonify
from collections import defaultdict
import html

# Rate limiting storage (in production, use Redis)
_rate_limit_storage = defaultdict(list)
_rate_limit_cleanup_interval = 300  # Clean up every 5 minutes
_last_cleanup = time.time()

def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # HTML escape to prevent XSS
    text = html.escape(text)
    
    return text.strip()

def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_message_id(message_id: str) -> bool:
    """
    Validate email message ID format.
    
    Args:
        message_id: Message ID to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not message_id or not isinstance(message_id, str):
        return False
    
    # Message IDs typically look like: <something@domain.com>
    pattern = r'^<[^<>]+>$'
    return bool(re.match(pattern, message_id))

def sanitize_sql_input(text: str) -> str:
    """
    Sanitize input for SQL queries (parameterized queries are still preferred).
    
    Args:
        text: Input text to sanitize
    
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Remove SQL injection patterns
    dangerous_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"('|;|\\)",
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()

def rate_limit(max_requests: int = 60, window: int = 60, per_ip: bool = True):
    """
    Rate limiting decorator for Flask routes.
    
    Args:
        max_requests: Maximum number of requests allowed
        window: Time window in seconds
        per_ip: If True, rate limit per IP; if False, global
    
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            global _last_cleanup
            
            # Clean up old entries periodically
            current_time = time.time()
            if current_time - _last_cleanup > _rate_limit_cleanup_interval:
                _cleanup_rate_limits(window)
                _last_cleanup = current_time
            
            # Get identifier (IP address or 'global')
            identifier = request.remote_addr if per_ip else 'global'
            
            # Check rate limit
            now = time.time()
            requests = _rate_limit_storage[identifier]
            
            # Remove old requests outside the window
            requests[:] = [req_time for req_time in requests if now - req_time < window]
            
            # Check if limit exceeded
            if len(requests) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_requests} requests per {window} seconds allowed',
                    'retry_after': int(window - (now - requests[0]) if requests else window)
                }), 429
            
            # Add current request
            requests.append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def _cleanup_rate_limits(window: int):
    """Clean up old rate limit entries."""
    now = time.time()
    for identifier in list(_rate_limit_storage.keys()):
        requests = _rate_limit_storage[identifier]
        requests[:] = [req_time for req_time in requests if now - req_time < window]
        if not requests:
            del _rate_limit_storage[identifier]

def validate_json_input(data: dict, required_fields: list = None, field_types: dict = None) -> tuple[bool, str]:
    """
    Validate JSON input data.
    
    Args:
        data: JSON data to validate
        required_fields: List of required field names
        field_types: Dict mapping field names to expected types
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Invalid input: expected JSON object"
    
    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
    
    # Check field types
    if field_types:
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                return False, f"Invalid type for field '{field}': expected {expected_type.__name__}"
    
    return True, ""

