"""Ventana GTK con la quota restante de Claude Code y Antigravity."""
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from modules.format_tools import format_pct, format_reset


class DashboardWindow(Gtk.Window):
    """Ventana con barras de progreso de quota restante y horas de reset."""

    def __init__(self, on_refresh=None):
        super().__init__(title="Quota — Claude Code / Antigravity")
        self.on_refresh = on_refresh
        self.set_default_size(520, 420)
        self.set_border_width(16)
        self.connect("delete-event", self._on_delete)

        self._outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(self._outer)

        self._claude_box = self._make_section("Claude Code")
        self._antigravity_box = self._make_section("Antigravity")

        self._status_label = Gtk.Label(label="", xalign=0)
        self._status_label.get_style_context().add_class("dim-label")
        self._outer.pack_end(self._status_label, False, False, 0)

        refresh_button = Gtk.Button(label="Actualizar ahora")
        refresh_button.connect("clicked", self._on_refresh_clicked)
        self._outer.pack_end(refresh_button, False, False, 0)

    def _make_section(self, title):
        """Crea una sección con encabezado y devuelve el box de contenido."""
        header = Gtk.Label(xalign=0)
        header.set_markup(f"<b>{title}</b>")
        self._outer.pack_start(header, False, False, 0)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self._outer.pack_start(box, False, False, 0)
        return box

    def _on_delete(self, *args):
        self.hide()
        return True

    def _on_refresh_clicked(self, _button):
        if self.on_refresh:
            self.on_refresh()

    def update_data(self, claude, antigravity, updated_at):
        """Redibuja las dos secciones con los datos recibidos."""
        self._fill_rows(
            self._claude_box,
            [(w["label"], w["remaining_pct"], w["resets_at"])
             for w in claude["windows"]],
            claude["error"],
        )
        self._fill_rows(
            self._antigravity_box,
            [(m["label"], m["remaining_pct"], m["resets_at"])
             for m in antigravity["models"]],
            antigravity["error"],
        )
        self._status_label.set_text(
            f"Actualizado: {updated_at.strftime('%H:%M:%S')}"
        )
        self.show_all()

    def _fill_rows(self, box, rows, error):
        """Reemplaza el contenido de una sección con filas de quota."""
        for child in box.get_children():
            box.remove(child)

        if error:
            label = Gtk.Label(label=f"Error: {error}", xalign=0)
            label.set_line_wrap(True)
            box.pack_start(label, False, False, 0)
            return

        for name, remaining_pct, resets_at in rows:
            row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            text = Gtk.Label(xalign=0)
            text.set_markup(
                f"{name} — <b>{format_pct(remaining_pct)}</b> restante"
                f"  ·  reset {format_reset(resets_at)}"
            )
            bar = Gtk.ProgressBar()
            bar.set_fraction(remaining_pct / 100.0)
            row.pack_start(text, False, False, 0)
            row.pack_start(bar, False, False, 0)
            box.pack_start(row, False, False, 0)
