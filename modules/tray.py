"""Icono en la barra de GNOME (AppIndicator) con resumen de quota."""
import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from modules.format_tools import format_pct, format_reset

logger = logging.getLogger(__name__)

try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
except (ValueError, ImportError):
    AppIndicator = None
    logger.warning(
        "AyatanaAppIndicator3 no disponible — instala "
        "gir1.2-ayatanaappindicator3-0.1 para el icono en la barra"
    )


class TokenTray:
    """Indicador en la barra: % de sesión en la etiqueta y menú con detalle."""

    def __init__(self, on_open, on_refresh, on_quit):
        self.on_open = on_open
        self.on_refresh = on_refresh
        self.on_quit = on_quit
        self.available = AppIndicator is not None
        if not self.available:
            return

        self._indicator = AppIndicator.Indicator.new(
            "token-dashboard",
            "utilities-system-monitor",
            AppIndicator.IndicatorCategory.APPLICATION_STATUS,
        )
        self._indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self._indicator.set_title("Quota Claude Code / Antigravity")
        self._indicator.set_menu(self._build_menu([], []))

    def _build_menu(self, claude_lines, antigravity_lines):
        """Construye el menú con las líneas de quota recibidas."""
        menu = Gtk.Menu()

        for text in claude_lines + (["—"] if antigravity_lines else []) \
                + antigravity_lines:
            if text == "—":
                menu.append(Gtk.SeparatorMenuItem())
                continue
            item = Gtk.MenuItem(label=text)
            item.set_sensitive(False)
            menu.append(item)

        if claude_lines or antigravity_lines:
            menu.append(Gtk.SeparatorMenuItem())

        open_item = Gtk.MenuItem(label="Abrir dashboard")
        open_item.connect("activate", lambda *_: self.on_open())
        menu.append(open_item)

        refresh_item = Gtk.MenuItem(label="Actualizar ahora")
        refresh_item.connect("activate", lambda *_: self.on_refresh())
        menu.append(refresh_item)

        menu.append(Gtk.SeparatorMenuItem())
        quit_item = Gtk.MenuItem(label="Salir")
        quit_item.connect("activate", lambda *_: self.on_quit())
        menu.append(quit_item)

        menu.show_all()
        return menu

    def update_data(self, claude, antigravity):
        """Actualiza etiqueta y menú con la quota actual."""
        if not self.available:
            return

        claude_lines = [
            f"Claude {w['label']}: {format_pct(w['remaining_pct'])} "
            f"· reset {format_reset(w['resets_at'])}"
            for w in claude["windows"]
        ] or [f"Claude: error ({claude['error']})"]

        antigravity_lines = [
            f"AG {m['label']}: {format_pct(m['remaining_pct'])} "
            f"· reset {format_reset(m['resets_at'])}"
            for m in antigravity["models"]
        ] or [f"Antigravity: error ({antigravity['error']})"]

        session = next(
            (w for w in claude["windows"] if w["key"] == "five_hour"), None
        )
        label = format_pct(session["remaining_pct"]) if session else "?"
        self._indicator.set_label(label, "100%")

        self._indicator.set_menu(
            self._build_menu(claude_lines, antigravity_lines)
        )
