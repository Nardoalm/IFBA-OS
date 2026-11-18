"""Transient, non-interactive X11 outline for a verified AT-SPI control."""

try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gdk, GLib, Gtk
except ImportError:
    Gtk = None


if Gtk is not None:
    class HighlightOverlay(Gtk.Window):
        def __init__(self, bounds, label, duration_ms=6000):
            super().__init__(type=Gtk.WindowType.TOPLEVEL)
            x, y, width, height = [int(value) for value in bounds]
            self.set_decorated(False)
            self.set_resizable(False)
            self.set_accept_focus(False)
            self.set_focus_on_map(False)
            self.set_keep_above(True)
            self.set_skip_taskbar_hint(True)
            self.set_skip_pager_hint(True)
            self.set_app_paintable(True)
            self.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
            self.target_width = max(width, 32)
            self.target_height = max(height, 32)
            self.target_window_width = max(width, 220)
            self.cancel_x = self.target_window_width - 22
            self.cancel_y = 4
            self.set_default_size(self.target_window_width, max(height, 32) + 28)
            self.move(x, y - 28)
            screen = self.get_screen()
            visual = screen.get_rgba_visual()
            if visual is not None:
                self.set_visual(visual)
            self.label = str(label)[:100]
            self.set_tooltip_text("Fechar destaque; o restante da tela continua interativo")
            self.connect("draw", self._draw)
            self.connect("realize", self._make_click_through)
            self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            self.connect("button-press-event", self._on_button_press)
            self._timeout = GLib.timeout_add(duration_ms, self._expire)
            self.show_all()

        def _make_click_through(self, *_args):
            window = self.get_window()
            if window is not None:
                window.set_override_redirect(True)
                try:
                    cairo = __import__("cairo")
                    region = cairo.Region()
                    region.union_rectangle(cairo.RectangleInt(self.cancel_x, self.cancel_y, 18, 18))
                    window.input_shape_combine_region(region, 0, 0)
                except Exception:
                    pass

        def _draw(self, _widget, cr):
            cr.set_source_rgba(0.18, 0.82, 0.35, 0.16)
            cr.rectangle(2, 28, max(0, self.target_width - 4), max(0, self.target_height - 4))
            cr.fill_preserve()
            cr.set_source_rgba(0.22, 0.94, 0.42, 0.96)
            cr.set_line_width(3)
            cr.stroke()
            cr.select_font_face("Inter", 0, 1)
            cr.set_font_size(12)
            cr.set_source_rgba(1, 1, 1, 0.98)
            cr.move_to(6, 20)
            cr.show_text(self.label[:24])
            cr.move_to(self.cancel_x + 4, self.cancel_y + 14)
            cr.show_text("×")
            return False

        def _on_button_press(self, _widget, event):
            if (self.cancel_x <= event.x <= self.cancel_x + 18
                    and self.cancel_y <= event.y <= self.cancel_y + 18):
                self.destroy()
                return True
            return False

        def _expire(self):
            self.destroy()
            return False

        def cancel(self):
            if self._timeout:
                GLib.source_remove(self._timeout)
                self._timeout = None
            self.destroy()
else:
    class HighlightOverlay:
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError("A sobreposição requer GTK 3.")
