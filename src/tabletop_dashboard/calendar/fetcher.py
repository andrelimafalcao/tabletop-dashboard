"""Calendar fetcher — supports iCal URL feeds and CalDAV servers."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import requests
from icalendar import Calendar  # type: ignore[import-untyped]

from tabletop_dashboard.calendar.models import CalendarEvent
from tabletop_dashboard.config import CalendarSource

logger = logging.getLogger(__name__)


class CalendarFetcher:
    """Fetches upcoming events from one or more calendar sources."""

    def __init__(self, sources: list[CalendarSource]) -> None:
        self._sources = sources

    def fetch_upcoming(self, days_ahead: int = 7) -> list[CalendarEvent]:
        """Return events starting within the next *days_ahead* days, sorted by start time."""
        now = datetime.now(tz=timezone.utc)
        cutoff = now + timedelta(days=days_ahead)
        events: list[CalendarEvent] = []

        for source in self._sources:
            try:
                events.extend(self._fetch_source(source, now, cutoff))
            except Exception:
                logger.exception("Failed to fetch calendar source %r", source.name)

        return sorted(events)

    def _fetch_source(
        self, source: CalendarSource, start: datetime, end: datetime
    ) -> list[CalendarEvent]:
        if source.url.startswith("webcal://"):
            url = "https://" + source.url[len("webcal://"):]
        else:
            url = source.url

        if source.username:
            response = requests.get(url, auth=(source.username, source.password), timeout=15)
        else:
            response = requests.get(url, timeout=15)
        response.raise_for_status()

        return self._parse_ical(response.content, start, end)

    @staticmethod
    def _parse_ical(
        data: bytes, start: datetime, end: datetime
    ) -> list[CalendarEvent]:
        cal = Calendar.from_ical(data)
        events: list[CalendarEvent] = []

        for component in cal.walk():
            if component.name != "VEVENT":
                continue

            dtstart = component.get("DTSTART")
            if dtstart is None:
                continue

            event_start = dtstart.dt
            # Normalise to aware datetime for comparison
            if isinstance(event_start, datetime):
                if event_start.tzinfo is None:
                    event_start = event_start.replace(tzinfo=timezone.utc)
                if not (start <= event_start <= end):
                    continue
                all_day = False
            else:
                # date-only event
                if not (start.date() <= event_start <= end.date()):
                    continue
                all_day = True

            dtend = component.get("DTEND")
            event_end = dtend.dt if dtend else None

            summary = str(component.get("SUMMARY", "(no title)"))
            uid = str(component.get("UID", ""))

            events.append(
                CalendarEvent(
                    start=event_start,
                    title=summary,
                    end=event_end,
                    all_day=all_day,
                    uid=uid,
                )
            )

        return events
