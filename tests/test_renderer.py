"""Tests for the frame renderer and mock display driver."""

from __future__ import annotations

from datetime import datetime, timezone

from PIL import Image

from tabletop_dashboard.calendar.models import CalendarEvent
from tabletop_dashboard.display.mock import MockDisplayDriver
from tabletop_dashboard.display.renderer import Renderer


def test_mock_driver_creates_png(tmp_path):  # type: ignore[no-untyped-def]
    driver = MockDisplayDriver(output_dir=tmp_path)
    img = Image.new("L", (driver.width, driver.height), 255)
    driver.display(img)
    assert driver.last_frame_path is not None
    assert driver.last_frame_path.exists()


def test_mock_driver_dimensions():  # type: ignore[no-untyped-def]
    driver = MockDisplayDriver()
    assert driver.width == MockDisplayDriver.DEFAULT_WIDTH
    assert driver.height == MockDisplayDriver.DEFAULT_HEIGHT


def test_renderer_produces_image(mock_driver):  # type: ignore[no-untyped-def]
    renderer = Renderer(mock_driver)
    now = datetime(2026, 4, 9, 8, 0, tzinfo=timezone.utc)
    events = [
        CalendarEvent(
            start=datetime(2026, 4, 9, 10, 0, tzinfo=timezone.utc),
            title="Team standup",
        ),
        CalendarEvent(
            start=datetime(2026, 4, 9, 14, 30, tzinfo=timezone.utc),
            title="1:1 with manager",
        ),
    ]
    renderer.render(events, as_of=now)
    assert mock_driver.last_frame_path is not None
    assert mock_driver.last_frame_path.exists()


def test_renderer_empty_events(mock_driver):  # type: ignore[no-untyped-def]
    renderer = Renderer(mock_driver)
    renderer.render([], as_of=datetime(2026, 4, 9, 8, 0, tzinfo=timezone.utc))
    assert mock_driver.last_frame_path is not None


def test_renderer_clears_display(mock_driver):  # type: ignore[no-untyped-def]
    mock_driver.clear()
    assert mock_driver.last_frame_path is not None
    assert mock_driver.last_frame_path.exists()
