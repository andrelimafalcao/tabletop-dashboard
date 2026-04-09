"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from tabletop_dashboard.display.mock import MockDisplayDriver


@pytest.fixture()
def mock_driver(tmp_path):  # type: ignore[no-untyped-def]
    return MockDisplayDriver(output_dir=tmp_path)
