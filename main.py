"""Tray de quota restante de Claude Code y Antigravity en la barra de GNOME."""
import logging
import os
import subprocess
import sys
import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from config.config import REFRESH_INTERVAL_MINUTES
from modules.antigravity_usage import get_antigravity_usage
from modules.claude_usage import get_claude_usage
from modules.tray import TokenTray

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

DASHBOARD_APP_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "dashboard_app.py"
)

_refreshing = False


def open_dashboard():
    """Abre la ventana GTK4 del dashboard como proceso aparte (single-instance)."""
    subprocess.Popen([sys.executable, DASHBOARD_APP_PATH])


def refresh(tray):
    """Lanza la consulta de quota en segundo plano y actualiza el tray."""
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
            tray.update_data(claude, antigravity)
            return False

        GLib.idle_add(apply)

    threading.Thread(target=worker, daemon=True).start()


def main():
    """Arranca el tray; sin AppIndicator delega en la ventana GTK4."""
    tray = TokenTray(
        on_open=open_dashboard,
        on_refresh=lambda: refresh(tray),
        on_quit=Gtk.main_quit,
    )
    if not tray.available:
        logger.warning("Sin AppIndicator: abriendo solo la ventana GTK4")
        os.execv(sys.executable, [sys.executable, DASHBOARD_APP_PATH])

    refresh(tray)
    GLib.timeout_add_seconds(
        REFRESH_INTERVAL_MINUTES * 60, lambda: (refresh(tray), True)[1]
    )
    Gtk.main()


if __name__ == "__main__":
    main()
