"""Icono en la barra de GNOME (AppIndicator) sin icono cargado, solo texto/números."""
import logging
import os
from datetime import datetime

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from modules.format_tools import format_pct, format_reset, level_emoji

logger = logging.getLogger(__name__)

BLANK_ICON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "blank.png"
)

try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
except (ValueError, ImportError):
    AppIndicator = None
    logger.warning(
        "AyatanaAppIndicator3 no disponible — instala "
        "gir1.2-ayatanaappindicator3-0.1 para el texto en la barra"
    )


def _quota_line(label, remaining_pct, resets_at):
    """Arma la línea de menú con círculo de estado, % y hora de reset."""
    return (
        f"{level_emoji(remaining_pct)} {label} — {format_pct(remaining_pct)}"
        f" · reset {format_reset(resets_at)}"
    )


def _format_compact_num(num: float) -> str:
    """Formatea grandes números de tokens en formato compacto (e.g. 1.2M, 450k)."""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.0f}k"
    return str(int(num))


class TokenTray:
    """Indicador minimalista en la barra superior (solo números y texto)."""

    def __init__(self, on_open, on_refresh, on_quit):
        self.on_open = on_open
        self.on_refresh = on_refresh
        self.on_quit = on_quit
        self.available = AppIndicator is not None
        if not self.available:
            return

        icon_path = BLANK_ICON_PATH if os.path.exists(BLANK_ICON_PATH) else "utilities-system-monitor"
        self._indicator = AppIndicator.Indicator.new(
            "token-dashboard",
            icon_path,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS,
        )
        if os.path.exists(BLANK_ICON_PATH):
            self._indicator.set_icon_full(BLANK_ICON_PATH, "TokenBar")

        self._indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self._indicator.set_title("TokenBar Linux")
        self._indicator.set_menu(self._build_menu([]))

    def _build_menu(self, sections, updated_at=None):
        """Construye el menú contextual."""
        menu = Gtk.Menu()

        for title, lines in sections:
            header = Gtk.MenuItem(label=f"<b>{title}</b>")
            header.get_child().set_use_markup(True)
            header.set_sensitive(False)
            menu.append(header)
            for text in lines:
                item = Gtk.MenuItem(label=text)
                item.set_sensitive(False)
                menu.append(item)
            menu.append(Gtk.SeparatorMenuItem())

        if updated_at is not None:
            updated = Gtk.MenuItem(
                label=f"Actualizado {updated_at.strftime('%H:%M:%S')}"
            )
            updated.set_sensitive(False)
            menu.append(updated)
            menu.append(Gtk.SeparatorMenuItem())

        open_item = Gtk.MenuItem(label="Abrir Dashboard completo")
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

    def update_data(self, data):
        """Actualiza la etiqueta de la barra superior (solo números y métricas)."""
        if not self.available or not data:
            return

        claude = data.get("claude_quota", {})
        antigravity = data.get("antigravity_quota", {})

        claude_lines = [
            _quota_line(w["label"], w["remaining_pct"], w["resets_at"])
            for w in claude.get("windows", [])
        ] or [f"⚠ Error: {claude.get('error', 'Sin datos')}"]

        antigravity_lines = [
            _quota_line(m["label"], m["remaining_pct"], m["resets_at"])
            for m in antigravity.get("models", [])
        ] or [f"⚠ Error: {antigravity.get('error', 'Sin datos')}"]

        today_tok_str = _format_compact_num(data.get("today_tokens", 0))
        today_cost = data.get("today_cost", 0.0)
        speed = data.get("tokens_per_min", 0.0)

        summary_lines = [
            f"⚡ Tokens Hoy: {today_tok_str} ({data.get('today_tokens', 0):,} tok)",
            f"💵 Costo Hoy: ${today_cost:.2f} USD",
            f"📈 Velocidad: {speed:.1f} tok/min",
        ]

        session = next(
            (w for w in claude.get("windows", []) if w["key"] == "five_hour"), None
        )
        if session:
            emoji = level_emoji(session["remaining_pct"])
            pct_str = format_pct(session["remaining_pct"])
            label_text = f"{emoji} {pct_str} | {today_tok_str} | ${today_cost:.2f}"
        else:
            label_text = f"⚡ {today_tok_str} | ${today_cost:.2f}"

        self._indicator.set_label(label_text, "100%")

        sections = [
            ("RESUMEN DE HOY", summary_lines),
            ("CLAUDE CODE (CUOTAS)", claude_lines),
            ("ANTIGRAVITY (CUOTAS)", antigravity_lines),
        ]

        self._indicator.set_menu(self._build_menu(sections, data.get("updated_at", datetime.now())))
