"""Refresh scheduler — manages view rotation, partial refresh, and event fetching."""

from __future__ import annotations

import logging
import signal
import time

from tabletop_dashboard.calendar.fetcher import CalendarFetcher
from tabletop_dashboard.calendar.models import CalendarEvent
from tabletop_dashboard.config import AppConfig
from tabletop_dashboard.display.base import DisplayDriver
from tabletop_dashboard.display.renderer import Renderer
from tabletop_dashboard.display.views import ViewKind

logger = logging.getLogger(__name__)

_TICK_INTERVAL = 60  # seconds between scheduler wakes


class Scheduler:
    """Manages the fetch → render loop with view rotation and partial refresh."""

    def __init__(self, config: AppConfig, driver: DisplayDriver) -> None:
        self._config = config
        self._driver = driver
        self._fetcher = CalendarFetcher(config.calendar.sources)
        self._renderer = Renderer(driver)
        self._running = False

        self._events: list[CalendarEvent] = []
        self._view_idx: int = 0
        self._last_event_fetch: float = 0.0
        self._last_full_refresh: float = 0.0
        self._last_partial_refresh: float = 0.0
        self._last_view_rotation: float = 0.0

    @property
    def _current_view(self) -> ViewKind:
        views = [ViewKind(v) for v in self._config.views.rotation]
        if not views:
            return ViewKind.MAIN_DASHBOARD
        return views[self._view_idx % len(views)]

    def run(self) -> None:
        """Start the main loop. Blocks until SIGINT/SIGTERM."""
        self._running = True
        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)

        logger.info(
            "Scheduler started (rotation=%ds, partial=%ds, full_refresh=%ds)",
            self._config.views.rotation_interval_sec,
            self._config.views.partial_refresh_interval_sec,
            self._config.views.full_refresh_interval_sec,
        )

        # Initial render
        self._fetch_events()
        self._do_full_refresh()

        while self._running:
            time.sleep(_TICK_INTERVAL)
            if not self._running:
                break
            self._tick()

    def _tick(self) -> None:
        now_mono = time.monotonic()
        vc = self._config.views

        # Re-fetch events if interval elapsed
        if now_mono - self._last_event_fetch >= self._config.scheduler.refresh_interval_sec:
            self._fetch_events()

        # Rotate view if interval elapsed
        if now_mono - self._last_view_rotation >= vc.rotation_interval_sec:
            self._view_idx += 1
            self._last_view_rotation = now_mono
            logger.info("Rotating to view: %s", self._current_view)
            self._do_full_refresh()
            return

        # Anti-ghosting full refresh
        if now_mono - self._last_full_refresh >= vc.full_refresh_interval_sec:
            logger.info("Anti-ghosting full refresh")
            self._do_full_refresh()
            return

        # Partial refresh: clock + badge update (main dashboard only)
        if (
            self._current_view == ViewKind.MAIN_DASHBOARD
            and now_mono - self._last_partial_refresh >= vc.partial_refresh_interval_sec
        ):
            self._do_partial_refresh()

    def _fetch_events(self) -> None:
        logger.info("Fetching calendar events…")
        try:
            self._events = self._fetcher.fetch_upcoming()
            self._last_event_fetch = time.monotonic()
            logger.info("Fetched %d event(s)", len(self._events))
        except Exception:
            logger.exception("Event fetch failed")

    def _do_full_refresh(self) -> None:
        try:
            self._renderer.render(self._events, view=self._current_view)
            t = time.monotonic()
            self._last_full_refresh = t
            self._last_partial_refresh = t
            logger.info("Full refresh (%s)", self._current_view)
        except Exception:
            logger.exception("Full refresh failed")

    def _do_partial_refresh(self) -> None:
        try:
            self._renderer.render_partial(self._events)
            self._last_partial_refresh = time.monotonic()
            logger.info("Partial refresh (clock/badge)")
        except Exception:
            logger.exception("Partial refresh failed")

    def _stop(self, *_: object) -> None:
        logger.info("Shutting down…")
        self._running = False
        self._driver.close()
