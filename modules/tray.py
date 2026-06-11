"""Icono en la barra de GNOME (AppIndicator) con resumen de quota."""
import logging
from datetime import datetime

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from modules.format_tools import format_pct, format_reset, level_emoji

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


def _quota_line(label, remaining_pct, resets_at):
    """Arma la línea de menú con círculo de estado, % y hora de reset."""
    return (
        f"{level_emoji(remaining_pct)} {label} — {format_pct(remaining_pct)}"
        f" · reset {format_reset(resets_at)}"
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
        self._indicator.set_menu(self._build_menu([]))

    def _build_menu(self, sections, updated_at=None):
        """Construye el menú: secciones (título, líneas) de quota + acciones."""
        menu = Gtk.Menu()

        for title, lines in sections:
            header = Gtk.MenuItem(label=title)
            header.set_sensitive(False)
            menu.append(header)
            for text in lines:
                item = Gtk.MenuItem(label=text)
                item.set_sensitive(False)
                menu.append(item)
            menu.append(Gtk.SeparatorMenuItem())

        if updated_at is not None:
            updated = Gtk.MenuItem(
                label=f"Actualizado {updated_at.strftime('%H:%M')}"
            )
            updated.set_sensitive(False)
            menu.append(updated)
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
            _quota_line(w["label"], w["remaining_pct"], w["resets_at"])
            for w in claude["windows"]
        ] or [f"⚠ Error: {claude['error']}"]

        antigravity_lines = [
            _quota_line(m["label"], m["remaining_pct"], m["resets_at"])
            for m in antigravity["models"]
        ] or [f"⚠ Error: {antigravity['error']}"]

        session = next(
            (w for w in claude["windows"] if w["key"] == "five_hour"), None
        )
        if session:
            label = (
                f"{level_emoji(session['remaining_pct'])} "
                f"{format_pct(session['remaining_pct'])}"
            )
        else:
            label = "⚠"
        self._indicator.set_label(label, "🟢 100%")

        self._indicator.set_menu(self._build_menu(
            [("CLAUDE CODE", claude_lines), ("ANTIGRAVITY", antigravity_lines)],
            datetime.now(),
        ))
