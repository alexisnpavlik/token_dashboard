"""Tray de monitoreo de tokens, cuotas y costos en la barra de GNOME (TokenBar Linux)."""
import logging
import os
import subprocess
import sys
import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from config.config import REFRESH_INTERVAL_MINUTES
from modules.aggregator import get_aggregated_data
from modules.server import PORT, start_server_in_background
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
    """Abre la ventana WebKitGTK Liquid Glass del dashboard (single-instance)."""
    subprocess.Popen([sys.executable, DASHBOARD_APP_PATH])


def refresh(tray):
    """Lanza la agregación de métricas en segundo plano y actualiza el tray."""
    global _refreshing
    if _refreshing:
        return
    _refreshing = True

    def worker():
        global _refreshing
        try:
            data = get_aggregated_data(max_days=90)
        except Exception as e:
            logger.error("Error agregando métricas de tokens: %s", e)
            data = None
        _refreshing = False

        def apply():
            if data:
                tray.update_data(data)
            return False

        GLib.idle_add(apply)

    threading.Thread(target=worker, daemon=True).start()


def main():
    """Arranca el servidor local y el tray de la barra superior."""
    start_server_in_background(PORT)

    tray = TokenTray(
        on_open=open_dashboard,
        on_refresh=lambda: refresh(tray),
        on_quit=Gtk.main_quit,
    )
    if not tray.available:
        logger.warning("Sin AppIndicator disponible: abriendo el Dashboard Liquid Glass")
        os.execv(sys.executable, [sys.executable, DASHBOARD_APP_PATH])

    refresh(tray)
    GLib.timeout_add_seconds(
        REFRESH_INTERVAL_MINUTES * 60, lambda: (refresh(tray), True)[1]
    )
    Gtk.main()


if __name__ == "__main__":
    main()
