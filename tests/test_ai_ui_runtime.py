"""GTK state regressions for the IFBA AI's initial and service-error screens."""

import unittest

try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    from ai.ifba_ai.ui import AssistantWindow
except (ImportError, SystemExit):
    Gtk = None
    AssistantWindow = None


@unittest.skipUnless(Gtk is not None, "GTK 3 and PyGObject are installed in the Linux target")
class AssistantUiRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = Gtk.Application(application_id="org.ifba.OS.Assistant.Test")
        cls.application.register(None)

    def setUp(self):
        self.window = AssistantWindow(self.application)
        self.window.show_all()

    def tearDown(self):
        self.window.destroy()

    def _message_text(self):
        buffer = self.window.messages_buffer
        start, end = buffer.get_bounds()
        return buffer.get_text(start, end, True)

    def test_loaded_empty_history_displays_the_chat_welcome(self):
        self.window._on_conversations_loaded([])

        self.assertEqual(self.window.stack.get_visible_child_name(), "chat")
        self.assertIn("Olá, estudante!", self._message_text())
        self.assertIn("Faça uma pergunta", self._message_text())

    def test_service_failure_displays_recovery_instead_of_an_empty_chat(self):
        self.window._on_service_error()

        self.assertEqual(self.window.stack.get_visible_child_name(), "chat")
        self.assertIn("serviço local do IFBA AI não respondeu", self._message_text())
        self.assertTrue(self.window.retry_service_button.get_visible())
        self.assertFalse(self.window.new_chat.get_sensitive())


if __name__ == "__main__":
    unittest.main()
