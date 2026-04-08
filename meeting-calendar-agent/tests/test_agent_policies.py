from __future__ import annotations

from app.services.agent.policies import evaluate_policies
from app.services.agent.contracts import ConflictDetail


def test_allow_when_no_conflicts_and_in_hours():
    result = evaluate_policies([], "2026-02-08T10:00:00+00:00", "2026-02-08T11:00:00+00:00")
    assert result["allowed"] is True


def test_block_hard_conflict():
    conflicts = [ConflictDetail(type="HARD", severity="high", explanation="busy")]
    result = evaluate_policies(conflicts, "2026-02-08T10:00:00+00:00", "2026-02-08T11:00:00+00:00")
    assert result["allowed"] is False
    assert "Hard" in result["explanation"]


def test_block_outside_hours():
    result = evaluate_policies([], "2026-02-08T08:00:00+00:00", "2026-02-08T19:00:00+00:00")
    assert result["allowed"] is False
    assert "Outside" in result["explanation"]


def test_requires_approval_medium_threshold():
    conflicts = [ConflictDetail(type="SOFT", severity="medium", explanation="maybe")]
    result = evaluate_policies(conflicts, "2026-02-08T10:00:00+00:00", "2026-02-08T11:00:00+00:00", approval_severity_threshold="medium")
    assert result["allowed"] is False
    assert "approval" in result["explanation"]


def test_no_approval_if_below_threshold():
    conflicts = [ConflictDetail(type="SOFT", severity="low", explanation="low")]
    result = evaluate_policies(conflicts, "2026-02-08T10:00:00+00:00", "2026-02-08T11:00:00+00:00", approval_severity_threshold="medium")
    assert result["allowed"] is True
