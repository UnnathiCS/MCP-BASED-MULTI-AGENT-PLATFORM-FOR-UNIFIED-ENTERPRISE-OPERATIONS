import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

client = TestClient(app)

payload = {
    "title": "Team Sync",
    "description": "Weekly sync",
    "start_time": "2026-02-08T14:00:00+00:00",
    "end_time": "2026-02-08T15:00:00+00:00",
    "timezone": "UTC",
    "attendees": ["alice@example.com"],
    "location": "Conference Room A",
}

event = {
    "id": "ev1",
    "summary": "Team Sync",
    "description": "Weekly sync",
    "start": {"dateTime": "2026-02-08T14:00:00+00:00", "timeZone": "UTC"},
    "end": {"dateTime": "2026-02-08T15:00:00+00:00", "timeZone": "UTC"},
    "attendees": [{"email": "alice@example.com"}],
    "location": "Conference Room A",
    "hangoutLink": "https://meet.google.com/abc-123",
}

with patch("app.routes.meetings.create_meeting", return_value={"event": event, "explainability": {"api_call": "events.insert", "status": "success", "details": {}}}):
    r = client.post("/meetings/", json=payload)
    print(r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)
