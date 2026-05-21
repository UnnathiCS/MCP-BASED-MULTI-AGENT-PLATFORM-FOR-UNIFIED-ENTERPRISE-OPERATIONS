from pathlib import Path
import sqlite3
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

TICKETS_DB = str(BASE_DIR / "tickets.db")
AUDIT_DB = str(BASE_DIR / "audit.db")
ADMIN_DB = str(BASE_DIR / "admin.db")


def get_tickets_conn():
    return sqlite3.connect(TICKETS_DB)


def get_audit_conn():
    return sqlite3.connect(AUDIT_DB)


def get_admin_conn():
    return sqlite3.connect(ADMIN_DB)


def init_ticket_db():
    conn = get_tickets_conn()
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
    c.execute('CREATE INDEX IF NOT EXISTS idx_conversation_id ON tickets(conversation_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_message_id ON tickets(message_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_date ON tickets(date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_sender ON tickets(sender)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_intent ON tickets(intent)')
    conn.commit()
    conn.close()


def init_audit_db():
    conn = get_audit_conn()
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


def init_admin_db():
    conn = get_admin_conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            google_id TEXT UNIQUE,
            created_at TEXT NOT NULL,
            last_login TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_admin_email ON admin_accounts(email)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_admin_google_id ON admin_accounts(google_id)')
    conn.commit()
    conn.close()


def init_all_dbs():
    init_ticket_db()
    init_audit_db()
    init_admin_db()
