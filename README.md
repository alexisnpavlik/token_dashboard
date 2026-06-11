# Token Dashboard

> GNOME system tray applet that shows remaining quota for **Claude Code** and **Antigravity** in real time.

![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Linux%20%E2%80%A2%20GNOME-orange?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

## Overview

Token Dashboard sits in the GNOME top bar and keeps your AI quota visible at a glance:

- **Tray label** — session percentage updated every 5 minutes
- **Dropdown menu** — per-window / per-model breakdown with next reset time
- **GTK4 / libadwaita window** — native GNOME look, automatic dark/light theme, colour-coded progress bars (green / orange / red by remaining quota)

No external Python dependencies. All data comes from credentials already on disk.

---

## Data Sources

| Service | Source |
|---|---|
| **Claude Code** | `GET https://api.anthropic.com/api/oauth/usage` authenticated with `~/.claude/.credentials.json` |
| **Antigravity** | `antigravity-usage quota --json` (CLI must be in `$PATH`) |

Tracked Claude windows: **5-hour session**, **7-day rolling**, **7-day Opus**, **7-day Sonnet**.

---

## Requirements

**Ubuntu / Debian**

```bash
sudo apt install gir1.2-ayatanaappindicator3-0.1
```

PyGObject, GTK 3/4 and libadwaita (`gir1.2-adw-1`) ship with Ubuntu by default. No `pip install` is required.

---

## Installation

```bash
git clone https://github.com/alexisnpavlik/token_dashboard.git
cd token_dashboard
python3 main.py
```

### Autostart on login

```bash
cp token-dashboard.desktop ~/.config/autostart/
```

---

## Configuration

Behaviour is controlled entirely via environment variables. The defaults work without any setup.

| Variable | Default | Description |
|---|---|---|
| `REFRESH_INTERVAL_MINUTES` | `5` | Polling interval |
| `CLAUDE_CREDENTIALS_PATH` | `~/.claude/.credentials.json` | Claude Code OAuth credentials |
| `CLAUDE_USAGE_URL` | `https://api.anthropic.com/api/oauth/usage` | Usage API endpoint |
| `ANTIGRAVITY_USAGE_BIN` | `antigravity-usage` | Antigravity CLI binary |

**Example — faster refresh:**

```bash
REFRESH_INTERVAL_MINUTES=2 python3 main.py
```

---

## Project Structure

```
token_dashboard/
├── config/
│   └── config.py              # Environment variable bindings
├── modules/
│   ├── claude_usage.py        # Claude Code quota via OAuth API
│   ├── antigravity_usage.py   # Antigravity quota via CLI
│   ├── tray.py                # GNOME AppIndicator tray icon (GTK3)
│   └── format_tools.py        # Percentage / time formatters
├── main.py                    # Entry point — resident tray process
├── dashboard_app.py           # GTK4 + libadwaita window (single-instance)
└── token-dashboard.desktop    # XDG autostart descriptor
```

---

## How It Works

The app runs as **two processes**, because `AyatanaAppIndicator3` (tray) requires GTK 3 while libadwaita requires GTK 4 — they cannot share a process:

1. **`main.py`** is the resident tray process. On startup (and every `REFRESH_INTERVAL_MINUTES`) a background thread polls both data sources and updates the tray label and menu via `GLib.idle_add`.
2. **"Abrir dashboard"** spawns `dashboard_app.py` — a GTK4 + libadwaita app with a fixed application id, so it is single-instance: relaunching it just presents the existing window.
3. The window polls on its own with the same interval and shows colour-coded rows (green ≥ 50 %, orange ≥ 20 %, red < 20 %).
4. If `AyatanaAppIndicator3` is not installed, `main.py` replaces itself with the GTK4 window as a fallback.

---

## License

[MIT](LICENSE)
