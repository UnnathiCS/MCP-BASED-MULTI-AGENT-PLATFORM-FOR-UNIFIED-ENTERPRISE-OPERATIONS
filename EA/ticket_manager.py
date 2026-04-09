import sqlite3
import datetime

DB_PATH = "tickets.db"

def init_ticket_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            conversation_id TEXT,
            message_id TEXT,
            subject TEXT,
            sender TEXT,
            body TEXT,
            date TEXT,
            assigned_agent TEXT,
            intent TEXT,
            response TEXT
        )
    ''')
    # Create indexes for better query performance
    c.execute('CREATE INDEX IF NOT EXISTS idx_conversation_id ON tickets(conversation_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_message_id ON tickets(message_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_date ON tickets(date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_sender ON tickets(sender)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_intent ON tickets(intent)')
    conn.commit()
    conn.close()

def create_ticket(email_data, conversation_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    now = datetime.datetime.now()
    ticket_id = f"TCK-{now.strftime('%Y%m%d-%H%M%S')}-{now.microsecond}"
    
    # If it's a new conversation, its ID is its own ticket_id
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

def find_conv_id_by_message_id(message_id):
    """Finds the conversation_id of a ticket given a message_id."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT conversation_id FROM tickets WHERE message_id = ?", (message_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_conversation_history(conversation_id):
    """Retrieves all messages for a given conversation_id."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT sender, body FROM tickets WHERE conversation_id = ? ORDER BY date ASC", (conversation_id,))
    history = c.fetchall()
    conn.close()
    
    formatted_history = ""
    for sender, body in history:
        formatted_history += f"--- From: {sender} ---\n{body}\n\n"
    return formatted_history

def update_ticket_with_processing(ticket_id, assigned_agent, intent, response):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE tickets
        SET assigned_agent = ?, intent = ?, response = ?
        WHERE ticket_id = ?
    ''', (assigned_agent, intent, response, ticket_id))
    conn.commit()
    conn.close()