"""Mini Month Calendar view — C-10, C-11."""

from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import TYPE_CHECKING

from tabletop_dashboard.calendar.models import CalendarEvent

if TYPE_CHECKING:
    from PIL import ImageDraw, ImageFont

# Layout constants (baseline 800×480)
HEADER_H = 70
DAY_LABELS_H = 30
GRID_START_Y = 100
DOT_R = 3  # radius of event dot
DOT_OFFSET_Y = 18  # dot y relative to cell top

BG = 255
FG = 0
GRAY = 160


def render_mini_month(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    events: list[CalendarEvent],
    now: datetime,
    fonts: dict[str, ImageFont.ImageFont],
) -> None:
    """Render the Mini Month Calendar view onto *draw*."""
    today = now.date()
    year, month = today.year, today.month

    # C-11: Month header (centered)
    month_str = now.strftime("%B  %Y").upper()
    mhdr_w = int(draw.textlength(month_str, font=fonts["month_header"]))
    draw.text(((width - mhdr_w) // 2, 20), month_str, font=fonts["month_header"], fill=FG)

    # Day-of-week labels (Su Mo Tu We Th Fr Sa)
    col_w = width // 7
    day_names = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
    for col, name in enumerate(day_names):
        label_w = int(draw.textlength(name, font=fonts["section"]))
        x = col * col_w + (col_w - label_w) // 2
        draw.text((x, HEADER_H), name, font=fonts["section"], fill=FG)

    # Separator under day labels
    draw.line([(0, GRID_START_Y - 4), (width, GRID_START_Y - 4)], fill=FG, width=1)

    # Build set of dates that have events
    event_dates: set[date] = set()
    for e in events:
        if isinstance(e.start, datetime):
            event_dates.add(e.start.astimezone().date())
        elif isinstance(e.start, date):
            event_dates.add(e.start)

    # Compute grid
    cal = calendar.monthcalendar(year, month)
    avail_rows = max(len(cal), 1)
    row_h = (height - GRID_START_Y) // avail_rows

    # C-10: MiniMonthGrid — day cells
    for row_idx, week in enumerate(cal):
        for col_idx, day_num in enumerate(week):
            if day_num == 0:
                continue
            cell_date = date(year, month, day_num)
            cell_x = col_idx * col_w
            cell_y = GRID_START_Y + row_idx * row_h
            center_x = cell_x + col_w // 2
            num_str = str(day_num)
            num_w = int(draw.textlength(num_str, font=fonts["day_num"]))

            if cell_date == today:
                # Inverted box for today (C-10: today indicator)
                pad = 4
                draw.rectangle(
                    [
                        (center_x - num_w // 2 - pad, cell_y + 2),
                        (center_x + num_w // 2 + pad, cell_y + row_h - 4),
                    ],
                    fill=FG,
                )
                draw.text(
                    (center_x - num_w // 2, cell_y + 4),
                    num_str,
                    font=fonts["day_num"],
                    fill=BG,
                )
            else:
                # Normal day number
                text_fill = GRAY if cell_date < today else FG
                draw.text(
                    (center_x - num_w // 2, cell_y + 4),
                    num_str,
                    font=fonts["day_num"],
                    fill=text_fill,
                )

            # Event dot below day number
            if cell_date in event_dates:
                dot_x = center_x
                dot_y = cell_y + DOT_OFFSET_Y + 14
                dot_fill = BG if cell_date == today else FG
                draw.ellipse(
                    [
                        (dot_x - DOT_R, dot_y - DOT_R),
                        (dot_x + DOT_R, dot_y + DOT_R),
                    ],
                    fill=dot_fill,
                )
