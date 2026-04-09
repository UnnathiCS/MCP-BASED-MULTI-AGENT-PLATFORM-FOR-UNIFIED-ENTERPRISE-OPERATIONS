from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import threading
import time
import os
import traceback
import sqlite3
from functools import wraps
from email_fetcher import fetch_unread_emails
from ticket_manager import (
    create_ticket, update_ticket_with_processing,
    get_conversation_history, init_ticket_db
)
from responder import send_auto_reply, extract_customer_name
from gemini_agent import process_email_with_agent
from security import (
    sanitize_input, validate_email, validate_json_input,
    rate_limit, sanitize_sql_input
)
from audit_logger import log_action, get_audit_logs
from retry_logic import retry_function
from analytics import get_ticket_statistics, get_recent_tickets, get_performance_metrics, get_trends
from admin_auth import (
    create_admin_account,
    get_admin_by_email, get_admin_by_google_id, update_last_login
)
from google_oauth import verify_google_token, get_google_auth_url
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

# ================= Auth Helpers =================
def is_admin() -> bool:
    return bool(session.get("admin", False))

def require_admin_json():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401
    return None

# Initialize DB on startup
init_ticket_db()

# ================= Error Handling Decorator =================
def handle_errors(f):
    """Decorator for comprehensive error handling."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        ip_address = request.remote_addr
        endpoint = request.endpoint
        method = request.method
        
        try:
            result = f(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            
            # Log successful request
            log_action(
                action=f"{endpoint}_{method.lower()}",
                ip_address=ip_address,
                endpoint=request.path,
                method=method,
                response_status=200,
                duration_ms=duration
            )
            
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = str(e)
            error_trace = traceback.format_exc()
            
            logger.error(f"Error in {endpoint}: {error_msg}\n{error_trace}")
            
            # Log error
            log_action(
                action=f"{endpoint}_{method.lower()}_error",
                ip_address=ip_address,
                endpoint=request.path,
                method=method,
                response_status=500,
                error_message=error_msg,
                duration_ms=duration
            )
            
            return jsonify({
                'error': 'Internal server error',
                'message': 'An error occurred processing your request'
            }), 500
    
    return decorated_function

# ================= Health Check =================
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Check database connectivity
        conn = sqlite3.connect('tickets.db')
        c = conn.cursor()
        c.execute('SELECT 1')
        conn.close()
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    # Check audit DB
    try:
        conn = sqlite3.connect('audit.db')
        c = conn.cursor()
        c.execute('SELECT 1')
        conn.close()
        audit_db_status = 'healthy'
    except Exception as e:
        audit_db_status = f'unhealthy: {str(e)}'
    
    status = 'healthy' if db_status == 'healthy' and audit_db_status == 'healthy' else 'degraded'
    
    return jsonify({
        'status': status,
        'database': db_status,
        'audit_database': audit_db_status,
        'timestamp': time.time()
    }), 200 if status == 'healthy' else 503

@app.route('/emails/fetch', methods=['POST'])
@rate_limit(max_requests=30, window=60)
@handle_errors
def fetch_emails():
    """Fetch unread emails with rate limiting and error handling."""
    emails = retry_function(
        fetch_unread_emails,
        max_retries=2,
        initial_delay=1.0
    )
    return jsonify({'emails': emails})

@app.route('/tickets', methods=['POST'])
@rate_limit(max_requests=60, window=60)
@handle_errors
def create_ticket_endpoint():
    """Create a new ticket with input validation."""
    data = request.json or {}
    
    # Validate input
    is_valid, error_msg = validate_json_input(
        data,
        required_fields=['subject', 'from', 'body'],
        field_types={'subject': str, 'from': str, 'body': str}
    )
    
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Sanitize inputs
    sanitized_data = {
        'subject': sanitize_input(data.get('subject', ''), max_length=500),
        'from': sanitize_input(data.get('from', ''), max_length=255),
        'body': sanitize_input(data.get('body', ''), max_length=50000),
        'message_id': sanitize_input(data.get('message_id', ''), max_length=500) if data.get('message_id') else None,
        'in_reply_to': sanitize_input(data.get('in_reply_to', ''), max_length=500) if data.get('in_reply_to') else None,
    }
    
    # Validate email
    if not validate_email(sanitized_data['from']):
        return jsonify({'error': 'Invalid email address'}), 400
    
    ticket_id, conv_id = create_ticket(sanitized_data)
    return jsonify({'ticket_id': ticket_id, 'conversation_id': conv_id})

@app.route('/tickets', methods=['GET'])
@rate_limit(max_requests=100, window=60)
@handle_errors
def list_tickets():
    """List all tickets (admin only) with SQL injection prevention."""
    guard = require_admin_json()
    if guard:
        return guard
    
    # Get query parameters for filtering
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    intent_filter = request.args.get('intent', None)
    
    # Sanitize limit and offset
    limit = min(max(limit, 1), 1000)  # Between 1 and 1000
    offset = max(offset, 0)
    
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    
    if intent_filter:
        # Use parameterized query to prevent SQL injection
        intent_filter = sanitize_sql_input(intent_filter)
        c.execute('SELECT * FROM tickets WHERE intent = ? LIMIT ? OFFSET ?', (intent_filter, limit, offset))
    else:
        c.execute('SELECT * FROM tickets ORDER BY date DESC LIMIT ? OFFSET ?', (limit, offset))
    
    tickets = c.fetchall()
    conn.close()
    
    # Convert to list of dicts for better JSON response
    columns = ['ticket_id', 'conversation_id', 'message_id', 'subject', 'sender', 
               'body', 'date', 'assigned_agent', 'intent', 'response']
    tickets_list = [dict(zip(columns, ticket)) for ticket in tickets]
    
    return jsonify({'tickets': tickets_list, 'count': len(tickets_list)})
@app.route('/')
def home():
    return "API is running!"

# --- Frontend (Static) Serving ---
@app.route('/ui')
def serve_ui_index():
    return send_from_directory('frontend', 'index.html')

@app.route('/ui/<path:path>')
def serve_ui_assets(path):
    return send_from_directory('frontend', path)

@app.route('/ui/dashboard.html')
def serve_dashboard():
    return send_from_directory('frontend', 'dashboard.html')

@app.route('/ui/admin-signup.html')
def serve_admin_signup():
    return send_from_directory('frontend', 'admin-signup.html')

@app.route('/ui/admin-login.html')
def serve_admin_login():
    return send_from_directory('frontend', 'admin-login.html')

@app.route('/config')
def config_info():
    # Provide minimal client config like the recipient mailbox address
    return jsonify({
        'mailbox': os.getenv('EMAIL_ADDRESS', '')
    })
@app.route('/tickets/<ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    guard = require_admin_json()
    if guard:
        return guard
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    c.execute('SELECT * FROM tickets WHERE ticket_id = ?', (ticket_id,))
    ticket = c.fetchone()
    conn.close()
    return jsonify({'ticket': ticket})

@app.route('/tickets/<ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    data = request.json
    update_ticket_with_processing(ticket_id, data.get('assigned_agent'), data.get('intent'), data.get('response'))
    return jsonify({'status': 'updated'})

@app.route('/tickets/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    guard = require_admin_json()
    if guard:
        return guard
    history = get_conversation_history(conversation_id)
    return jsonify({'history': history})

@app.route('/tickets/<ticket_id>/process', methods=['POST'])
def process_ticket(ticket_id):
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    c.execute('SELECT body, conversation_id FROM tickets WHERE ticket_id = ?', (ticket_id,))
    result = c.fetchone()
    conn.close()
    if not result:
        return jsonify({'error': 'Ticket not found'}), 404
    body, conv_id = result
    full_history = get_conversation_history(conv_id)
    agent_response = process_email_with_agent(full_history)
    update_ticket_with_processing(ticket_id, 'Mail Agent', 'Processed by Agent', agent_response)
    return jsonify({'response': agent_response})

@app.route('/agent/process', methods=['POST'])
@rate_limit(max_requests=30, window=60)
@handle_errors
def process_arbitrary_email():
    """Process arbitrary email content with AI agent (preview mode)."""
    data = request.json or {}
    
    # Validate input
    is_valid, error_msg = validate_json_input(
        data,
        required_fields=['content'],
        field_types={'content': str}
    )
    
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Sanitize and limit content length
    email_content = sanitize_input(data.get('content', ''), max_length=50000)
    
    if not email_content:
        return jsonify({'error': 'Content cannot be empty'}), 400
    
    # Process with retry logic
    response = retry_function(
        process_email_with_agent,
        max_retries=2,
        initial_delay=1.0,
        email_content=email_content
    )
    
    # Extract customer name for preview
    customer_name = extract_customer_name(email_content)
    
    return jsonify({
        'response': response,
        'customer_name': customer_name,
        'preview': True
    })

@app.route('/tickets/<ticket_id>/reply', methods=['POST'])
def reply_ticket(ticket_id):
    data = request.json
    to_email = data.get('to_email')
    subject = data.get('subject')
    body = data.get('body')
    original_message_id = data.get('original_message_id')
    in_reply_to = data.get('in_reply_to')
    send_auto_reply(to_email, subject, body, original_message_id, in_reply_to)
    return jsonify({'status': 'reply sent'})

@app.route('/process-all', methods=['POST'])
def process_all():
    guard = require_admin_json()
    if guard:
        return guard
    from main import main
    main()
    return jsonify({'status': 'all processed'})

# ================= Auto Processing (Background) =================
_auto_lock = threading.Lock()
_auto_thread = None
_auto_stop_event = threading.Event()
_auto_interval_seconds = 60


def _auto_process_loop():
    from main import main as process_all_emails
    while not _auto_stop_event.is_set():
        try:
            process_all_emails()
        except Exception as e:
            print(f"[auto] Error during auto processing: {e}")
        # Wait with responsiveness to stop event
        waited = 0
        while waited < _auto_interval_seconds and not _auto_stop_event.is_set():
            time.sleep(1)
            waited += 1


@app.route('/autoprocess/start', methods=['POST'])
def autoprocess_start():
    guard = require_admin_json()
    if guard:
        return guard
    global _auto_thread, _auto_interval_seconds
    data = request.get_json(silent=True) or {}
    interval = int(data.get('interval', _auto_interval_seconds))
    if interval < 10:
        interval = 10
    with _auto_lock:
        if _auto_thread and _auto_thread.is_alive():
            _auto_interval_seconds = interval
            return jsonify({'running': True, 'interval': _auto_interval_seconds})
        _auto_stop_event.clear()
        _auto_interval_seconds = interval
        _auto_thread = threading.Thread(target=_auto_process_loop, daemon=True)
        _auto_thread.start()
        return jsonify({'running': True, 'interval': _auto_interval_seconds})


@app.route('/autoprocess/stop', methods=['POST'])
def autoprocess_stop():
    guard = require_admin_json()
    if guard:
        return guard
    with _auto_lock:
        if _auto_thread and _auto_thread.is_alive():
            _auto_stop_event.set()
            return jsonify({'running': False})
    return jsonify({'running': False})


@app.route('/autoprocess/status', methods=['GET'])
def autoprocess_status():
    guard = require_admin_json()
    if guard:
        return guard
    running = _auto_thread is not None and _auto_thread.is_alive() and not _auto_stop_event.is_set()
    return jsonify({'running': running, 'interval': _auto_interval_seconds})

# ================= Auth Routes =================

@app.route('/auth/google/verify', methods=['POST'])
@handle_errors
def verify_google_auth():
    """Verify Google OAuth token."""
    data = request.get_json(silent=True) or {}
    token = data.get('token', '')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 400
    
    user_info = verify_google_token(token)
    if not user_info:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get or create admin account
    admin = get_admin_by_google_id(user_info['google_id'])
    if not admin:
        admin = get_admin_by_email(user_info['email'])
        if not admin:
            # Create new admin account
            admin_id = create_admin_account(
                user_info['email'],
                user_info['name'],
                user_info['google_id']
            )
            admin = get_admin_by_email(user_info['email'])
        else:
            # Update with Google ID
            import sqlite3 as sqlite3_admin
            conn = sqlite3_admin.connect('admin.db')
            c = conn.cursor()
            c.execute('UPDATE admin_accounts SET google_id = ? WHERE id = ?', 
                     (user_info['google_id'], admin['id']))
            conn.commit()
            conn.close()
    
    # Log in directly after Google verification
    update_last_login(admin['id'])
    session['admin'] = True
    session['admin_id'] = admin['id']
    session['admin_email'] = admin['email']

    return jsonify({
        'authenticated': True,
        'admin_id': admin['id'],
        'email': admin['email'],
        'name': admin['name']
    })

@app.route('/auth/google/url', methods=['GET'])
@handle_errors
def get_google_auth_url_endpoint():
    """Get Google OAuth URL."""
    auth_url = get_google_auth_url()
    if not auth_url:
        return jsonify({'error': 'Google OAuth not configured'}), 500
    return jsonify({'auth_url': auth_url})

@app.route('/auth/logout', methods=['POST'])
def auth_logout():
    session.pop('admin', None)
    session.pop('admin_id', None)
    session.pop('admin_email', None)
    return jsonify({'authenticated': False})

@app.route('/auth/status', methods=['GET'])
def auth_status():
    admin_id = session.get('admin_id')
    return jsonify({
        'authenticated': is_admin(),
        'admin_id': admin_id
    })

# ================= Analytics & Dashboard Endpoints =================
@app.route('/api/analytics/statistics', methods=['GET'])
@rate_limit(max_requests=60, window=60)
@handle_errors
def get_statistics():
    """Get ticket statistics for dashboard (admin only)."""
    guard = require_admin_json()
    if guard:
        return guard
    
    days = request.args.get('days', 30, type=int)
    stats = get_ticket_statistics(days=days)
    return jsonify(stats)

@app.route('/api/analytics/recent-tickets', methods=['GET'])
@rate_limit(max_requests=60, window=60)
@handle_errors
def get_recent_tickets_endpoint():
    """Get recent tickets for dashboard (admin only)."""
    guard = require_admin_json()
    if guard:
        return guard
    
    limit = request.args.get('limit', 10, type=int)
    tickets = get_recent_tickets(limit=limit)
    return jsonify({'tickets': tickets})

@app.route('/api/analytics/performance', methods=['GET'])
@rate_limit(max_requests=60, window=60)
@handle_errors
def get_performance():
    """Get performance metrics (admin only)."""
    guard = require_admin_json()
    if guard:
        return guard
    
    days = request.args.get('days', 30, type=int)
    metrics = get_performance_metrics(days=days)
    return jsonify(metrics)

@app.route('/api/analytics/trends', methods=['GET'])
@rate_limit(max_requests=60, window=60)
@handle_errors
def get_trends_endpoint():
    """Get trend data for charts (admin only)."""
    guard = require_admin_json()
    if guard:
        return guard
    
    days = request.args.get('days', 30, type=int)
    trends = get_trends(days=days)
    return jsonify(trends)

# ================= Audit Logs Endpoint =================
@app.route('/audit/logs', methods=['GET'])
@handle_errors
def get_audit_logs_endpoint():
    """Get audit logs (admin only)."""
    guard = require_admin_json()
    if guard:
        return guard
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    action = request.args.get('action')
    user_id = request.args.get('user_id')
    limit = request.args.get('limit', 100, type=int)
    
    logs = get_audit_logs(
        start_date=start_date,
        end_date=end_date,
        action=action,
        user_id=user_id,
        limit=min(limit, 1000)
    )
    
    return jsonify({'logs': logs, 'count': len(logs)})

# ================= Response Preview Endpoint =================
@app.route('/tickets/<ticket_id>/preview', methods=['GET'])
@rate_limit(max_requests=60, window=60)
@handle_errors
def preview_ticket_response(ticket_id):
    """Preview AI response for a ticket before sending (admin only)."""
    guard = require_admin_json()
    if guard:
        return guard
    
    # Sanitize ticket_id to prevent SQL injection
    ticket_id = sanitize_sql_input(ticket_id)
    
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    c.execute('SELECT body, conversation_id, sender FROM tickets WHERE ticket_id = ?', (ticket_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return jsonify({'error': 'Ticket not found'}), 404
    
    body, conv_id, sender = result
    full_history = get_conversation_history(conv_id)
    
    # Process with agent
    agent_response = retry_function(
        process_email_with_agent,
        max_retries=2,
        initial_delay=1.0,
        email_content=full_history
    )
    
    # Extract customer name
    customer_name = extract_customer_name(sender, body)
    
    return jsonify({
        'ticket_id': ticket_id,
        'response': agent_response,
        'customer_name': customer_name,
        'preview': True
    })

if __name__ == '__main__':
    app.run(debug=True)
