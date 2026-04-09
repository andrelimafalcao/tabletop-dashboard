"""Frame renderer — composes calendar events into a Pillow Image."""

from __future__ import annotations

import textwrap
from datetime import date, datetime

from PIL import Image, ImageDraw, ImageFont

from tabletop_dashboard.calendar.models import CalendarEvent
from tabletop_dashboard.display.base import DisplayDriver


class Renderer:
    """Renders a list of upcoming calendar events onto an e-Ink frame."""

    BACKGROUND = 255  # white
    FOREGROUND = 0    # black

    def __init__(self, driver: DisplayDriver) -> None:
        self._driver = driver
        # Use default PIL bitmap font; override with a TTF path in production.
        try:
            self._font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
            self._font_body = ImageFont.truetype("DejaVuSans.ttf", 11)
        except OSError:
            self._font_title = ImageFont.load_default()
            self._font_body = ImageFont.load_default()

    def render(self, events: list[CalendarEvent], as_of: datetime | None = None) -> None:
        """Compose *events* into a frame and push it to the display."""
        image = Image.new("L", (self._driver.width, self._driver.height), self.BACKGROUND)
        draw = ImageDraw.Draw(image)

        now = as_of or datetime.now().astimezone()
        header = now.strftime("%-d %b  %H:%M")
        draw.text((4, 2), header, font=self._font_title, fill=self.FOREGROUND)
        draw.line([(0, 18), (self._driver.width, 18)], fill=self.FOREGROUND, width=1)

        y = 22
        row_height = 16
        for event in events:
            if y + row_height > self._driver.height:
                break
            line = self._format_event(event, now)
            for wrapped_line in textwrap.wrap(line, width=38):
                draw.text((4, y), wrapped_line, font=self._font_body, fill=self.FOREGROUND)
                y += row_height

        self._driver.display(image)

    @staticmethod
    def _format_event(event: CalendarEvent, now: datetime) -> str:
        start = event.start
        if isinstance(start, datetime):
            if start.date() == now.date():
                prefix = start.strftime("%H:%M")
            else:
                prefix = start.strftime("%-d %b %H:%M")
        elif isinstance(start, date):
            prefix = start.strftime("%-d %b") if start != now.date() else "Today"
        else:
            prefix = "?"
        return f"{prefix}  {event.title}"
