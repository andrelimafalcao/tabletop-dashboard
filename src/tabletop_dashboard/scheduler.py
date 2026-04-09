"""Refresh scheduler — wakes periodically to fetch data and redraw the display."""

from __future__ import annotations

import logging
import signal
import time

from tabletop_dashboard.calendar.fetcher import CalendarFetcher
from tabletop_dashboard.config import AppConfig
from tabletop_dashboard.display.base import DisplayDriver
from tabletop_dashboard.display.renderer import Renderer

logger = logging.getLogger(__name__)


class Scheduler:
    """Runs the fetch → render → sleep loop."""

    def __init__(self, config: AppConfig, driver: DisplayDriver) -> None:
        self._config = config
        self._driver = driver
        self._fetcher = CalendarFetcher(config.calendar.sources)
        self._renderer = Renderer(driver)
        self._running = False

    def run(self) -> None:
        """Start the main loop. Blocks until SIGINT/SIGTERM."""
        self._running = True
        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)

        logger.info("Scheduler started (interval=%ds)", self._config.scheduler.refresh_interval_sec)
        while self._running:
            self._tick()
            if self._running:
                time.sleep(self._config.scheduler.refresh_interval_sec)

    def _tick(self) -> None:
        logger.info("Fetching calendar events…")
        try:
            events = self._fetcher.fetch_upcoming()
            logger.info("Fetched %d event(s)", len(events))
            self._renderer.render(events)
        except Exception:
            logger.exception("Tick failed")

    def _stop(self, *_: object) -> None:
        logger.info("Shutting down…")
        self._running = False
        self._driver.close()
