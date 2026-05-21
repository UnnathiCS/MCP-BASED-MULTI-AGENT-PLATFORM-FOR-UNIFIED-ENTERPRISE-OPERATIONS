import datetime
from typing import Optional, Tuple
from app.database.connection import get_tickets_conn


def create_ticket(email_data: dict, conversation_id: Optional[str] = None) -> Tuple[str, str]:
    conn = get_tickets_conn()
    c = conn.cursor()
    now = datetime.datetime.now()
    ticket_id = f"TCK-{now.strftime('%Y%m%d-%H%M%S')}-{now.microsecond}"
    if not conversation_id:
        conversation_id = ticket_id
    c.execute('''
        INSERT INTO tickets (ticket_id, conversation_id, message_id, subject, sender, body, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        ticket_id, conversation_id, email_data.get("message_id"),
        email_data["subject"], email_data["from"], email_data["body"],
        now.isoformat()
    ))
    conn.commit()
    conn.close()
    return ticket_id, conversation_id


def find_conv_id_by_message_id(message_id: str) -> Optional[str]:
    conn = get_tickets_conn()
    c = conn.cursor()
    c.execute("SELECT conversation_id FROM tickets WHERE message_id = ?", (message_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def get_conversation_history(conversation_id: str) -> str:
    conn = get_tickets_conn()
    c = conn.cursor()
    c.execute("SELECT sender, body FROM tickets WHERE conversation_id = ? ORDER BY date ASC", (conversation_id,))
    history = c.fetchall()
    conn.close()
    formatted = ""
    for sender, body in history:
        formatted += f"--- From: {sender} ---\n{body}\n\n"
    return formatted


def update_ticket_with_processing(ticket_id: str, assigned_agent: str, intent: str, response: str):
    conn = get_tickets_conn()
    c = conn.cursor()
    c.execute('''
        UPDATE tickets SET assigned_agent = ?, intent = ?, response = ?
        WHERE ticket_id = ?
    ''', (assigned_agent, intent, response, ticket_id))
    conn.commit()
    conn.close()


def list_tickets(limit: int = 100, offset: int = 0, intent: Optional[str] = None) -> list:
    conn = get_tickets_conn()
    c = conn.cursor()
    if intent:
        c.execute('SELECT * FROM tickets WHERE intent = ? LIMIT ? OFFSET ?', (intent, limit, offset))
    else:
        c.execute('SELECT * FROM tickets ORDER BY date DESC LIMIT ? OFFSET ?', (limit, offset))
    tickets = c.fetchall()
    conn.close()
    columns = ['ticket_id', 'conversation_id', 'message_id', 'subject', 'sender',
               'body', 'date', 'assigned_agent', 'intent', 'response']
    return [dict(zip(columns, t)) for t in tickets]


def get_ticket_by_id(ticket_id: str) -> Optional[dict]:
    conn = get_tickets_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM tickets WHERE ticket_id = ?', (ticket_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    columns = ['ticket_id', 'conversation_id', 'message_id', 'subject', 'sender',
               'body', 'date', 'assigned_agent', 'intent', 'response']
    return dict(zip(columns, row))
