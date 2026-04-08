from __future__ import annotations
from datetime import datetime, time
from typing import Any, Dict, List, Optional

from app.services.agent.contracts import ConflictDetail


# This module analyzes a proposed meeting window against availability
# information and returns a list of conflict details.  It is deliberately
# independent of Google APIs; callers supply the results of freebusy
# queries or availability engines.


def _parse_iso(dt: str) -> datetime:
    return datetime.fromisoformat(dt)


def _overlaps(start: datetime, end: datetime, busy_start: datetime, busy_end: datetime) -> bool:
    return not (busy_end <= start or busy_start >= end)


def analyze_conflicts(
    window_start: str,
    window_end: str,
    availability: Dict[str, Any],
    required: Optional[List[str]] = None,
    optional: Optional[List[str]] = None,
) -> List[ConflictDetail]:
    """Return a list of conflicts for the requested window.

    ``availability`` is expected to be a mapping such as the
    ``calendars`` value returned by ``check_availability`` (i.e. each
    key is a calendar id/participant email and its value has a ``busy``
    list of ``{start,end}`` ranges).

    ``required`` and ``optional`` are lists of participant identifiers
    that are treated with different severities.  Absence from both means
    the participant is ignored for conflict classification.
    """
    start_dt = _parse_iso(window_start)
    end_dt = _parse_iso(window_end)

    req_set = set(required or [])
    opt_set = set(optional or [])

    conflicts: List[ConflictDetail] = []

    # check participant availability
    for cal_id, cal_data in availability.items():
        for b in cal_data.get("busy", []):
            busy_start = _parse_iso(b["start"])
            busy_end = _parse_iso(b["end"])
            if _overlaps(start_dt, end_dt, busy_start, busy_end):
                if cal_id in req_set:
                    conflicts.append(
                        ConflictDetail(
                            type="HARD",
                            severity="high",
                            explanation=f"Required participant {cal_id} is busy during requested slot",
                        )
                    )
                elif cal_id in opt_set:
                    conflicts.append(
                        ConflictDetail(
                            type="SOFT",
                            severity="medium",
                            explanation=f"Optional participant {cal_id} is busy during requested slot",
                        )
                    )
                else:
                    # treat unknown calendars as hard by default
                    conflicts.append(
                        ConflictDetail(
                            type="HARD",
                            severity="high",
                            explanation=f"Participant {cal_id} (unspecified requirement) is busy",
                        )
                    )
                # break after first overlapping busy entry for this calendar
                break

    # policy: working hours
    # simple check: if window starts before 9am or ends after 6pm in its
    # local timezone (derived from start_dt)
    local_start = start_dt
    if local_start.time() < time(hour=9) or end_dt.time() > time(hour=18):
        conflicts.append(
            ConflictDetail(
                type="POLICY",
                severity="low",
                explanation="Requested time falls outside working hours (9am-6pm)",
            )
        )

    return conflicts
