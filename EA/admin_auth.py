"""
Admin authentication with Google OAuth.
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

ADMIN_DB_PATH = "admin.db"

def init_admin_db():
    """Initialize admin database."""
    conn = sqlite3.connect(ADMIN_DB_PATH)
    c = conn.cursor()

    # Admin accounts table
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

    # Create indexes
    c.execute('CREATE INDEX IF NOT EXISTS idx_admin_email ON admin_accounts(email)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_admin_google_id ON admin_accounts(google_id)')

    conn.commit()
    conn.close()

def create_admin_account(email: str, name: str, google_id: Optional[str] = None) -> int:
    """
    Create a new admin account.
    
    Args:
        email: Admin email address
        name: Admin name
        google_id: Google OAuth ID (optional)
    
    Returns:
        Admin account ID
    """
    conn = sqlite3.connect(ADMIN_DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO admin_accounts (email, name, google_id, created_at)
            VALUES (?, ?, ?, ?)
        ''', (email, name, google_id, datetime.utcnow().isoformat()))
        
        admin_id = c.lastrowid
        conn.commit()
        return admin_id
    except sqlite3.IntegrityError:
        # Account already exists
        c.execute('SELECT id FROM admin_accounts WHERE email = ?', (email,))
        result = c.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def get_admin_by_email(email: str) -> Optional[Dict]:
    """Get admin account by email."""
    conn = sqlite3.connect(ADMIN_DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT * FROM admin_accounts WHERE email = ?', (email,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return None
    
    columns = ['id', 'email', 'name', 'google_id', 'created_at', 'last_login', 'is_active']
    return dict(zip(columns, row))

def get_admin_by_google_id(google_id: str) -> Optional[Dict]:
    """Get admin account by Google ID."""
    conn = sqlite3.connect(ADMIN_DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT * FROM admin_accounts WHERE google_id = ?', (google_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return None
    
    columns = ['id', 'email', 'name', 'google_id', 'created_at', 'last_login', 'is_active']
    return dict(zip(columns, row))

def update_last_login(admin_id: int):
    """Update last login timestamp."""
    conn = sqlite3.connect(ADMIN_DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        UPDATE admin_accounts
        SET last_login = ?
        WHERE id = ?
    ''', (datetime.utcnow().isoformat(), admin_id))
    
    conn.commit()
    conn.close()

# Initialize database on import
init_admin_db()

