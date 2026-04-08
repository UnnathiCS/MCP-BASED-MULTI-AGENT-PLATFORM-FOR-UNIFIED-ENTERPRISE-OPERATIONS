from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
CLIENT_SECRETS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_FILE = CONFIG_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _load_credentials() -> Credentials | None:
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            return creds
        except Exception:
            return None
    return None


def _save_credentials(creds: Credentials) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with TOKEN_FILE.open("w", encoding="utf-8") as f:
        f.write(creds.to_json())


def get_calendar_service() -> Any:
    """Return an authenticated Google Calendar service object.

    Behavior:
    - Loads credentials from `config/credentials.json` and `config/token.json`.
    - Performs an OAuth login (local server) on first run.
    - Refreshes tokens automatically when expired.
    - Returns `googleapiclient.discovery.Resource` for the Calendar API.
    """
    creds = _load_credentials()

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

    if not creds:
        if not CLIENT_SECRETS_FILE.exists():
            raise FileNotFoundError(
                f"OAuth client secrets not found at {CLIENT_SECRETS_FILE}"
            )
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRETS_FILE), SCOPES
        )
        creds = flow.run_local_server(port=0)

    if creds and creds.valid:
        _save_credentials(creds)

    service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    return service
