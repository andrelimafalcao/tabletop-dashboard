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


@dataclass
class CalendarConfig:
    sources: list[CalendarSource] = field(default_factory=list)


@dataclass
class SchedulerConfig:
    refresh_interval_sec: int = 900


@dataclass
class AppConfig:
    display: DisplayConfig = field(default_factory=DisplayConfig)
    calendar: CalendarConfig = field(default_factory=CalendarConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)


def load_config(path: Path | str = "config.toml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        return AppConfig()

    with config_path.open("rb") as fh:
        raw = tomllib.load(fh)

    display = DisplayConfig(**raw.get("display", {}))

    raw_cal = raw.get("calendar", {})
    sources = [
        CalendarSource(**src) for src in raw_cal.get("sources", [])
    ]
    calendar = CalendarConfig(sources=sources)

    scheduler = SchedulerConfig(**raw.get("scheduler", {}))

    return AppConfig(display=display, calendar=calendar, scheduler=scheduler)
