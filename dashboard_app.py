"""Ventana nativa WebKitGTK para TokenBar Linux (Liquid Glass Interface)."""
import logging
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("WebKit2", "4.1")

from gi.repository import Gdk, GLib, Gtk, WebKit2

from modules.server import PORT, start_server_in_background

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

DASHBOARD_URL = f"http://127.0.0.1:{PORT}"


class LiquidGlassWindow(Gtk.Window):
    """Ventana nativa con vista web WebKitGTK Liquid Glass."""

    def __init__(self):
        super().__init__(title="TokenBar — Liquid Glass")
        self.set_default_size(840, 720)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Iniciar servidor local en segundo plano
        start_server_in_background(PORT)

        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title("TokenBar")
        header.set_subtitle("Linux Liquid Glass Edition")

        refresh_btn = Gtk.Button()
        refresh_btn.set_tooltip_text("Actualizar datos")
        icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        refresh_btn.set_image(icon)
        refresh_btn.connect("clicked", lambda *_: self._webview.reload())
        header.pack_start(refresh_btn)

        self.set_titlebar(header)

        # WebKit WebView
        self._webview = WebKit2.WebView()
        self._webview.load_uri(DASHBOARD_URL)

        # Fondo transparente / oscuro glassmorphic
        bg_color = Gdk.RGBA()
        bg_color.parse("rgba(11, 15, 25, 0.95)")
        self._webview.set_background_color(bg_color)

        self.add(self._webview)
        self.show_all()
        self.connect("destroy", Gtk.main_quit)


def main():
    start_server_in_background(PORT)
    win = LiquidGlassWindow()
    Gtk.main()


if __name__ == "__main__":
    main()
