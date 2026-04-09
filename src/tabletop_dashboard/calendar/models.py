"""Calendar domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, order=True)
class CalendarEvent:
    """A single calendar event."""

    start: datetime | date
    title: str
    end: datetime | date | None = None
    all_day: bool = False
    uid: str = ""
