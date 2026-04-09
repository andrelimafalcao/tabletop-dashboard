"""Daily Agenda view — C-02, C-06, C-07, C-08, C-09, C-14."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

from tabletop_dashboard.calendar.models import CalendarEvent

if TYPE_CHECKING:
    from PIL import ImageDraw, ImageFont

# Layout constants (baseline 800×480)
MARGIN = 20
HEADER_H = 45
HOUR_COL_W = 65
START_HOUR = 8
END_HOUR = 20  # exclusive; hours 8..19 displayed
HOURS = END_HOUR - START_HOUR  # 12
MIN_EVENT_H = 4

BG = 255
FG = 0
GRAY = 160


def _to_aware(dt: datetime | date) -> datetime | None:
    if isinstance(dt, datetime):
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    return None


def _px_per_hour(height: int) -> float:
    return (height - HEADER_H) / HOURS


def _time_to_y(dt: datetime | date, height: int, day_offset: int = 0) -> float:
    """Convert a datetime to a y-pixel position in the timeline."""
    if isinstance(dt, datetime):
        local = dt.astimezone()
        h = local.hour + local.minute / 60 + local.second / 3600
    elif isinstance(dt, date):
        h = float(START_HOUR)
    else:
        h = float(START_HOUR)
    h = max(START_HOUR, min(END_HOUR, h))
    return HEADER_H + (h - START_HOUR) * _px_per_hour(height)


def render_daily_agenda(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    events: list[CalendarEvent],
    now: datetime,
    fonts: dict[str, ImageFont.ImageFont],
    day_offset: int = 0,
) -> None:
    """Render the Daily Agenda (timeline) view onto *draw*.

    *day_offset* = 0 for today, 1 for tomorrow, -1 for yesterday.
    """
    target_date = (now + timedelta(days=day_offset)).date()
    pph = _px_per_hour(height)

    # C-09: Day navigation header
    header_str = (now + timedelta(days=day_offset)).strftime("%A, %B %-d, %Y")
    full_header = f"\u25c4  {header_str}  \u25ba"
    hdr_w = int(draw.textlength(full_header, font=fonts["date"]))
    draw.text(((width - hdr_w) // 2, 10), full_header, font=fonts["date"], fill=FG)

    # Timeline area divider (vertical line separating hour labels from events)
    draw.line([(HOUR_COL_W - 2, HEADER_H), (HOUR_COL_W - 2, height)], fill=FG, width=1)

    # C-07: Hourly timeline — hour labels and horizontal tick marks
    for hour in range(START_HOUR, END_HOUR):
        y = int(HEADER_H + (hour - START_HOUR) * pph)
        label = f"{hour % 12 or 12}{'AM' if hour < 12 else 'PM'}"
        draw.text((4, y + 2), label, font=fonts["hour_label"], fill=FG)
        draw.line([(HOUR_COL_W - 2, y), (width, y)], fill=180, width=1)

    # Bottom border
    end_y = int(HEADER_H + HOURS * pph)
    draw.line([(HOUR_COL_W - 2, end_y), (width, end_y)], fill=FG, width=1)

    # C-08: Event blocks — filled rectangles proportional to duration
    event_x0 = HOUR_COL_W + 4
    event_x1 = width - 4
    target_events = [
        e
        for e in events
        if not e.all_day
        and isinstance(e.start, datetime)
        and e.start.astimezone().date() == target_date
    ]

    for event in target_events:
        y_start = _time_to_y(event.start, height)
        y_end = _time_to_y(event.end, height) if event.end is not None else y_start + pph
        y_end = max(y_start + MIN_EVENT_H, y_end)
        y_start = max(HEADER_H, min(height - MIN_EVENT_H, y_start))
        y_end = max(y_start + MIN_EVENT_H, min(height, y_end))

        draw.rectangle(
            [(event_x0, int(y_start)), (event_x1, int(y_end))],
            fill=FG,
        )
        # Label inside block (if space allows)
        block_h = y_end - y_start
        if block_h >= 16:
            start_dt = event.start
            if isinstance(start_dt, datetime):
                local_s = start_dt.astimezone()
                time_label = local_s.strftime("%-I:%M %p")
                label_text = f"{time_label} {event.title}"
            else:
                label_text = event.title
            # Clip text to block width
            avail_w = event_x1 - event_x0 - 8
            font_et = fonts["event_time"]
            while label_text and int(draw.textlength(label_text, font=font_et)) > avail_w:
                label_text = label_text[:-1]
            if label_text:
                draw.text(
                    (event_x0 + 4, int(y_start) + 2),
                    label_text,
                    font=fonts["event_time"],
                    fill=BG,
                )

    # C-14: Empty state
    if not target_events:
        msg = "No events"
        msg_w = int(draw.textlength(msg, font=fonts["event_title"]))
        mid_y = HEADER_H + int(HOURS * pph / 2)
        draw.text(((width - msg_w) // 2, mid_y), msg, font=fonts["event_title"], fill=GRAY)

    # C-06: Now marker — horizontal dashed line at current time (today only)
    if day_offset == 0:
        now_y = int(_time_to_y(now, height))
        if HEADER_H <= now_y <= height:
            dash_len, gap_len = 6, 4
            x = HOUR_COL_W
            while x < width:
                draw.line([(x, now_y), (min(x + dash_len, width), now_y)], fill=FG, width=2)
                x += dash_len + gap_len
