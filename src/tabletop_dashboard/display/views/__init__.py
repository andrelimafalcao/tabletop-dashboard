"""View kinds for the tabletop dashboard."""

from __future__ import annotations

from enum import StrEnum


class ViewKind(StrEnum):
    """The three display views supported by the renderer."""

    MAIN_DASHBOARD = "main_dashboard"
    DAILY_AGENDA = "daily_agenda"
    MINI_MONTH = "mini_month"
