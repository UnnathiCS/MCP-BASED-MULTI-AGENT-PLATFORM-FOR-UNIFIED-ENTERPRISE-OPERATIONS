from __future__ import annotations
from datetime import datetime, timedelta, time
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.integrations.google_calendar import query_freebusy


# NOTE: this module implements a simple availability engine for Phase-2.
# It does not involve any AI; rather it wraps the Google Calendar
# freebusy API and applies basic business rules such as working hours.
# The engine returns a list of free time slots between a requested window.



def _parse_iso(dt_str: str) -> datetime:
    """Parse an ISO 8601 string into an aware datetime object."""
    # datetime.fromisoformat handles offsets like +00:00
    return datetime.fromisoformat(dt_str)



def _merge_intervals(intervals: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
    if not intervals:
        return []
    sorted_int = sorted(intervals, key=lambda x: x[0])
    merged: List[Tuple[datetime, datetime]] = []
    cur_start, cur_end = sorted_int[0]
    for s, e in sorted_int[1:]:
        if s <= cur_end:
            # overlapping or contiguous
            cur_end = max(cur_end, e)
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = s, e
    merged.append((cur_start, cur_end))
    return merged



def _split_by_working_hours(
    slot_start: datetime, slot_end: datetime, tzinfo=None
) -> List[Tuple[datetime, datetime]]:
    """Given a free slot, return pieces that fall within 9am–6pm local time.

    Working hours are interpreted in the provided ``tzinfo``.  If no timezone
    is supplied, we fall back to ``slot_start.tzinfo`` to preserve backwards
    compatibility.
    """
    result: List[Tuple[datetime, datetime]] = []
    cur = slot_start
    # choose timezone for working hours
    tz = tzinfo if tzinfo is not None else slot_start.tzinfo
    while cur < slot_end:
        local = cur.astimezone(tz) if tz else cur
        day = local.date()
        wh_start_local = datetime.combine(day, time(hour=9), tzinfo=tz)
        wh_end_local = datetime.combine(day, time(hour=18), tzinfo=tz)
        wh_start_utc = wh_start_local
        wh_end_utc = wh_end_local
        # intersection of [cur, slot_end] with [wh_start_utc, wh_end_utc]
        window_start = max(cur, wh_start_utc)
        window_end = min(slot_end, wh_end_utc)
        if window_start < window_end:
            result.append((window_start, window_end))
        # move to next day beginning
        cur = datetime.combine(day + timedelta(days=1), time.min, tzinfo=tz)
    return result



def compute_free_slots(
    participants: Optional[Iterable[str]], time_min: str, time_max: str
) -> List[Dict[str, str]]:
    """Return free time slots for the given window and participants.

    - Queries Google Calendar freebusy API for primary calendar and any
      participant emails supplied.
    - Normalizes all times to aware datetimes using the offsets provided in
      the input.
    - Excludes any times outside 9am–6pm local working hours.

    The returned list contains dictionaries with ``start`` and ``end``
    keys (ISO strings).
    """
    # gather busy intervals
    fb = query_freebusy(time_min, time_max, participants)
    busy: List[Tuple[datetime, datetime]] = []
    for cal_data in fb.get("calendars", {}).values():
        for b in cal_data.get("busy", []):
            busy.append((_parse_iso(b["start"]), _parse_iso(b["end"])))
    merged_busy = _merge_intervals(busy)

    window_start = _parse_iso(time_min)
    window_end = _parse_iso(time_max)
    free_slots: List[Tuple[datetime, datetime]] = []
    cur = window_start
    for s, e in merged_busy:
        if e <= cur:
            continue
        if s > cur:
            free_slots.append((cur, s))
        cur = max(cur, e)
    if cur < window_end:
        free_slots.append((cur, window_end))

    # apply working hours filter using timezone of the request window
    req_tz = _parse_iso(time_min).tzinfo
    final: List[Dict[str, str]] = []
    for start, end in free_slots:
        for piece_start, piece_end in _split_by_working_hours(start, end, tzinfo=req_tz):
            final.append({"start": piece_start.isoformat(), "end": piece_end.isoformat()})
    return final
