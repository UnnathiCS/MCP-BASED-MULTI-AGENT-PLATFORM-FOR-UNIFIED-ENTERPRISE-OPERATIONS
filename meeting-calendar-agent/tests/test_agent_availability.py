from __future__ import annotations
from unittest.mock import patch

from app.services.agent.availability import compute_free_slots


def test_free_slots_no_busy():
    # no busy periods, window 8am-7pm UTC -> should return 9-18 only
    with patch("app.services.agent.availability.query_freebusy", return_value={"calendars": {"primary": {"busy": []}}}):
        slots = compute_free_slots([], "2026-02-08T08:00:00+00:00", "2026-02-08T19:00:00+00:00")
        # expect one slot 09:00-18:00
        assert slots == [{"start": "2026-02-08T09:00:00+00:00", "end": "2026-02-08T18:00:00+00:00"}]


def test_free_slots_with_busy():
    # busy from 12-13, should split into two slots
    busy = {"calendars": {"primary": {"busy": [{"start": "2026-02-08T12:00:00+00:00", "end": "2026-02-08T13:00:00+00:00"}]}}}
    with patch("app.services.agent.availability.query_freebusy", return_value=busy):
        slots = compute_free_slots([], "2026-02-08T09:00:00+00:00", "2026-02-08T18:00:00+00:00")
        assert slots == [
            {"start": "2026-02-08T09:00:00+00:00", "end": "2026-02-08T12:00:00+00:00"},
            {"start": "2026-02-08T13:00:00+00:00", "end": "2026-02-08T18:00:00+00:00"},
        ]


def test_free_slots_multiday_and_working_hours():
    # window spans two days; working hours should slice per day
    with patch("app.services.agent.availability.query_freebusy", return_value={"calendars": {"primary": {"busy": []}}}):
        slots = compute_free_slots([], "2026-02-08T15:00:00+00:00", "2026-02-09T12:00:00+00:00")
        # day1: 15-18, day2: 9-12
        assert slots == [
            {"start": "2026-02-08T15:00:00+00:00", "end": "2026-02-08T18:00:00+00:00"},
            {"start": "2026-02-09T09:00:00+00:00", "end": "2026-02-09T12:00:00+00:00"},
        ]
