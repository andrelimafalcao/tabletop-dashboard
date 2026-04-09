# Painel de Mesa — e-Ink Tabletop Dashboard

A Raspberry Pi-powered e-Ink tabletop display that shows your upcoming calendar events at a glance.

## Requirements

- Python 3.11+
- Raspberry Pi Zero 2 W (or any Pi with SPI/GPIO)
- Waveshare e-Paper display (or run in `mock` mode for development without hardware)

## Quick Start (local / mock mode)

```bash
# 1. Clone the repo
git clone https://github.com/andrelimafalcao/tabletop-dashboard.git
cd tabletop-dashboard

# 2. Create a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 3. Install the package and dev dependencies
pip install -e ".[dev]"

# 4. Copy and edit the config
cp config.example.toml config.toml
$EDITOR config.toml   # set your calendar URL(s)

# 5. Run (mock mode — saves PNG frames to /tmp/tabletop-dashboard/)
tabletop-dashboard --config config.toml
```

Mock mode is the default (`display.model = "mock"` in `config.toml`). Each refresh cycle
saves a `frame_XXXX.png` to the configured `mock_output_dir` directory so you can preview
the layout without hardware.

## Hardware Setup (Raspberry Pi)

1. Enable SPI on the Pi: `sudo raspi-config` → Interface Options → SPI → Enable.
2. Install the Waveshare EPD library:
   ```bash
   git clone https://github.com/waveshare/e-Paper.git
   pip install ./e-Paper/RaspberryPi_JetsonNano/python/
   ```
3. Set `display.model` in `config.toml` to your display model (e.g. `"epd2in13_V4"`).
4. Run as a systemd service (see `deploy/` in a future release).

## Calendar Configuration

The dashboard supports any calendar reachable via **iCal URL** or **CalDAV**:

```toml
[[calendar.sources]]
name = "Personal"
url = "https://calendar.google.com/calendar/ical/..."   # iCal export URL

[[calendar.sources]]
name = "Work (CalDAV)"
url = "https://caldav.example.com/dav/calendars/user/you@example.com/work/"
username = "you@example.com"
password = "app-specific-password"
```

Google Calendar iCal export URLs are available under **Settings → [calendar] → Integrate calendar → Secret address in iCal format**.

## Running Tests

```bash
pytest
```

Coverage is gated at 80%. The full report is printed to the terminal.

## Linting & Type Checking

```bash
ruff check src/ tests/      # linting
mypy src/                   # static type analysis
```

## Project Structure

```
src/tabletop_dashboard/
├── main.py           — CLI entry point
├── config.py         — TOML configuration loader
├── scheduler.py      — fetch → render → sleep loop
├── display/
│   ├── base.py       — DisplayDriver abstract interface
│   ├── mock.py       — MockDisplayDriver (saves PNG, no hardware)
│   └── renderer.py   — Pillow-based frame composer
└── calendar/
    ├── models.py     — CalendarEvent dataclass
    └── fetcher.py    — iCal/CalDAV fetcher
```

## License

MIT
