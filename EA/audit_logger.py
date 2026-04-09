"""
Audit logging system for tracking all system actions.
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audit.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('audit')

AUDIT_DB_PATH = "audit.db"

def init_audit_db():
    """Initialize audit database."""
    conn = sqlite3.connect(AUDIT_DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            user_id TEXT,
            ip_address TEXT,
            endpoint TEXT,
            method TEXT,
            request_data TEXT,
            response_status INTEGER,
            error_message TEXT,
            duration_ms REAL
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_logs(timestamp)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_action ON audit_logs(action)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON audit_logs(user_id)')
    conn.commit()
    conn.close()

def log_action(
    action: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    request_data: Optional[Dict[str, Any]] = None,
    response_status: Optional[int] = None,
    error_message: Optional[str] = None,
    duration_ms: Optional[float] = None
):
    """
    Log an action to the audit log.
    
    Args:
        action: Action description (e.g., "email_processed", "ticket_created")
        user_id: User identifier
        ip_address: IP address of the requester
        endpoint: API endpoint
        method: HTTP method
        request_data: Request data (sanitized)
        response_status: HTTP response status
        error_message: Error message if any
        duration_ms: Duration of the action in milliseconds
    """
    timestamp = datetime.utcnow().isoformat()
    
    # Sanitize request data (remove sensitive information)
    sanitized_data = None
    if request_data:
        sanitized_data = _sanitize_audit_data(request_data.copy())
    
    # Log to database
    try:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO audit_logs 
            (timestamp, action, user_id, ip_address, endpoint, method, 
             request_data, response_status, error_message, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp, action, user_id, ip_address, endpoint, method,
            json.dumps(sanitized_data) if sanitized_data else None,
            response_status, error_message, duration_ms
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to write audit log to database: {e}")
    
    # Also log to file
    log_entry = {
        'timestamp': timestamp,
        'action': action,
        'user_id': user_id,
        'ip_address': ip_address,
        'endpoint': endpoint,
        'method': method,
        'response_status': response_status,
        'error_message': error_message,
        'duration_ms': duration_ms
    }
    
    if error_message:
        logger.warning(f"Audit: {json.dumps(log_entry)}")
    else:
        logger.info(f"Audit: {json.dumps(log_entry)}")

def _sanitize_audit_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive information from audit data."""
    sensitive_fields = ['password', 'api_key', 'token', 'secret', 'authorization']
    sanitized = {}
    
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_audit_data(value)
        elif isinstance(value, list):
            sanitized[key] = [_sanitize_audit_data(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    
    return sanitized

def get_audit_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100
) -> list:
    """
    Retrieve audit logs with filtering.
    
    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        action: Filter by action
        user_id: Filter by user ID
        limit: Maximum number of results
    
    Returns:
        List of audit log entries
    """
    conn = sqlite3.connect(AUDIT_DB_PATH)
    c = conn.cursor()
    
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)
    
    if action:
        query += " AND action = ?"
        params.append(action)
    
    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    
    # Convert to list of dicts
    columns = ['id', 'timestamp', 'action', 'user_id', 'ip_address', 'endpoint',
               'method', 'request_data', 'response_status', 'error_message', 'duration_ms']
    
    return [dict(zip(columns, row)) for row in rows]

# Initialize audit DB on import
init_audit_db()

