import sqlite3
from datetime import datetime
from typing import Optional, Dict

from app.database.connection import get_admin_conn
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI


def create_admin_account(email: str, name: str, google_id: Optional[str] = None) -> int:
    conn = get_admin_conn()
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
        c.execute('SELECT id FROM admin_accounts WHERE email = ?', (email,))
        result = c.fetchone()
        return result[0] if result else None
    finally:
        conn.close()


def get_admin_by_email(email: str) -> Optional[Dict]:
    conn = get_admin_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM admin_accounts WHERE email = ?', (email,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    columns = ['id', 'email', 'name', 'google_id', 'created_at', 'last_login', 'is_active']
    return dict(zip(columns, row))


def get_admin_by_google_id(google_id: str) -> Optional[Dict]:
    conn = get_admin_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM admin_accounts WHERE google_id = ?', (google_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    columns = ['id', 'email', 'name', 'google_id', 'created_at', 'last_login', 'is_active']
    return dict(zip(columns, row))


def update_last_login(admin_id: int):
    conn = get_admin_conn()
    c = conn.cursor()
    c.execute('UPDATE admin_accounts SET last_login = ? WHERE id = ?',
              (datetime.utcnow().isoformat(), admin_id))
    conn.commit()
    conn.close()


def link_google_id(admin_id: int, google_id: str):
    conn = get_admin_conn()
    c = conn.cursor()
    c.execute('UPDATE admin_accounts SET google_id = ? WHERE id = ?', (google_id, admin_id))
    conn.commit()
    conn.close()


def verify_google_token(token: str) -> Optional[Dict]:
    if not GOOGLE_CLIENT_ID:
        return None
    try:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        return {
            'email': idinfo.get('email'),
            'name': idinfo.get('name', ''),
            'google_id': idinfo.get('sub'),
            'picture': idinfo.get('picture', '')
        }
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None


def get_google_auth_url() -> str:
    if not GOOGLE_CLIENT_ID:
        return ""
    return (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid email profile&"
        f"access_type=offline&"
        f"prompt=consent"
    )
