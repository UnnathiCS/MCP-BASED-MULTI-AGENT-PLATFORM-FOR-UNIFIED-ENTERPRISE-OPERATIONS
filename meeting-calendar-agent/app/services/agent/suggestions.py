from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


# This module provides a simple rule-based slot ranking engine.  It assumes
# that availability information has already been computed by other modules
# (e.g. the availability engine) and focuses purely on sorting candidate
# slots according to participant availability and urgency.


def _parse_iso(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str)


def _overlaps(
    start: datetime, end: datetime, busy_start: datetime, busy_end: datetime
) -> bool:
    return not (busy_end <= start or busy_start >= end)


def suggest_slots(
    availability: Dict[str, Any],
    window_start: str,
    window_end: str,
    duration_minutes: int = 60,
    required: Optional[List[str]] = None,
    optional: Optional[List[str]] = None,
    urgency: float = 1.0,
) -> List[Dict[str, Any]]:
    """Rank candidate slots and return up to three suggestions.

    * ``availability``: mapping of calendar ids to busy lists, matching the
      format returned by ``check_availability``.
    * ``window_start``/``window_end``: ISO timestamps bounding the search.
    * ``duration_minutes``: length of each candidate slot.
    * ``required``/``optional``: participant lists used for scoring.
    * ``urgency``: higher values bias the ranking toward earlier slots.

    The returned list contains at most three dictionaries with ``start``,
    ``end`` and ``explanation`` keys.
    """
    start_dt = _parse_iso(window_start)
    end_dt = _parse_iso(window_end)
    required_set = set(required or [])
    optional_set = set(optional or [])

    # build a flat list of busy intervals per participant for quick lookup
    busy_intervals: Dict[str, List[tuple[datetime, datetime]]] = {}
    for cal_id, cal_data in availability.items():
        busy_intervals[cal_id] = [
            (_parse_iso(b["start"]), _parse_iso(b["end"]))
            for b in cal_data.get("busy", [])
        ]

    candidates: List[Dict[str, Any]] = []
    cur = start_dt
    delta = timedelta(minutes=duration_minutes)
    while cur + delta <= end_dt:
        slot_end = cur + delta
        # check required participants free
        req_ok = True
        opt_free = 0
        for cal_id, intervals in busy_intervals.items():
            busy_here = any(_overlaps(cur, slot_end, bs, be) for bs, be in intervals)
            if busy_here:
                if cal_id in required_set:
                    req_ok = False
                    break
                if cal_id in optional_set:
                    continue
                # treat unknown as optional for scoring
            else:
                if cal_id in optional_set or cal_id not in required_set:
                    opt_free += 1
        if req_ok:
            # compute score: optional free minus urgency*minutes from window start
            minutes_from_start = (cur - start_dt).total_seconds() / 60
            score = opt_free - urgency * minutes_from_start
            candidates.append(
                {
                    "start": cur.isoformat(),
                    "end": slot_end.isoformat(),
                    "opt_free": opt_free,
                    "score": score,
                }
            )
        cur += timedelta(minutes=15)  # sliding window step smaller than duration

    # sort and take top 3
    ranked = sorted(candidates, key=lambda x: (-x["score"], x["start"]))[:3]
    results: List[Dict[str, Any]] = []
    for r in ranked:
        explain = (
            f"Slot starting {r['start']} has {r['opt_free']} optional participants free "
            f"(urgency={urgency})"
        )
        results.append({"start": r["start"], "end": r["end"], "explanation": explain})
    return results
