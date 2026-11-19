"""Static packaging contracts for the native XFCE desktop."""

import configparser
import hashlib
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


class DesktopPackagingTests(unittest.TestCase):
    def test_native_panels_have_valid_ids_and_top_bottom_positions(self):
        panel = ET.parse(ROOT / "packaging/xfce4-panel.xml").getroot()
        panels = next(node for node in panel.iter("property") if node.attrib.get("name") == "panels")
        self.assertEqual(panels.attrib["type"], "array")
        self.assertEqual([node.attrib["value"] for node in panels.findall("value")], ["1", "2"])
        panel_positions = {
            item.attrib["name"]: next(
                prop.attrib["value"] for prop in item.findall("property")
                if prop.attrib.get("name") == "position"
            )
            for item in panels.findall("property")
        }
        self.assertTrue(panel_positions["panel-1"].startswith("p=10;"))
        self.assertTrue(panel_positions["panel-2"].startswith("p=6;"))

    def test_wallpaper_sources_are_identical_and_packed_at_desktop_path(self):
        wallpaper = (ROOT / "assets/wallpapers/ifba-os-desktop.png").read_bytes()
        splash = (ROOT / "assets/plymouth/ifba-os-startup.png").read_bytes()
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        self.assertEqual(hashlib.sha256(wallpaper).digest(), hashlib.sha256(splash).digest())
        self.assertIn("/usr/share/backgrounds/ifba-os/wallpaper.png", build)
        self.assertIn("/work/assets/wallpapers/ifba-os-desktop.png", build)

    def test_live_home_permissions_and_guest_diagnostics_are_packaged(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        self.assertIn("chown -R ubuntu:ubuntu /home/ubuntu", build)
        self.assertIn('chmod 0700 "$ROOTFS/home/ubuntu/.cache"', build)
        self.assertIn("qemu-guest-agent", build)
        self.assertIn("ifba-wired.nmconnection", build)

    def test_generic_desktop_shortcuts_are_hidden_for_reference_layout(self):
        desktop = ET.parse(ROOT / "packaging/xfce4-desktop.xml").getroot()
        hidden_names = {"show-home", "show-filesystem", "show-trash"}
        hidden = {node.attrib["name"]: node.attrib.get("value")
                  for node in desktop.iter("property") if node.attrib.get("name") in hidden_names}
        self.assertEqual(hidden, {name: "false" for name in hidden_names})

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
