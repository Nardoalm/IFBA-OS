"""Static packaging contracts for the native desktop builds."""

import configparser
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


class DesktopPackagingTests(unittest.TestCase):
    def test_native_panel_has_only_the_bottom_panel_and_no_workspace_pager(self):
        panel = ET.parse(ROOT / "packaging/xfce4-panel.xml").getroot()
        panels = next(node for node in panel.iter("property") if node.attrib.get("name") == "panels")
        self.assertEqual(panels.attrib["type"], "array")
        self.assertEqual([node.attrib["value"] for node in panels.findall("value")], ["1"])
        panel1 = panels.find("property[@name='panel-1']")
        self.assertTrue(panel1.find("property[@name='position']").attrib["value"].startswith("p=10;"))
        self.assertIsNone(panels.find("property[@name='panel-2']"))
        self.assertNotIn("15", [node.attrib["value"] for node in panel1.find("property[@name='plugin-ids']").findall("value")])

    def test_wallpaper_and_splash_are_copied_to_their_own_runtime_paths(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        self.assertIn("/usr/share/backgrounds/ifba-os/wallpaper.png", build)
        self.assertIn("/work/assets/wallpapers/ifba-os-desktop.png", build)
        self.assertIn("/usr/share/plymouth/themes/ifba-os/", build)
        self.assertIn("/work/assets/plymouth/ifba-os-startup.png", build)

    def test_live_home_permissions_and_guest_diagnostics_are_packaged(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        self.assertIn("chown -R ubuntu:ubuntu /home/ubuntu", build)
        self.assertIn('"$ROOTFS/home/ubuntu/.cache/ifba-ai"', build)
        self.assertIn('"$ROOTFS/etc/skel/.cache/ifba-ai"', build)
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
        mime_defaults = (ROOT / "scripts/build-iso-xfce4-legacy-container.sh").read_text()

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

    def test_assistant_view_transitions_default_to_no_animation(self):
        ui = (ROOT / "ai/ifba_ai/ui.py").read_text()
        self.assertIn("Gtk.StackTransitionType.NONE", ui)
        self.assertIn("self.stack.set_transition_duration(0)", ui)
        self.assertNotIn("Gtk.StackTransitionType.CROSSFADE", ui)

    def test_assistant_service_activation_does_not_block_initial_window(self):
        ui = (ROOT / "ai/ifba_ai/ui.py").read_text()
        self.assertIn("self.proxy.GetStatus(\n                reply_handler=self._on_service_status", ui)
        self.assertIn("self.proxy.GetSettings(\n                reply_handler=self._on_settings_loaded", ui)
        self.assertIn("self.proxy.ListConversations(\n                reply_handler=self._on_conversations_loaded", ui)
        self.assertIn("error_handler=self._on_service_error", ui)
        self.assertIn("timeout=5", ui)
        self.assertIn("self.status.set_text(\"O assistente abriu, mas o serviço local não respondeu.", ui)

    def test_assistant_relaunch_activates_the_existing_window(self):
        ui = (ROOT / "ai/ifba_ai/ui.py").read_text()
        self.assertIn("Gio.ApplicationFlags.HANDLES_COMMAND_LINE", ui)
        self.assertIn("def do_command_line(self, command_line):", ui)
        self.assertIn("window = self.get_active_window()", ui)
        self.assertIn("window.present()", ui)
        self.assertIn("traceback.print_exc(file=sys.stderr)", ui)

    def test_iso_build_uses_active_kernel_and_initrd_symlinks(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        self.assertIn('cp -L "$ROOTFS/boot/vmlinuz" "$ISO/casper/vmlinuz"', build)
        self.assertIn('cp -L "$ROOTFS/boot/initrd.img" "$ISO/casper/initrd"', build)
        self.assertNotIn('cp "$ROOTFS/boot/vmlinuz-"*', build)
        self.assertNotIn('cp "$ROOTFS/boot/initrd.img-"*', build)

    def test_plasma_builder_uses_only_ubuntu_26_04_desktop_components(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        layout = (ROOT / "packaging/plasma/ifba-os/contents/layouts/org.kde.plasma.desktop-layout.js").read_text()
        defaults = (ROOT / "packaging/plasma/ifba-os/contents/defaults").read_text()
        metadata = json.loads((ROOT / "packaging/plasma/ifba-os/metadata.json").read_text())
        for package in (
            "plasma-desktop",
            "plasma-session-wayland",
            "plasma-session-x11",
            "kwin-x11",
            "sddm",
            "dolphin",
            "konsole",
            "plasma-discover",
            "plasma-nm",
            "plasma-pa",
            "systemsettings",
        ):
            self.assertIn(package, build)
        self.assertIn('debootstrap --arch="$IFBA_ARCH" resolute', build)
        self.assertIn("IFBA-OS-Dark.colors", build)
        self.assertIn("IFBA OS Dark", build)
        self.assertIn("org.ifbaos.desktop", build)
        self.assertEqual(metadata["KPackageStructure"], "Plasma/LookAndFeel")
        self.assertEqual(metadata["KPlugin"]["Id"], "org.ifbaos.desktop")
        self.assertIn("panel.floating = true", layout)
        for widget in ("org.kde.plasma.kickoff", "org.kde.plasma.icontasks",
                       "org.kde.plasma.systemtray", "org.kde.plasma.digitalclock"):
            self.assertIn(widget, layout)
        self.assertIn("LookAndFeelPackage=org.ifbaos.desktop", defaults)
        setup = (ROOT / "packaging/plasma/ifba-os-session-setup").read_text()
        self.assertIn('marker="$HOME/.config/ifba-os/plasma-layout-applied"', setup)
        self.assertIn('touch "$marker"', setup)
        self.assertIn("plasma-apply-lookandfeel --apply org.ifbaos.desktop", setup)
        self.assertIn("plasma-apply-wallpaperimage /usr/share/backgrounds/ifba-os/wallpaper.png", setup)
        self.assertIn("Session=plasmax11.desktop", build)
        self.assertIn("/lib/systemd/system/sddm.service", build)
        self.assertNotIn("xfce4-session", build)
        self.assertNotIn("lightdm", build.lower())


if __name__ == "__main__":
    unittest.main()
