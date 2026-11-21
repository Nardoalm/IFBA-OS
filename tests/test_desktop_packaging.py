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
        self.assertNotIn('mksquashfs "$ROOTFS" "$ISO/casper/filesystem.squashfs" -comp xz -b 1M -processors "$(nproc)" -e boot', build)

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
        self.assertIn('topPanel.location = "top"', layout)
        self.assertIn('dock.location = "bottom"', layout)
        self.assertIn('dock.lengthMode = "fit"', layout)
        self.assertIn('dock.alignment = "center"', layout)
        self.assertIn('dock.floating = true', layout)
        self.assertIn('dock.hiding = "autohide"', layout)
        self.assertIn('org.kde.plasma.icontasks', layout)
        for favorite in ("firefox.desktop", "org.kde.dolphin.desktop", "org.kde.konsole.desktop",
                         "ifba-ai.desktop", "systemsettings.desktop"):
            self.assertIn(favorite, layout)
        for widget in ("org.kde.plasma.kickoff", "org.kde.plasma.icontasks",
                       "org.kde.plasma.systemtray", "org.kde.plasma.digitalclock",
                       "org.kde.plasma.panelspacer"):
            self.assertIn(widget, layout)
        self.assertIn("LookAndFeelPackage=org.ifbaos.desktop", defaults)
        self.assertIn("[kwinrc][Desktops]\nNumber=1", defaults)
        self.assertIn("ButtonsOnLeft=MXIA", defaults)
        self.assertIn("AnimationSpeed=2", defaults)
        self.assertIn("[kwinrc][Effect-Overview]", defaults)
        setup = (ROOT / "packaging/plasma/ifba-os-session-setup").read_text()
        self.assertIn('marker="$HOME/.config/ifba-os/plasma-layout-applied"', setup)
        self.assertIn('touch "$marker"', setup)
        self.assertIn("plasma-apply-lookandfeel --apply org.ifbaos.desktop", setup)
        self.assertIn("plasma-apply-wallpaperimage /usr/share/backgrounds/ifba-os/wallpaper.png", setup)
        self.assertIn("Session=plasmax11.desktop", build)
        self.assertIn("/lib/systemd/system/sddm.service", build)
        self.assertNotIn("xfce4-session", build)
        self.assertNotIn("lightdm", build.lower())

    def test_calamares_is_configured_for_uefi_manual_partitions_and_safe_user_setup(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        settings = (ROOT / "packaging/calamares/settings.conf").read_text()
        partition = (ROOT / "packaging/calamares/partition.conf").read_text()
        users = (ROOT / "packaging/calamares/users.conf").read_text()
        cleanup = (ROOT / "packaging/calamares/shellprocess.conf").read_text()
        bootloader = (ROOT / "packaging/calamares/bootloader.conf").read_text()
        removeuser = (ROOT / "packaging/calamares/removeuser.conf").read_text()
        launcher = (ROOT / "packaging/ifba-os-installer").read_text()
        desktop = configparser.ConfigParser(interpolation=None)
        desktop.read(ROOT / "packaging/ifba-os-installer.desktop")

        self.assertIn("prompt-install: true", settings)
        self.assertIn("initialPartitioningChoice: none", partition)
        self.assertIn("allowManualPartitioning: true", partition)
        self.assertIn("alwaysShowPartitionLabels: true", partition)
        self.assertIn("requiredStorage: 25.0", partition)
        self.assertIn("mountPoint: /boot/efi", partition)
        self.assertIn("efiBootloaderId: ubuntu", bootloader)
        self.assertIn("username: ubuntu", removeuser)
        self.assertIn("- removeuser\n      - shellprocess", settings)
        self.assertIn("rm -f /etc/sddm.conf.d/10-ifba-os.conf", cleanup)
        self.assertIn("rm -f /etc/sudoers.d/90-casper", cleanup)
        self.assertIn("rm -f /usr/share/applications/ifba-os-installer.desktop /usr/share/applications/calamares.desktop", cleanup)
        self.assertIn("dpkg --purge casper", cleanup)
        self.assertIn("doAutologin: false", users)
        self.assertIn("setRootPassword: false", users)
        self.assertIn("minLength: 8", users)
        self.assertIn("- sudo", users)
        self.assertIn('autologinGroup: ""', users)
        self.assertIn('sudoersGroup: ""', users)
        self.assertIn("/sys/firmware/efi", launcher)
        self.assertIn("filesystem.squashfs", launcher)
        self.assertEqual(desktop["Desktop Entry"]["Exec"], "/usr/bin/ifba-os-installer")
        self.assertIn("grub-efi-amd64-signed", build)
        self.assertIn("grub-efi-arm64-signed", build)

    def test_calamares_target_extraction_and_cleanup_precede_initramfs_and_users(self):
        settings = (ROOT / "packaging/calamares/settings.conf").read_text()
        sequence = settings.split("  - exec:", 1)[1].split("  - show:", 1)[0]
        self.assertLess(sequence.index("unpackfs"), sequence.index("removeuser"))
        self.assertLess(sequence.index("removeuser"), sequence.index("shellprocess"))
        self.assertLess(sequence.index("shellprocess"), sequence.index("initramfs"))
        self.assertLess(sequence.index("shellprocess"), sequence.index("users"))
        self.assertLess(sequence.index("users"), sequence.index("displaymanager"))


if __name__ == "__main__":
    unittest.main()
