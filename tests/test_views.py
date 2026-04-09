"""Tests for multi-view renderer and partial refresh."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from tabletop_dashboard.calendar.models import CalendarEvent
from tabletop_dashboard.display.mock import MockDisplayDriver
from tabletop_dashboard.display.renderer import Renderer
from tabletop_dashboard.display.views import ViewKind

_NOW = datetime(2026, 4, 9, 10, 0, tzinfo=UTC)

_EVENTS = [
    CalendarEvent(
        start=datetime(2026, 4, 9, 11, 0, tzinfo=UTC),
        end=datetime(2026, 4, 9, 11, 30, tzinfo=UTC),
        title="Team Standup",
    ),
    CalendarEvent(
        start=datetime(2026, 4, 9, 14, 0, tzinfo=UTC),
        end=datetime(2026, 4, 9, 15, 30, tzinfo=UTC),
        title="Product Review",
    ),
    CalendarEvent(
        start=datetime(2026, 4, 9, 9, 0, tzinfo=UTC),
        end=datetime(2026, 4, 9, 9, 30, tzinfo=UTC),
        title="Morning Sync (past)",
    ),
    CalendarEvent(start=date(2026, 4, 9), title="All-day reminder", all_day=True),
    CalendarEvent(
        start=datetime(2026, 4, 10, 10, 0, tzinfo=UTC),
        title="Tomorrow meeting",
    ),
]


@pytest.mark.parametrize("view", list(ViewKind))
def test_render_view_produces_png(tmp_path: pytest.Path, view: ViewKind) -> None:
    """Each view should produce a saved PNG frame."""
    driver = MockDisplayDriver(output_dir=tmp_path)
    renderer = Renderer(driver)
    renderer.render(_EVENTS, view=view, as_of=_NOW)
    assert driver.last_frame_path is not None
    assert driver.last_frame_path.exists()


def test_three_views_produce_different_output(tmp_path: pytest.Path) -> None:
    """The three views should produce visually distinct frames."""
    driver = MockDisplayDriver(output_dir=tmp_path)
    renderer = Renderer(driver)

    frames: list[bytes] = []
    for view in ViewKind:
        renderer.render(_EVENTS, view=view, as_of=_NOW)
        assert driver.last_frame_path is not None
        frames.append(driver.last_frame_path.read_bytes())

    # All three frames must differ from each other
    assert frames[0] != frames[1]
    assert frames[1] != frames[2]
    assert frames[0] != frames[2]


def test_render_partial_produces_partial_png(tmp_path: pytest.Path) -> None:
    """render_partial should save a smaller partial-region PNG."""
    driver = MockDisplayDriver(output_dir=tmp_path)
    renderer = Renderer(driver)
    renderer.render_partial(_EVENTS, as_of=_NOW)
    assert driver.last_partial_path is not None
    assert driver.last_partial_path.exists()


def test_partial_image_dimensions(tmp_path: pytest.Path) -> None:
    """Partial frame dimensions match the declared partial_region height."""
    from PIL import Image

    driver = MockDisplayDriver(output_dir=tmp_path)
    renderer = Renderer(driver)
    region = renderer.partial_region
    renderer.render_partial(_EVENTS, as_of=_NOW)
    assert driver.last_partial_path is not None
    img = Image.open(driver.last_partial_path)
    expected_w = region[2] - region[0]
    expected_h = region[3] - region[1]
    assert img.size == (expected_w, expected_h)


def test_render_default_view_is_main_dashboard(tmp_path: pytest.Path) -> None:
    """Default render() should produce the same frame as MAIN_DASHBOARD."""
    driver = MockDisplayDriver(output_dir=tmp_path)
    renderer = Renderer(driver)

    renderer.render(_EVENTS, as_of=_NOW)
    assert driver.last_frame_path is not None
    default_bytes = driver.last_frame_path.read_bytes()

    renderer.render(_EVENTS, view=ViewKind.MAIN_DASHBOARD, as_of=_NOW)
    assert driver.last_frame_path is not None
    explicit_bytes = driver.last_frame_path.read_bytes()

    assert default_bytes == explicit_bytes


def test_main_dashboard_empty_events(tmp_path: pytest.Path) -> None:
    """Main dashboard should render without error when there are no events."""
    driver = MockDisplayDriver(output_dir=tmp_path)
    renderer = Renderer(driver)
    renderer.render([], view=ViewKind.MAIN_DASHBOARD, as_of=_NOW)
    assert driver.last_frame_path is not None
    assert driver.last_frame_path.exists()


def test_daily_agenda_no_events(tmp_path: pytest.Path) -> None:
    """Daily agenda should render empty state without error."""
    driver = MockDisplayDriver(output_dir=tmp_path)
    renderer = Renderer(driver)
    renderer.render([], view=ViewKind.DAILY_AGENDA, as_of=_NOW)
    assert driver.last_frame_path is not None


def test_mini_month_marks_event_dates(tmp_path: pytest.Path) -> None:
    """Mini month frame must not be all-white (events/today should mark pixels)."""
    from PIL import Image

    driver = MockDisplayDriver(output_dir=tmp_path)
    renderer = Renderer(driver)
    renderer.render(_EVENTS, view=ViewKind.MINI_MONTH, as_of=_NOW)
    assert driver.last_frame_path is not None
    img = Image.open(driver.last_frame_path)
    # At least some black pixels must be present (text, grid lines)
    assert min(img.tobytes()) < 128
