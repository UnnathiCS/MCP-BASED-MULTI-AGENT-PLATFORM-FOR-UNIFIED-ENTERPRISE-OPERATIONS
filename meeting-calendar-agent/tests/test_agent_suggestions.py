from __future__ import annotations

from app.services.agent.suggestions import suggest_slots


def make_availability(busy_by_cal):
    # busy_by_cal: dict of cal_id -> list of {start,end}
    return {cal_id: {"busy": periods} for cal_id, periods in busy_by_cal.items()}


def test_suggest_prefers_more_optional():
    # two optional participants; first slot only one free, second slot both free
    busy = {
        "opt1": [{"start": "2026-02-08T09:00:00+00:00", "end": "2026-02-08T10:00:00+00:00"}],
        "opt2": [{"start": "2026-02-08T11:00:00+00:00", "end": "2026-02-08T12:00:00+00:00"}],
    }
    av = make_availability(busy)
    slots = suggest_slots(
        av,
        "2026-02-08T08:00:00+00:00",
        "2026-02-08T13:00:00+00:00",
        duration_minutes=60,
        optional=["opt1", "opt2"],
        urgency=1.0,
    )
    # expect best slot to start at 10:00 when both optional free
    assert slots[0]["start"] == "2026-02-08T10:00:00+00:00"


def test_urgency_prefers_earlier():
    # optional always free, but earlier slot should rank higher when urgency high
    av = make_availability({})
    slots_low = suggest_slots(
        av,
        "2026-02-08T08:00:00+00:00",
        "2026-02-08T12:00:00+00:00",
        duration_minutes=60,
        optional=["a"],
        urgency=0.1,
    )
    slots_high = suggest_slots(
        av,
        "2026-02-08T08:00:00+00:00",
        "2026-02-08T12:00:00+00:00",
        duration_minutes=60,
        optional=["a"],
        urgency=10.0,
    )
    assert slots_low[0]["start"] == "2026-02-08T09:00:00+00:00"  # maybe middle
    assert slots_high[0]["start"] == "2026-02-08T08:00:00+00:00"  # earliest
