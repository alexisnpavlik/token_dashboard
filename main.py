"""Dashboard de quota restante de Claude Code y Antigravity en la barra de GNOME."""
import logging
import threading
from datetime import datetime

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from config.config import REFRESH_INTERVAL_MINUTES
from modules.antigravity_usage import get_antigravity_usage
from modules.claude_usage import get_claude_usage
from modules.dashboard_window import DashboardWindow
from modules.tray import TokenTray

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

_refreshing = False


def refresh(window, tray):
    """Lanza la consulta de quota en segundo plano y actualiza la UI."""
    global _refreshing
    if _refreshing:
        return
    _refreshing = True

    def worker():
        global _refreshing
        claude = get_claude_usage()
        antigravity = get_antigravity_usage()
        _refreshing = False

        def apply():
            window.update_data(claude, antigravity, datetime.now())
            tray.update_data(claude, antigravity)
            return False

        GLib.idle_add(apply)

    threading.Thread(target=worker, daemon=True).start()


def main():
    window = DashboardWindow()
    tray = TokenTray(
        on_open=lambda: window.present(),
        on_refresh=lambda: refresh(window, tray),
        on_quit=Gtk.main_quit,
    )
    window.on_refresh = lambda: refresh(window, tray)

    refresh(window, tray)
    GLib.timeout_add_seconds(
        REFRESH_INTERVAL_MINUTES * 60, lambda: (refresh(window, tray), True)[1]
    )

    if not tray.available:
        window.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
