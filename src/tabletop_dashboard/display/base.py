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

    def display_partial(
        self,
        image: Image.Image,
        region: tuple[int, int, int, int],
    ) -> None:
        """Push a partial update for *region* = (x0, y0, x1, y1).

        Default implementation pastes the partial image onto a full white
        frame and calls :meth:`display` — effectively a full refresh.
        Hardware drivers should override this with a true partial update.
        """
        full = Image.new("L", (self.width, self.height), 255)
        full.paste(image, (region[0], region[1]))
        self.display(full)

    def close(self) -> None:  # noqa: B027
        """Optional teardown (e.g. put display to sleep). Default: no-op."""
