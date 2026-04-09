"""Entry point for the tabletop dashboard."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from tabletop_dashboard.config import load_config
from tabletop_dashboard.display.mock import MockDisplayDriver
from tabletop_dashboard.scheduler import Scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    stream=sys.stdout,
)


def _build_driver(config_path: Path):  # type: ignore[return]
    from tabletop_dashboard.config import load_config as _lc
    cfg = _lc(config_path)

    model = cfg.display.model.lower()
    if model == "mock":
        return MockDisplayDriver(output_dir=cfg.display.mock_output_dir)

    # Hardware drivers are imported lazily so the app starts without the
    # Waveshare library installed (e.g., in CI or on non-Pi hosts).
    try:
        from tabletop_dashboard.display.waveshare import WaveshareEPDDriver  # type: ignore[import]
        return WaveshareEPDDriver(model=cfg.display.model)
    except ImportError:
        logging.warning(
            "Waveshare EPD library not found; falling back to MockDisplayDriver."
        )
        return MockDisplayDriver(output_dir=cfg.display.mock_output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Painel de Mesa e-Ink tabletop dashboard")
    parser.add_argument(
        "--config",
        default="config.toml",
        help="Path to config.toml (default: ./config.toml)",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(config_path)
    driver = _build_driver(config_path)

    scheduler = Scheduler(config, driver)
    scheduler.run()


if __name__ == "__main__":
    main()
