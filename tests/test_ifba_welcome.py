"""Runtime-level IFBA Welcome tests, enabled where system PyQt6 is available."""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "welcome"))

try:
    from PyQt6.QtWidgets import QApplication
    import ifba_welcome
except ImportError as error:
    if error.name != "PyQt6":
        raise
    QApplication = None
    ifba_welcome = None


@unittest.skipUnless(QApplication is not None, "PyQt6 is installed in the target Linux image")
class WelcomeRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication(["ifba-welcome-test"])

    def test_do_not_show_preference_is_saved_per_user(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ifba-os" / "welcome.ini"
            self.assertTrue(ifba_welcome.show_at_login(path))
            ifba_welcome.save_show_at_login(False, path)
            self.assertFalse(ifba_welcome.show_at_login(path))
            ifba_welcome.save_show_at_login(True, path)
            self.assertTrue(ifba_welcome.show_at_login(path))

    def test_window_opens_and_exposes_the_expected_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "welcome.ini"
            window = ifba_welcome.WelcomeWindow(path)
            window.show()
            self.app.processEvents()
            self.assertTrue(window.isVisible())
            self.assertIn("SUAP", window._buttons)
            self.assertIn("AVA IFBA", window._buttons)
            self.assertIn("IFBA AI", window._buttons)
            self.assertIn("Documentação", window._buttons)
            self.assertIn("Atualizações", window._buttons)
            with patch.object(ifba_welcome, "user_config_path", return_value=path):
                window.hide_at_login.setChecked(True)
                self.assertFalse(ifba_welcome.show_at_login(path))
                self.assertEqual(ifba_welcome.main(["--autostart"]), 0)
            window.close()


if __name__ == "__main__":
    unittest.main()
