"""Main Dashboard view — C-01 through C-06, C-12, C-13, C-14."""

from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

from tabletop_dashboard.calendar.models import CalendarEvent

if TYPE_CHECKING:
    from PIL import ImageDraw, ImageFont

# Layout constants (baseline 800×480)
MARGIN = 20
DAY_Y = 6
DATE_Y = 12
CLOCK_Y = 50
BADGE_X = 370
BADGE_Y = 75
DIVIDER_Y = 148
SECTION_Y = 160
EVENTS_Y = 180
EVENT_ROW_H = 28

BG = 255
FG = 0
GRAY = 160


def _to_aware(dt: datetime | date) -> datetime | None:
    """Convert a date or datetime to an aware datetime, or None if date-only."""
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt
    return None


def _is_past(event: CalendarEvent, now: datetime) -> bool:
    """True if the event has ended (or started + no end, more than 1 h ago)."""
    if event.all_day:
        if isinstance(event.start, date):
            return event.start < now.date()
        return False
    start = _to_aware(event.start)  # type: ignore[arg-type]
    if start is None:
        return False
    if event.end is not None:
        end = _to_aware(event.end)  # type: ignore[arg-type]
        if end is not None:
            return end <= now
    return start + timedelta(hours=1) <= now


def _is_active(event: CalendarEvent, now: datetime) -> bool:
    """True if the event is currently in progress."""
    if event.all_day:
        if isinstance(event.start, date):
            return event.start == now.date()
        return False
    start = _to_aware(event.start)  # type: ignore[arg-type]
    if start is None or start > now:
        return False
    if event.end is not None:
        end = _to_aware(event.end)  # type: ignore[arg-type]
        if end is not None:
            return start <= now < end
    return start <= now < start + timedelta(hours=1)


def _minutes_until(event: CalendarEvent, now: datetime) -> int:
    """Minutes until the event starts (0 if already started)."""
    start = _to_aware(event.start)  # type: ignore[arg-type]
    if start is None:
        return 0
    delta = (start - now).total_seconds()
    return max(0, math.ceil(delta / 60))


def _get_today_events(events: list[CalendarEvent], now: datetime) -> list[CalendarEvent]:
    """Return events that start today (past, active, or upcoming)."""
    today = now.date()
    result = []
    for e in events:
        if e.all_day:
            if isinstance(e.start, date) and e.start == today:
                result.append(e)
        else:
            start = _to_aware(e.start)  # type: ignore[arg-type]
            if start is not None and start.date() == today:
                result.append(e)
    return result


def _get_next_event(events: list[CalendarEvent], now: datetime) -> CalendarEvent | None:
    """Return the next upcoming event (first that hasn't started yet)."""
    for e in events:
        if e.all_day:
            continue
        start = _to_aware(e.start)  # type: ignore[arg-type]
        if start is not None and start > now:
            return e
    return None


def _format_event_time(event: CalendarEvent, now: datetime) -> str:
    """Return a human-readable time prefix for an event row."""
    if event.all_day:
        return "All day"
    start = event.start
    if isinstance(start, datetime):
        local_start = start.astimezone()
        if local_start.date() == now.date():
            return local_start.strftime("%-I:%M %p").lstrip("0") or "12:00 AM"
        return local_start.strftime("%-d %b %-I:%M %p")
    return ""


def render_clock_badge(
    draw: ImageDraw.ImageDraw,
    width: int,
    events: list[CalendarEvent],
    now: datetime,
    fonts: dict[str, ImageFont.ImageFont],
    offset_y: int = 0,
) -> None:
    """Render C-01 (clock), C-02 (day/date), C-03 (next event badge) onto *draw*.

    All y positions are shifted by *offset_y* to support partial-refresh crops.
    """
    # C-02: Day name (bold, large) — top-left
    day_name = now.strftime("%A").upper()
    draw.text((MARGIN, DAY_Y - offset_y), day_name, font=fonts["day_name"], fill=FG)

    # C-02: Full date — top-right, right-aligned
    date_str = now.strftime("%B %-d, %Y").upper()
    date_w = int(draw.textlength(date_str, font=fonts["date"]))
    draw.text((width - MARGIN - date_w, DATE_Y - offset_y), date_str, font=fonts["date"], fill=FG)

    # C-01: Clock (largest element) — left zone
    clock_str = now.strftime("%-I:%M %p")
    draw.text((MARGIN, CLOCK_Y - offset_y), clock_str, font=fonts["clock"], fill=FG)

    # C-03: Next event badge — right of clock
    next_event = _get_next_event(events, now)
    if next_event is not None:
        mins = _minutes_until(next_event, now)
        if mins < 60:
            time_str = f"in {mins} min"
        else:
            hours = mins // 60
            rem = mins % 60
            time_str = f"in {hours}h {rem}m" if rem else f"in {hours}h"
        badge_text = f"\u25b6 {next_event.title}  {time_str}"
        draw.text((BADGE_X, BADGE_Y - offset_y), badge_text, font=fonts["badge"], fill=FG)


def render_main_dashboard(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    events: list[CalendarEvent],
    now: datetime,
    fonts: dict[str, ImageFont.ImageFont],
) -> None:
    """Render the Main Dashboard view onto *draw* (800×480 baseline)."""
    # Header zone: C-01, C-02, C-03
    render_clock_badge(draw, width, events, now, fonts, offset_y=0)

    # C-12: Section divider
    draw.line([(0, DIVIDER_Y), (width, DIVIDER_Y)], fill=FG, width=1)

    # Event list zone
    today_events = _get_today_events(events, now)

    # C-13: Section label
    draw.text((MARGIN, SECTION_Y), "TODAY", font=fonts["section"], fill=FG)

    y = EVENTS_Y
    if not today_events:
        # C-14: Empty state
        draw.text((MARGIN, y), "No events today", font=fonts["event_title"], fill=GRAY)
        return

    for event in today_events:
        if y + EVENT_ROW_H > height:
            break

        past = _is_past(event, now)
        active = _is_active(event, now)
        fill = GRAY if past else FG

        time_prefix = _format_event_time(event, now)

        if active:
            # C-06: NowMarker — invert the row background for active event
            draw.rectangle([(0, y - 2), (width, y + EVENT_ROW_H - 2)], fill=FG)
            row_fill = BG
        else:
            row_fill = fill

        # Time
        time_w = int(draw.textlength(time_prefix + "  ", font=fonts["event_time"]))
        draw.text((MARGIN, y), time_prefix, font=fonts["event_time"], fill=row_fill)

        # Title
        draw.text((MARGIN + time_w, y), event.title, font=fonts["event_title"], fill=row_fill)

        if active:
            # "← now" marker at right edge
            marker = "\u2190 now"
            marker_w = int(draw.textlength(marker, font=fonts["section"]))
            draw.text((width - MARGIN - marker_w, y + 6), marker, font=fonts["section"], fill=BG)

        y += EVENT_ROW_H
