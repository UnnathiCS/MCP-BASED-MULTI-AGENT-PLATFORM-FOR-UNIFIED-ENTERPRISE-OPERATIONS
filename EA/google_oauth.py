"""
Google OAuth integration for admin authentication.
"""

import os
from typing import Optional, Dict
from flask import session, redirect, url_for, request
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

def verify_google_token(token: str) -> Optional[Dict]:
    """
    Verify Google OAuth token and return user info.
    
    Args:
        token: Google OAuth ID token
    
    Returns:
        User info dict with email, name, google_id, or None if invalid
    """
    if not GOOGLE_CLIENT_ID:
        print("Warning: GOOGLE_CLIENT_ID not set. Google OAuth disabled.")
        return None
    
    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        # Check if token is from correct issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        return {
            'email': idinfo.get('email'),
            'name': idinfo.get('name', ''),
            'google_id': idinfo.get('sub'),
            'picture': idinfo.get('picture', '')
        }
    except ValueError as e:
        print(f"Token verification failed: {e}")
        return None
    except Exception as e:
        print(f"Error verifying Google token: {e}")
        return None

def get_google_auth_url() -> str:
    """
    Get Google OAuth authorization URL.
    
    Returns:
        OAuth URL for Google sign-in
    """
    if not GOOGLE_CLIENT_ID:
        return ""
    
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/auth/google/callback")
    scope = "openid email profile"
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return auth_url

