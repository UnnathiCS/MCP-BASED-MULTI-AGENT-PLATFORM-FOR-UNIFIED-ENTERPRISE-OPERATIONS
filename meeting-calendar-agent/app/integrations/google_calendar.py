from __future__ import annotations
from typing import Any, Iterable, List

from googleapiclient.errors import HttpError
from app.integrations.google_calendar_client import get_calendar_service


# high-level helpers for Google Calendar operations that go beyond the
# thin client wrapper.  Phase‑1 only used raw service calls in
# meetings_service; Phase‑2 introduces free/busy queries and other
# availability helpers.  Keeping this logic in a separate module makes it
# easier to extend later (e.g. per‑calendar settings, caching, etc.)


def query_freebusy(
    time_min: str,
    time_max: str,
    attendees: Iterable[str] | None = None,
) -> Any:
    """Perform a freebusy query over the specified interval.

    The returned object is the raw response from the Google API.  It
    contains a ``calendars`` mapping where the keys are calendar IDs
    (``primary`` or attendee emails) and the values include a ``busy``
    list of time ranges.

    If the API call fails (e.g., bad attendee format, quota exceeded), we
    return a default result with empty busy periods so that the caller can
    continue gracefully.
    """
    service = get_calendar_service()
    items: List[dict] = [{"id": "primary"}]
    if attendees:
        items.extend({"id": email} for email in attendees)

    body: dict = {"timeMin": time_min, "timeMax": time_max, "items": items}
    
    try:
        return service.freebusy().query(body=body).execute()
    except HttpError as e:
        # Log and return default response with no busy times
        print(f"freebusy query failed: {e}")
        # Return expected structure with empty busy lists
        result = {"calendars": {}}
        for item in items:
            result["calendars"][item["id"]] = {"busy": []}
        return result
