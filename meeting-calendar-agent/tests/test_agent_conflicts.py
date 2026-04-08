from __future__ import annotations

from app.services.agent.conflicts import analyze_conflicts
from app.services.agent.contracts import ConflictDetail


def _availability(busy_list):
    return {"primary": {"busy": busy_list}}


def test_no_conflicts():
    av = _availability([])
    conf = analyze_conflicts("2026-02-08T10:00:00+00:00", "2026-02-08T11:00:00+00:00", av)
    assert conf == []


def test_hard_conflict_required():
    av = _availability([{"start": "2026-02-08T10:30:00+00:00", "end": "2026-02-08T11:30:00+00:00"}])
    conf = analyze_conflicts(
        "2026-02-08T10:00:00+00:00",
        "2026-02-08T11:00:00+00:00",
        av,
        required=["primary"],
    )
    assert len(conf) == 1
    assert conf[0].type == "HARD"
    assert conf[0].severity == "high"


def test_soft_conflict_optional():
    av = _availability([{"start": "2026-02-08T10:30:00+00:00", "end": "2026-02-08T11:30:00+00:00"}])
    conf = analyze_conflicts(
        "2026-02-08T10:00:00+00:00",
        "2026-02-08T11:00:00+00:00",
        av,
        optional=["primary"],
    )
    assert len(conf) == 1
    assert conf[0].type == "SOFT"
    assert conf[0].severity == "medium"


def test_policy_conflict():
    av = _availability([])
    conf = analyze_conflicts("2026-02-08T08:00:00+00:00", "2026-02-08T19:00:00+00:00", av)
    assert len(conf) == 1
    assert conf[0].type == "POLICY"
    assert conf[0].severity == "low"
