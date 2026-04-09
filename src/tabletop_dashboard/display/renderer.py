"""Frame renderer — composes calendar events into a Pillow Image."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from tabletop_dashboard.calendar.models import CalendarEvent
from tabletop_dashboard.display.base import DisplayDriver
from tabletop_dashboard.display.views import ViewKind
from tabletop_dashboard.display.views.daily_agenda import render_daily_agenda
from tabletop_dashboard.display.views.main_dashboard import (
    DIVIDER_Y,
    render_clock_badge,
    render_main_dashboard,
)
from tabletop_dashboard.display.views.mini_month import render_mini_month

# Font search paths (tried in order; first match wins)
_BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "DejaVuSans-Bold.ttf",
]
_REGULAR_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "DejaVuSans.ttf",
]
_MONO_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/dejavu/DejaVuSansMono-Bold.ttf",
    "DejaVuSansMono-Bold.ttf",
]


def _load_font(paths: list[str], size: int) -> Any:
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)  # type: ignore[call-arg]
    except TypeError:
        return ImageFont.load_default()


class Renderer:
    """Multi-view renderer for the e-Ink tabletop dashboard."""

    BACKGROUND = 255  # white
    FOREGROUND = 0  # black

    # Partial-refresh region: the header zone (clock + badge + day/date).
    # Covers y=0 to y=DIVIDER_Y on the main dashboard.
    PARTIAL_Y0 = 0
    PARTIAL_Y1 = DIVIDER_Y  # 148 px

    def __init__(self, driver: DisplayDriver) -> None:
        self._driver = driver
        self._fonts: dict[str, Any] = {}
        self._load_fonts()

    def _load_fonts(self) -> None:
        self._fonts = {
            "clock": _load_font(_MONO_PATHS, 80),
            "day_name": _load_font(_BOLD_PATHS, 32),
            "date": _load_font(_REGULAR_PATHS, 24),
            "badge": _load_font(_REGULAR_PATHS, 22),
            "event_title": _load_font(_REGULAR_PATHS, 20),
            "event_time": _load_font(_REGULAR_PATHS, 18),
            "section": _load_font(_BOLD_PATHS, 14),
            "hour_label": _load_font(_REGULAR_PATHS, 16),
            "month_header": _load_font(_BOLD_PATHS, 28),
            "day_num": _load_font(_REGULAR_PATHS, 18),
        }

    @property
    def partial_region(self) -> tuple[int, int, int, int]:
        """Bounding box for the partial-refresh zone: (x0, y0, x1, y1)."""
        return (0, self.PARTIAL_Y0, self._driver.width, self.PARTIAL_Y1)

    def render(
        self,
        events: list[CalendarEvent],
        view: ViewKind = ViewKind.MAIN_DASHBOARD,
        as_of: datetime | None = None,
    ) -> None:
        """Compose *events* into a full frame for *view* and push to the display."""
        now = as_of or datetime.now().astimezone()
        image = Image.new("L", (self._driver.width, self._driver.height), self.BACKGROUND)
        draw = ImageDraw.Draw(image)

        w, h = self._driver.width, self._driver.height
        if view == ViewKind.MAIN_DASHBOARD:
            render_main_dashboard(draw, w, h, events, now, self._fonts)
        elif view == ViewKind.DAILY_AGENDA:
            render_daily_agenda(draw, w, h, events, now, self._fonts)
        elif view == ViewKind.MINI_MONTH:
            render_mini_month(draw, w, h, events, now, self._fonts)

        self._driver.display(image)

    def render_partial(
        self,
        events: list[CalendarEvent],
        as_of: datetime | None = None,
    ) -> None:
        """Re-render only the clock/badge region and push a partial update.

        Suitable for per-minute updates without a full display refresh.
        Only meaningful when the current view is MAIN_DASHBOARD; for other
        views the caller should use :meth:`render` instead.
        """
        now = as_of or datetime.now().astimezone()
        region = self.partial_region
        rw = region[2] - region[0]
        rh = region[3] - region[1]
        image = Image.new("L", (rw, rh), self.BACKGROUND)
        draw = ImageDraw.Draw(image)
        render_clock_badge(draw, rw, events, now, self._fonts, offset_y=region[1])
        self._driver.display_partial(image, region)
