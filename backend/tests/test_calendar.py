"""Tests for ContentCalendar."""

from datetime import datetime, timezone

import pytest

from content.calendar import ContentCalendar, WEEKLY_SCHEDULE

calendar = ContentCalendar()

REQUIRED_FIELDS = {"scheduled_at", "content_type", "language", "target_platform", "seo_keyword"}

# Monday April 13, 2026
START_DATE = datetime(2026, 4, 13, tzinfo=timezone.utc)


def test_generates_5_slots():
    plan = calendar.generate_weekly_plan(START_DATE, ["AI gateway"])
    assert len(plan) == 5


def test_slots_have_required_fields():
    plan = calendar.generate_weekly_plan(START_DATE, ["AI gateway"])
    for slot in plan:
        assert REQUIRED_FIELDS.issubset(slot.keys()), f"Missing fields in slot: {slot}"


def test_rotates_keywords():
    keywords = ["kw-a", "kw-b", "kw-c"]
    plan = calendar.generate_weekly_plan(START_DATE, keywords)
    used_keywords = [slot["seo_keyword"] for slot in plan]
    assert used_keywords[0] == "kw-a"
    assert used_keywords[1] == "kw-b"
    assert used_keywords[2] == "kw-c"
    assert used_keywords[3] == "kw-a"  # wraps around
    assert used_keywords[4] == "kw-b"


def test_get_next_monday():
    # Wednesday April 15, 2026 → next Monday April 20, 2026
    wednesday = datetime(2026, 4, 15, 12, 30, tzinfo=timezone.utc)
    next_monday = calendar.get_next_monday(wednesday)
    assert next_monday.year == 2026
    assert next_monday.month == 4
    assert next_monday.day == 20
    assert next_monday.weekday() == 0  # Monday
    assert next_monday.hour == 0
    assert next_monday.minute == 0
    assert next_monday.second == 0


def test_get_next_monday_from_monday():
    # From a Monday it should return same day
    monday = datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc)
    next_monday = calendar.get_next_monday(monday)
    assert next_monday.weekday() == 0
    assert next_monday.day == 13


def test_slots_scheduled_at_9am_utc():
    plan = calendar.generate_weekly_plan(START_DATE, ["keyword"])
    for slot in plan:
        assert slot["scheduled_at"].hour == 9
        assert slot["scheduled_at"].tzinfo is not None


def test_empty_keywords_uses_default():
    plan = calendar.generate_weekly_plan(START_DATE, [])
    for slot in plan:
        assert slot["seo_keyword"] == "AI API gateway"
