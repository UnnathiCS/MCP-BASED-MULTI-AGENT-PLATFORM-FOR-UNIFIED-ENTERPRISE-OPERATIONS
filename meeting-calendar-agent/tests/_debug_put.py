import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

client = TestClient(app)

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

with patch("app.routes.meetings.update_meeting", return_value={"event": {**event, "summary": "Updated"}, "explainability": {"api_call":"events.patch","status":"success","details":{}}}):
    r = client.put(f"/meetings/{event['id']}", json={"title": "Updated", "start_time": event["start"]["dateTime"], "end_time": event["end"]["dateTime"], "timezone": event["start"]["timeZone"]})
    print(r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)
