from __future__ import annotations
from datetime import datetime, time
from typing import Any, Dict, Iterable, List, Tuple

from app.services.agent.contracts import ConflictDetail


# This module encapsulates simple policy checks that must be evaluated
# prior to taking any action (e.g. auto-booking a meeting).  No AI logic is
# involved; the functions operate on the data structures produced earlier in
# the pipeline.


def _parse_iso(dt: str) -> datetime:
    return datetime.fromisoformat(dt)


def _outside_working_hours(start: datetime, end: datetime) -> bool:
    # local timezone assumed encoded in datetime object
    if start.time() < time(hour=9) or end.time() > time(hour=18):
        return True
    return False


def evaluate_policies(
    conflicts: Iterable[ConflictDetail],
    window_start: str,
    window_end: str,
    approval_severity_threshold: str = "high",
) -> Dict[str, Any]:
    """Run policy checks and return result.

    - If any conflict of type HARD exists, auto-booking is blocked.
    - If the meeting is outside working hours (9–18 local), blocked.
    - If any conflict severity >= threshold, the meeting requires approval.

    ``approval_severity_threshold`` should be one of ``"low"``,
    ``"medium"`` or ``"high"``.  Conflicts with severity equal or above are
    flagged for approval.

    Returns a dictionary with keys ``allowed`` (bool) and ``explanation``
    (str) describing the policy decision.
    """
    # severity ordering
    order = {"low": 1, "medium": 2, "high": 3}
    thresh_val = order.get(approval_severity_threshold, 3)

    # check times
    start_dt = _parse_iso(window_start)
    end_dt = _parse_iso(window_end)
    if _outside_working_hours(start_dt, end_dt):
        return {"allowed": False, "explanation": "Outside working hours"}

    # analyze conflicts
    requires_approval = False
    for c in conflicts:
        if c.type == "HARD":
            return {"allowed": False, "explanation": "Hard conflict present"}
        if order.get(c.severity, 0) >= thresh_val:
            requires_approval = True
    if requires_approval:
        return {"allowed": False, "explanation": "Requires approval due to severity"}

    return {"allowed": True, "explanation": "All policies passed"}
