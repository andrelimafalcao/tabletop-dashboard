"""Mock display driver — saves frames as PNG files instead of driving hardware."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from tabletop_dashboard.display.base import DisplayDriver


class MockDisplayDriver(DisplayDriver):
    """Saves rendered frames to *output_dir* as PNG files.

    Useful for local development and CI — no hardware required.
    """

    DEFAULT_WIDTH = 250
    DEFAULT_HEIGHT = 122

    def __init__(
        self,
        output_dir: str | Path = "/tmp/tabletop-dashboard",
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
    ) -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._width = width
        self._height = height
        self._frame_count = 0

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def display(self, image: Image.Image) -> None:
        self._frame_count += 1
        out_path = self._output_dir / f"frame_{self._frame_count:04d}.png"
        image.save(out_path)

    def clear(self) -> None:
        white = Image.new("L", (self._width, self._height), 255)
        self.display(white)

    @property
    def last_frame_path(self) -> Path | None:
        if self._frame_count == 0:
            return None
        return self._output_dir / f"frame_{self._frame_count:04d}.png"
