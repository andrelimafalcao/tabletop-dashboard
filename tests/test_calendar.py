"""Tests for calendar models and iCal parsing."""

from __future__ import annotations

from datetime import date, datetime, timezone

from tabletop_dashboard.calendar.models import CalendarEvent
from tabletop_dashboard.calendar.fetcher import CalendarFetcher
from tabletop_dashboard.config import CalendarSource


ICAL_FIXTURE = b"""\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:event-001@test
DTSTART:20260409T100000Z
DTEND:20260409T110000Z
SUMMARY:Team standup
END:VEVENT
BEGIN:VEVENT
UID:event-002@test
DTSTART;VALUE=DATE:20260410
DTEND;VALUE=DATE:20260411
SUMMARY:All-day event
END:VEVENT
BEGIN:VEVENT
UID:event-003@test
DTSTART:20260401T080000Z
DTEND:20260401T090000Z
SUMMARY:Past event (should be filtered)
END:VEVENT
END:VCALENDAR
"""


def test_calendar_event_ordering():  # type: ignore[no-untyped-def]
    earlier = CalendarEvent(
        start=datetime(2026, 4, 9, 8, 0, tzinfo=timezone.utc), title="Early"
    )
    later = CalendarEvent(
        start=datetime(2026, 4, 9, 10, 0, tzinfo=timezone.utc), title="Late"
    )
    assert earlier < later
    assert sorted([later, earlier]) == [earlier, later]


def test_calendar_event_all_day():  # type: ignore[no-untyped-def]
    event = CalendarEvent(start=date(2026, 4, 10), title="Holiday", all_day=True)
    assert event.all_day is True


def test_parse_ical_returns_upcoming():  # type: ignore[no-untyped-def]
    start = datetime(2026, 4, 9, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 4, 16, 0, 0, tzinfo=timezone.utc)
    events = CalendarFetcher._parse_ical(ICAL_FIXTURE, start, end)
    titles = [e.title for e in events]
    assert "Team standup" in titles
    assert "All-day event" in titles
    assert "Past event (should be filtered)" not in titles


def test_parse_ical_timed_event_fields():  # type: ignore[no-untyped-def]
    start = datetime(2026, 4, 9, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 4, 16, 0, 0, tzinfo=timezone.utc)
    events = CalendarFetcher._parse_ical(ICAL_FIXTURE, start, end)
    standup = next(e for e in events if e.title == "Team standup")
    assert isinstance(standup.start, datetime)
    assert standup.all_day is False
    assert standup.uid == "event-001@test"


def test_fetcher_empty_sources():  # type: ignore[no-untyped-def]
    fetcher = CalendarFetcher([])
    events = fetcher.fetch_upcoming()
    assert events == []
