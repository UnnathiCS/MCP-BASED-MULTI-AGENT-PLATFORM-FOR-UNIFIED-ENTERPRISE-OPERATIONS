import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from app.database.connection import get_audit_conn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('audit.log'), logging.StreamHandler()]
)
logger = logging.getLogger('audit')


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
    timestamp = datetime.utcnow().isoformat()
    sanitized_data = _sanitize_audit_data(request_data.copy()) if request_data else None
    try:
        conn = get_audit_conn()
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
        logger.error(f"Failed to write audit log: {e}")

    log_entry = {'timestamp': timestamp, 'action': action, 'user_id': user_id,
                 'ip_address': ip_address, 'endpoint': endpoint, 'method': method,
                 'response_status': response_status, 'error_message': error_message,
                 'duration_ms': duration_ms}
    if error_message:
        logger.warning(f"Audit: {json.dumps(log_entry)}")
    else:
        logger.info(f"Audit: {json.dumps(log_entry)}")


def _sanitize_audit_data(data: Dict[str, Any]) -> Dict[str, Any]:
    sensitive_fields = ['password', 'api_key', 'token', 'secret', 'authorization']
    sanitized = {}
    for key, value in data.items():
        if any(s in key.lower() for s in sensitive_fields):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_audit_data(value)
        elif isinstance(value, list):
            sanitized[key] = [_sanitize_audit_data(i) if isinstance(i, dict) else i for i in value]
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
    conn = get_audit_conn()
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
    columns = ['id', 'timestamp', 'action', 'user_id', 'ip_address', 'endpoint',
               'method', 'request_data', 'response_status', 'error_message', 'duration_ms']
    return [dict(zip(columns, row)) for row in rows]
