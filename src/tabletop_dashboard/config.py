"""Configuration loading from config.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CalendarSource:
    name: str
    url: str
    username: str = ""
    password: str = ""


@dataclass
class DisplayConfig:
    model: str = "mock"
    mock_output_dir: str = "/tmp/tabletop-dashboard"
    width: int = 800
    height: int = 480


@dataclass
class CalendarConfig:
    sources: list[CalendarSource] = field(default_factory=list)


@dataclass
class SchedulerConfig:
    refresh_interval_sec: int = 900  # how often to re-fetch calendar events


@dataclass
class ViewConfig:
    """Controls view rotation and refresh timing."""

    rotation: list[str] = field(
        default_factory=lambda: ["main_dashboard", "daily_agenda", "mini_month"]
    )
    rotation_interval_sec: int = 900  # seconds to show each view before rotating
    partial_refresh_interval_sec: int = 60  # clock/badge update interval (seconds)
    full_refresh_interval_sec: int = 3600  # anti-ghosting full refresh interval


@dataclass
class AppConfig:
    display: DisplayConfig = field(default_factory=DisplayConfig)
    calendar: CalendarConfig = field(default_factory=CalendarConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    views: ViewConfig = field(default_factory=ViewConfig)


def load_config(path: Path | str = "config.toml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        return AppConfig()

    with config_path.open("rb") as fh:
        raw = tomllib.load(fh)

    display_raw = raw.get("display", {})
    display_fields = DisplayConfig.__dataclass_fields__
    display = DisplayConfig(**{k: v for k, v in display_raw.items() if k in display_fields})

    raw_cal = raw.get("calendar", {})
    sources = [CalendarSource(**src) for src in raw_cal.get("sources", [])]
    calendar = CalendarConfig(sources=sources)

    scheduler_raw = raw.get("scheduler", {})
    sched_fields = SchedulerConfig.__dataclass_fields__
    scheduler = SchedulerConfig(**{k: v for k, v in scheduler_raw.items() if k in sched_fields})

    views_raw = raw.get("views", {})
    view_fields = ViewConfig.__dataclass_fields__
    views = ViewConfig(**{k: v for k, v in views_raw.items() if k in view_fields})

    return AppConfig(display=display, calendar=calendar, scheduler=scheduler, views=views)
