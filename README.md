# TokenBar Linux (Token Dashboard)

> Powerful Linux system tray applet & GTK4/Adwaita dashboard for monitoring AI token usage, costs ($ USD), session quotas, and activity heatmaps across AI coding agents. Inspired by **[Nanako0129/TokenBar](https://github.com/Nanako0129/TokenBar)**.

![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Linux%20%E2%80%A2%20GNOME%20%E2%80%A2%20KDE-orange?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

## Overview

**TokenBar Linux** sits in your top status bar and gives you complete local visibility over your AI token usage, estimated spend, and quota limits:

- **GNOME / KDE Status Tray** — Shows real-time session quota %, today's total tokens, estimated cost ($ USD), and live token velocity (`tokens/min`).
- **Multi-Agent Local Parsing** — Automatically scans local session logs without telemetry or external servers. Supports **Claude Code**, **Antigravity / Gemini CLI**, **Cursor**, **Aider**, and **Roo Code / Cline**.
- **90-Day Contribution Heatmap** — GitHub-style activity grid mapping your daily AI token burn and costs.
- **Model & Agent Rankings** — Interactive breakdown showing percentage share, token totals, and estimated costs per AI model (Claude 3.7 Sonnet, Gemini 3.6 Flash, GPT-4o, etc.).
- **Activity Lenses** — Hourly and daily distribution graphs to track peak coding hours.
- **Quota Tracking** — Real-time 5-hour session reset timers, 7-day rolling window limits, and model quotas.

---

## Supported AI Agents & Sources

| Agent | Log / Quota Source |
|---|---|
| **Claude Code** | OAuth Quota API (`~/.claude/.credentials.json`) + JSONL session logs (`~/.claude/projects/`) |
| **Antigravity / Gemini CLI** | `antigravity-usage quota --json` + local session logs (`~/.gemini/`) |
| **Cursor** | SQLite state databases (`~/.config/Cursor/User/`) |
| **Aider** | Chat history files (`.aider.chat.history.md`) |
| **Roo Code / Cline** | Extension task logs (`~/.config/Code/User/globalStorage/`) |

---

## Requirements

**Ubuntu / Debian / Fedora / Arch:**

```bash
sudo apt install gir1.2-ayatanaappindicator3-0.1 gir1.2-adw-1
```

PyGObject, GTK 3/4 and libadwaita ship with most modern Linux distros by default. No external `pip` dependencies are required.

---

## Installation & Running

```bash
git clone https://github.com/alexisnpavlik/token_dashboard.git
cd token_dashboard
python3 main.py
```

### Launching Standalone Dashboard UI

If you want to open the GTK4 / LibAdwaita window directly:

```bash
python3 dashboard_app.py
```

### Autostart on Login

```bash
cp token-dashboard.desktop ~/.config/autostart/
```

---

## Project Structure

```
token_dashboard/
├── config/
│   └── config.py              # Log paths & environment variables
├── modules/
│   ├── pricing.py             # Model pricing database ($/1M tokens) & cost calculator
│   ├── aggregator.py          # Multi-agent metric consolidation, heatmap & velocity engine
│   ├── format_tools.py        # Percentage, time & status formatters
│   ├── tray.py                # AppIndicator top bar status tray (GTK3)
│   └── parsers/               # Local session log scrapers
│       ├── claude_parser.py
│       ├── antigravity_parser.py
│       ├── cursor_parser.py
│       ├── aider_parser.py
│       └── roo_cline_parser.py
├── main.py                    # Resident tray applet controller
├── dashboard_app.py           # GTK4 + LibAdwaita multi-tab GUI dashboard
└── token-dashboard.desktop    # XDG autostart descriptor
```

---

## Configuration

Control behavior via environment variables or default settings:

| Variable | Default | Description |
|---|---|---|
| `REFRESH_INTERVAL_MINUTES` | `5` | Background polling interval |
| `CLAUDE_CREDENTIALS_PATH` | `~/.claude/.credentials.json` | Claude Code OAuth credentials |
| `CLAUDE_LOGS_DIR` | `~/.claude` | Claude Code project logs |
| `ANTIGRAVITY_LOGS_DIR` | `~/.gemini` | Antigravity logs directory |

---

## License

[MIT](LICENSE)
