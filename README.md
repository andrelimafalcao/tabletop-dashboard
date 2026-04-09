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
the layout without hardware. Partial-refresh updates are saved as `partial_XXXX.png`.

## Hardware Setup (Raspberry Pi)

1. Enable SPI on the Pi: `sudo raspi-config` → Interface Options → SPI → Enable.
2. Install the Waveshare EPD library:
   ```bash
   git clone https://github.com/waveshare/e-Paper.git
   pip install ./e-Paper/RaspberryPi_JetsonNano/python/
   ```
3. Set `display.model` in `config.toml` to your display model (e.g. `"epd7in5_V2"`).
4. Run as a systemd service (see `deploy/` in a future release).

## Calendar Configuration

The dashboard supports any calendar reachable via **iCal URL** or **CalDAV**:

```toml
# Plain iCal feed (read-only, e.g. Google Calendar "secret address")
[[calendar.sources]]
name = "Personal"
url = "https://calendar.google.com/calendar/ical/your.ical.address/public/basic.ics"

# CalDAV (read-write capable, e.g. Fastmail, Nextcloud, iCloud)
[[calendar.sources]]
name = "Work"
url = "https://caldav.fastmail.com/dav/calendars/user/you@example.com/work/"
username = "you@example.com"
password = "app-specific-password"
```

Google Calendar iCal export URLs are available under **Settings → [calendar] → Integrate calendar → Secret address in iCal format**.

Multiple sources are supported — events from all sources are merged and sorted.

## Display Configuration

```toml
[display]
model = "mock"             # "mock" or a Waveshare model string (e.g. "epd7in5_V2")
mock_output_dir = "/tmp/tabletop-dashboard"
width = 800                # display width in pixels (default: 800)
height = 480               # display height in pixels (default: 480)
```

## View Configuration

The dashboard cycles through three views:

| View | Description |
|------|-------------|
| `main_dashboard` | Clock + next-event badge + today's event list |
| `daily_agenda` | Hourly timeline with event blocks |
| `mini_month` | Month calendar grid with event dots |

```toml
[views]
# Which views to show and in what order
rotation = ["main_dashboard", "daily_agenda", "mini_month"]

# How long to show each view (seconds)
rotation_interval_sec = 900   # 15 minutes

# How often to update the clock/badge without a full refresh (e-Ink partial update)
partial_refresh_interval_sec = 60   # every minute

# How often to force a full refresh to clear ghosting artifacts
full_refresh_interval_sec = 3600   # every hour
```

## Refresh Behaviour

- **Startup**: full refresh with the first view in the rotation.
- **Every minute**: partial refresh of the clock and next-event badge (main dashboard only, fast, no flash).
- **Every `rotation_interval_sec`**: full refresh with the next view in the rotation.
- **Every `full_refresh_interval_sec`**: forced full refresh to prevent ghosting.
- **Every `refresh_interval_sec`** (scheduler): calendar data is re-fetched from all sources.

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
├── scheduler.py      — view rotation + partial/full refresh loop
├── display/
│   ├── base.py       — DisplayDriver abstract interface
│   ├── mock.py       — MockDisplayDriver (saves PNG, no hardware)
│   ├── renderer.py   — multi-view Pillow renderer + partial refresh
│   └── views/
│       ├── __init__.py      — ViewKind enum
│       ├── main_dashboard.py — C-01…C-06, C-12, C-13, C-14
│       ├── daily_agenda.py   — C-07, C-08, C-09, C-06
│       └── mini_month.py     — C-10, C-11
└── calendar/
    ├── models.py     — CalendarEvent dataclass
    └── fetcher.py    — iCal/CalDAV fetcher
```

## License

MIT
