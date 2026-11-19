"""Static packaging contracts for the native XFCE desktop."""

import configparser
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


class DesktopPackagingTests(unittest.TestCase):
    def test_firefox_is_the_default_xfce_browser(self):
        helper_settings = (ROOT / "packaging/xfce4-helpers.rc").read_text()
        panel = ET.parse(ROOT / "packaging/xfce4-panel.xml").getroot()
        panel_values = [node.attrib.get("value") for node in panel.iter("value")]
        mime_defaults = (ROOT / "scripts/build-iso-container.sh").read_text()

        self.assertIn("WebBrowser=firefox", helper_settings)
        self.assertIn("firefox.desktop", panel_values)
        self.assertIn("x-scheme-handler/https=firefox.desktop", mime_defaults)
        self.assertNotIn("WebBrowser=netsurf", helper_settings)

    def test_firefox_desktop_entry_has_url_associations(self):
        entry = configparser.ConfigParser(interpolation=None)
        entry.read(ROOT / "packaging/firefox.desktop")
        desktop = entry["Desktop Entry"]

        self.assertEqual(desktop["Exec"], "firefox %u")
        self.assertEqual(desktop["TryExec"], "firefox")
        self.assertIn("x-scheme-handler/https", desktop["MimeType"])

    def test_assistant_identity_and_interaction_states_are_packaged(self):
        entry = configparser.ConfigParser(interpolation=None)
        entry.read(ROOT / "packaging/ifba-ai.desktop")
        css = (ROOT / "packaging/ifba-ai.css").read_text()
        ui = (ROOT / "ai/ifba_ai/ui.py").read_text()

        self.assertEqual(entry["Desktop Entry"]["Name"], "IFBA AI")
        self.assertEqual(entry["Desktop Entry"]["StartupWMClass"], "org.ifba.OS.Assistant")
        self.assertIn('title="IFBA AI"', ui)
        for selector in ("button:hover", "button:active", "button:focus", "button:disabled"):
            self.assertIn(selector, css)


if __name__ == "__main__":
    unittest.main()
