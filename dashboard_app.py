"""Ventana GTK4 + libadwaita con la quota restante de Claude Code y Antigravity."""
import logging
import sys
import threading
from datetime import datetime

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk

from config.config import REFRESH_INTERVAL_MINUTES
from modules.antigravity_usage import get_antigravity_usage
from modules.claude_usage import get_claude_usage
from modules.format_tools import format_pct, format_reset, quota_level

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

APP_ID = "io.github.alexisnpavlik.TokenDashboard"

CSS = """
.pct-label { font-weight: 700; }
.pct-good  { color: #2ec27e; }
.pct-warn  { color: #e5a50a; }
.pct-alert { color: #ff7800; }
.pct-low   { color: #e01b24; }
progressbar trough, progressbar progress { min-height: 8px; border-radius: 4px; }
progressbar.good progress  { background-color: #2ec27e; }
progressbar.warn progress  { background-color: #e5a50a; }
progressbar.alert progress { background-color: #ff7800; }
progressbar.low progress   { background-color: #e01b24; }
"""


class QuotaWindow(Adw.ApplicationWindow):
    """Ventana con tarjetas Adwaita de quota restante y horas de reset."""

    def __init__(self, app):
        super().__init__(application=app, title="Quota")
        self.set_default_size(420, 540)
        self._refreshing = False

        self._spinner = Gtk.Spinner()
        self._spinner.set_visible(False)
        self._refresh_button = Gtk.Button(icon_name="view-refresh-symbolic")
        self._refresh_button.set_tooltip_text("Actualizar ahora")
        self._refresh_button.connect("clicked", lambda *_: self.refresh())

        header = Adw.HeaderBar()
        header.set_title_widget(
            Adw.WindowTitle(title="Quota", subtitle="Claude Code · Antigravity")
        )
        header.pack_start(self._refresh_button)
        header.pack_start(self._spinner)

        self._claude_group = Adw.PreferencesGroup(title="Claude Code")
        self._antigravity_group = Adw.PreferencesGroup(title="Antigravity")
        self._claude_rows = []
        self._antigravity_rows = []

        self._status_label = Gtk.Label(label="Cargando…")
        self._status_label.add_css_class("caption")
        self._status_label.add_css_class("dim-label")

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        content.set_margin_top(18)
        content.set_margin_bottom(18)
        content.set_margin_start(18)
        content.set_margin_end(18)
        content.append(self._claude_group)
        content.append(self._antigravity_group)
        content.append(self._status_label)

        clamp = Adw.Clamp(maximum_size=560, child=content)
        scrolled = Gtk.ScrolledWindow(child=clamp)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        view = Adw.ToolbarView(content=scrolled)
        view.add_top_bar(header)
        self.set_content(view)

    def refresh(self):
        """Lanza la consulta de quota en segundo plano y redibuja la ventana."""
        if self._refreshing:
            return
        self._refreshing = True
        self._refresh_button.set_sensitive(False)
        self._spinner.set_visible(True)
        self._spinner.start()

        def worker():
            claude = get_claude_usage()
            antigravity = get_antigravity_usage()

            def apply():
                self._refreshing = False
                self._refresh_button.set_sensitive(True)
                self._spinner.stop()
                self._spinner.set_visible(False)
                self._fill_group(
                    self._claude_group,
                    [(w["label"], w["remaining_pct"], w["resets_at"])
                     for w in claude["windows"]],
                    self._claude_rows,
                    claude["error"],
                )
                self._fill_group(
                    self._antigravity_group,
                    [(m["label"], m["remaining_pct"], m["resets_at"])
                     for m in antigravity["models"]],
                    self._antigravity_rows,
                    antigravity["error"],
                )
                if antigravity.get("email"):
                    self._antigravity_group.set_description(antigravity["email"])
                self._status_label.set_text(
                    f"Actualizado {datetime.now().strftime('%H:%M:%S')}"
                )
                return False

            GLib.idle_add(apply)

        threading.Thread(target=worker, daemon=True).start()

    def _fill_group(self, group, rows, tracked, error):
        """Reemplaza las filas de un grupo con los datos recibidos."""
        for row in tracked:
            group.remove(row)
        tracked.clear()

        if error:
            row = Adw.ActionRow(title="Error", subtitle=error)
            row.set_subtitle_lines(0)
            tracked.append(row)
            group.add(row)
            return

        for name, remaining_pct, resets_at in rows:
            row = self._quota_row(name, remaining_pct, resets_at)
            tracked.append(row)
            group.add(row)

    def _quota_row(self, name, remaining_pct, resets_at):
        """Crea una fila con nombre, % coloreado, barra y hora de reset."""
        level = quota_level(remaining_pct)

        name_label = Gtk.Label(label=name, xalign=0, hexpand=True)
        pct_label = Gtk.Label(label=format_pct(remaining_pct))
        pct_label.add_css_class("pct-label")
        pct_label.add_css_class(f"pct-{level}")
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top.append(name_label)
        top.append(pct_label)

        bar = Gtk.ProgressBar(fraction=remaining_pct / 100.0)
        bar.add_css_class(level)

        reset_label = Gtk.Label(label=f"reset {format_reset(resets_at)}", xalign=0)
        reset_label.add_css_class("caption")
        reset_label.add_css_class("dim-label")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(14)
        box.set_margin_end(14)
        box.append(top)
        box.append(bar)
        box.append(reset_label)

        row = Adw.PreferencesRow(activatable=False)
        row.set_child(box)
        return row


class QuotaApp(Adw.Application):
    """Aplicación single-instance del dashboard de quota."""

    def __init__(self):
        super().__init__(application_id=APP_ID)
        self._window = None

    def do_activate(self):
        """Crea la ventana en el primer activate; después solo la presenta."""
        if self._window is None:
            self._apply_css()
            self._window = QuotaWindow(self)
            self._window.refresh()
            GLib.timeout_add_seconds(
                REFRESH_INTERVAL_MINUTES * 60,
                lambda: (self._window.refresh(), True)[1],
            )
        self._window.present()

    def _apply_css(self):
        """Carga el CSS de colores de estado para toda la app."""
        provider = Gtk.CssProvider()
        provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )


def main():
    """Punto de entrada de la ventana del dashboard."""
    app = QuotaApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
