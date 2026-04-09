"""Abstract display driver interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from PIL import Image


class DisplayDriver(ABC):
    """Abstract base for e-Ink display drivers.

    Concrete implementations must supply the display's pixel dimensions and
    a method to push a rendered Pillow Image to the screen.
    """

    @property
    @abstractmethod
    def width(self) -> int:
        """Display width in pixels."""
        ...

    @property
    @abstractmethod
    def height(self) -> int:
        """Display height in pixels."""
        ...

    @abstractmethod
    def display(self, image: Image.Image) -> None:
        """Push *image* to the display (or mock output)."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear the display to white."""
        ...

    def close(self) -> None:
        """Optional teardown (e.g. put display to sleep). Default: no-op."""
