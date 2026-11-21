"""Static packaging contracts for the native desktop builds."""

import configparser
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
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

    def test_container_build_script_has_valid_shell_syntax(self):
        subprocess.run(["bash", "-n", str(ROOT / "scripts/build-iso-container.sh")], check=True)

    def test_lock_screen_uses_selected_wallpaper_for_live_and_new_users(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        config = (ROOT / "packaging/plasma/ifba-os-lockscreen.conf").read_text()
        wallpaper = ROOT / "assets/wallpapers/ifba-os-lockscreen.png"

        self.assertTrue(wallpaper.is_file())
        self.assertIn("/work/assets/wallpapers/ifba-os-lockscreen.png", build)
        self.assertIn("/usr/share/backgrounds/ifba-os/lockscreen-wallpaper.png", build)
        self.assertIn("$ROOTFS/etc/skel/.config/kscreenlockerrc", build)
        self.assertIn("$ROOTFS/home/ubuntu/.config/kscreenlockerrc", build)
        self.assertIn("WallpaperPlugin=org.kde.image", config)
        self.assertIn("Image=/usr/share/backgrounds/ifba-os/lockscreen-wallpaper.png", config)

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

    def test_assistant_presents_window_before_connecting_to_session_bus(self):
        ui = (ROOT / "ai/ifba_ai/ui.py").read_text()
        activation = ui.split("    def do_activate(self):", 1)[1].split("    def do_startup(self):", 1)[0]
        self.assertLess(activation.index("window.show_all()"), activation.index("window.present()"))
        self.assertLess(activation.index("window.present()"), activation.index("GLib.idle_add(window._connect_service)"))
        self.assertIn('self.retry_service_button = Gtk.Button(label="Tentar novamente")', ui)
        self.assertIn('self.retry_service_button.connect("clicked", self._retry_service)', ui)
        self.assertIn("self.service_connection_started = False", ui)

    def test_ai_launch_files_and_user_service_are_packaged_with_runtime_dependencies(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        launcher = configparser.ConfigParser(interpolation=None)
        launcher.read(ROOT / "packaging/ifba-ai.desktop")
        service = configparser.ConfigParser(interpolation=None)
        service.read(ROOT / "packaging/ifba-ai.service")
        dbus_service = configparser.ConfigParser(interpolation=None)
        dbus_service.read(ROOT / "packaging/org.ifba.OS.AI.service")

        self.assertEqual(launcher["Desktop Entry"]["Exec"], "/usr/bin/ifba-ai-ui")
        self.assertIn("python3-dbus python3-gi gir1.2-gtk-3.0", build)
        self.assertIn("dbus-x11", build)
        self.assertIn("/usr/lib/systemd/user/", build)
        self.assertIn("/usr/share/dbus-1/services/", build)
        self.assertEqual(service["Service"]["Type"], "dbus")
        self.assertEqual(service["Service"]["BusName"], "org.ifba.OS.AI")
        self.assertEqual(dbus_service["D-BUS Service"]["SystemdService"], "ifba-ai.service")

    def test_konsole_glass_is_default_for_new_users_without_replacing_existing_user_settings(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        profile = configparser.ConfigParser(interpolation=None)
        profile.read(ROOT / "packaging/konsole/IFBA Terminal.profile")
        colors = configparser.ConfigParser(interpolation=None)
        colors.read(ROOT / "packaging/konsole/IFBA Glass.colorscheme")
        prompt = (ROOT / "packaging/ifba-prompt.sh").read_text()

        self.assertEqual(profile["General"]["Name"], "IFBA Terminal")
        self.assertEqual(profile["Appearance"]["ColorScheme"], "IFBA Glass")
        self.assertEqual(colors["General"]["Description"], "IFBA Glass")
        self.assertGreater(float(colors["General"]["Opacity"]), 0.9)
        self.assertEqual(colors["Background"]["Transparency"], "12")
        self.assertIn("fastfetch", build)
        self.assertIn("! -e \"$home_root/.config/konsolerc\"", build)
        self.assertIn("! -e \"$home_root/.local/share/konsole/IFBA Terminal.profile\"", build)
        self.assertIn("PROMPT_COMMAND=__ifba_set_prompt", prompt)
        self.assertNotIn("fastfetch\\n", prompt)

    def test_plasma_launcher_uses_the_official_institutional_symbol(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        layout = (ROOT / "packaging/plasma/ifba-os/contents/layouts/org.kde.plasma.desktop-layout.js").read_text()
        symbol = ROOT / "assets/icons/ifba-institutional-symbol.png"
        self.assertTrue(symbol.is_file())
        self.assertIn('cp -R /work/assets/icons/. "$ROOTFS/usr/share/ifba-os/assets/icons/"', build)
        self.assertNotIn("ifba-mark-placeholder.png", layout)
        self.assertIn("ifba-institutional-symbol.png", layout)
        self.assertNotIn('writeConfig("menuLabel", "IFBA OS")', layout)

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
            "kwin-style-aurorae",
            "milou",
            "sddm",
            "dolphin",
            "konsole",
            "plasma-discover",
            "plasma-nm",
            "plasma-pa",
            "systemsettings",
            "kinfocenter",
            "powerdevil",
            "upower",
        ):
            self.assertIn(package, build)
        self.assertIn('debootstrap --arch="$IFBA_ARCH" resolute', build)
        self.assertIn("IFBA-OS-Dark.colors", build)
        self.assertIn("IFBA OS Dark", build)
        self.assertIn("org.ifbaos.desktop", build)
        self.assertEqual(metadata["KPackageStructure"], "Plasma/LookAndFeel")
        self.assertEqual(metadata["KPlugin"]["Id"], "org.ifbaos.desktop")
        top_layout = layout.split("var dock = new Panel", 1)[0]
        top_widgets = re.findall(r'topPanel\.addWidget\("([^"]+)"\)', top_layout)
        self.assertEqual(top_widgets, [
            "org.kde.plasma.appmenu",
            "org.kde.plasma.panelspacer",
            "org.kde.plasma.systemtray",
            "org.kde.plasma.digitalclock",
        ])
        self.assertIn('topPanel.location = "top"', top_layout)
        self.assertIn("topPanel.height = 36", top_layout)
        self.assertIn("topPanel.floating = true", top_layout)
        self.assertNotIn('systemMenu.writeConfig("menuLabel", "IFBA OS")', top_layout)
        self.assertIn('appLauncher.writeConfig("icon", "file:///usr/share/ifba-os/assets/icons/ifba-institutional-symbol.png")', layout)
        self.assertIn('appLauncher.writeConfig("systemFavorites", "lock-screen,reboot,shutdown")', layout)
        self.assertIn('globalMenu.writeConfig("compactView", "true")', top_layout)
        self.assertNotIn("org.kde.plasma.kicker", top_layout)
        self.assertNotIn("org.kde.milou", top_layout)
        for tray_item in (
            "org.kde.plasma.notifications",
            "org.kde.plasma.networkmanagement",
            "org.kde.plasma.volume",
            "org.kde.plasma.battery",
        ):
            self.assertIn(tray_item, top_layout)
        self.assertIn('clock.writeConfig("dateFormat", "custom")', top_layout)
        self.assertIn("ddd d 'de' MMM yyyy", top_layout)
        self.assertIn('clock.writeConfig("use24hFormat", "2")', top_layout)
        self.assertIn('dock.location = "bottom"', layout)
        self.assertIn('dock.height = 70', layout)
        self.assertIn('dock.lengthMode = "fit"', layout)
        self.assertIn('dock.alignment = "center"', layout)
        self.assertIn('dock.floating = true', layout)
        self.assertIn('dock.hiding = "dodgewindows"', layout)
        self.assertIn('org.kde.plasma.icontasks', layout)
        for favorite in ("firefox.desktop", "org.kde.dolphin.desktop", "org.kde.konsole.desktop",
                         "ifba-ai.desktop", "systemsettings.desktop"):
            self.assertIn(favorite, layout)
        for widget in ("org.kde.plasma.kickoff", "org.kde.plasma.icontasks",
                       "org.kde.plasma.systemtray", "org.kde.plasma.digitalclock",
                       "org.kde.plasma.panelspacer"):
            self.assertIn(widget, layout)
        dock = layout.split("var dock = new Panel", 1)[1]
        kickoff_index = dock.index('dock.addWidget("org.kde.plasma.kickoff")')
        tasks_index = dock.index('dock.addWidget("org.kde.plasma.icontasks")')
        self.assertLess(kickoff_index, tasks_index)
        launcher_line = re.search(r'tasks\.writeConfig\("launchers", "([^"]+)"\)', dock)
        self.assertIsNotNone(launcher_line)
        self.assertEqual(
            launcher_line.group(1).split(","),
            [
                "applications:ifba-ai.desktop",
                "applications:firefox.desktop",
                "applications:org.kde.dolphin.desktop",
                "applications:org.kde.konsole.desktop",
                "applications:systemsettings.desktop",
            ],
        )
        self.assertIn('tasks.writeConfig("showToolTips", true)', dock)
        self.assertIn('tasks.writeConfig("taskHoverEffect", true)', dock)
        self.assertIn('tasks.writeConfig("groupingStrategy", 1)', dock)
        self.assertIn('tasks.writeConfig("sortingStrategy", 1)', dock)
        self.assertIn('tasks.writeConfig("iconSpacing", 1)', dock)
        for required_file in (
            "/usr/share/plasma/plasmoids/org.kde.plasma.icontasks/metadata.json",
            "org.kde.plasma.taskmanager.so",
            "org.thonny.Thonny.desktop",
            "org.kde.gcompris.desktop",
            "libreoffice-writer.desktop",
        ):
            self.assertIn(required_file, build)
        self.assertIn("LookAndFeelPackage=org.ifbaos.desktop", defaults)
        self.assertIn("[kwinrc][Desktops]\nNumber=1", defaults)
        self.assertIn("ButtonsOnLeft=\nButtonsOnRight=IAX", defaults)
        self.assertIn("library=org.kde.kwin.aurorae", defaults)
        self.assertIn("theme=__aurorae__svg__IFBA-Window", defaults)
        self.assertIn("AnimationSpeed=2", defaults)
        self.assertIn("[kwinrc][Effect-Overview]", defaults)
        setup = (ROOT / "packaging/plasma/ifba-os-session-setup").read_text()
        self.assertIn('legacy_marker="$state_dir/plasma-layout-applied"', setup)
        self.assertIn('layout_marker="$state_dir/plasma-layout-applied-v2"', setup)
        self.assertIn('wallpaper_marker="$state_dir/plasma-wallpaper-attempted-v2"', setup)
        self.assertIn('touch "$layout_marker"', setup)
        self.assertLess(setup.index('touch "$wallpaper_marker"'), setup.index("plasma-apply-wallpaperimage"))

        self.assertIn('if [ -e "$legacy_marker" ] && [ ! -e "$layout_marker" ]; then', setup)
        self.assertIn("plasma-apply-lookandfeel --apply org.ifbaos.desktop", setup)
        self.assertIn("plasma-apply-wallpaperimage /usr/share/backgrounds/ifba-os/wallpaper.png", setup)
        self.assertIn('cp "$ROOTFS/etc/xdg/autostart/ifba-os-plasma-session-setup.desktop" "$ROOTFS/etc/skel/.config/autostart/"', build)
        self.assertIn('find "$ROOTFS/usr/lib" -path "*/qt6/plugins/plasma/applets/$applet.so"', build)
        for applet in (
            "org.kde.milou",
            "org.kde.plasma.kickoff",
            "org.kde.plasma.kicker",
            "org.kde.plasma.appmenu",
            "org.kde.plasma.systemtray",
            "org.kde.plasma.notifications",
            "org.kde.plasma.networkmanagement",
            "org.kde.plasma.volume",
            "org.kde.plasma.battery",
        ):
            self.assertIn(applet, build)
        self.assertIn("Session=plasmax11.desktop", build)
        self.assertIn("/lib/systemd/system/sddm.service", build)
        self.assertNotIn("xfce4-session", build)
        self.assertNotIn("lightdm", build.lower())

    def test_plasma_session_setup_applies_panels_only_once(self):
        setup = ROOT / "packaging/plasma/ifba-os-session-setup"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            mock_bin = temp / "bin"
            mock_bin.mkdir()
            log = temp / "calls.log"
            for command in ("plasma-apply-lookandfeel", "plasma-apply-wallpaperimage"):
                mock = mock_bin / command
                mock.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$TEST_LOG\"\n")
                mock.chmod(0o755)
            env = os.environ.copy()
            env.update({"HOME": str(temp / "home"), "PATH": f"{mock_bin}:/usr/bin:/bin", "TEST_LOG": str(log)})
            for _ in range(2):
                subprocess.run([str(setup)], env=env, check=True, capture_output=True, text=True)
            self.assertEqual(log.read_text().splitlines(), [
                "--apply org.ifbaos.desktop",
                "/usr/share/backgrounds/ifba-os/wallpaper.png",
            ])
            self.assertTrue((temp / "home/.config/ifba-os/plasma-layout-applied-v2").is_file())

    def test_ifba_aurorae_decoration_is_installed_and_has_native_window_controls(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        theme_dir = ROOT / "packaging/plasma/window-decoration/IFBA-Window"
        metadata = configparser.ConfigParser(interpolation=None)
        metadata.read(theme_dir / "metadata.desktop")
        theme = configparser.ConfigParser(interpolation=None)
        theme.read(theme_dir / "IFBA-Windowrc")
        frame_ids = {
            node.attrib.get("id")
            for node in ET.parse(theme_dir / "decoration.svg").iter()
        }

        self.assertEqual(metadata["DesktopEntry"]["x-kde-plugininfo-name"], "IFBA-Window")
        self.assertEqual(theme["General"]["rightbuttons"], "IAX")
        self.assertEqual(theme["Layout"]["titleheight"], "34")
        self.assertEqual(theme["Layout"]["buttonwidthclose"], "42")
        self.assertEqual(theme["Layout"]["buttonheight"], "34")
        for frame in ("decoration-top", "decoration-inactive-top", "decoration-maximized-center"):
            self.assertIn(frame, frame_ids)
        for button, path in (("minimize", "M14 17H28"), ("maximize", "#22C55E"),
                             ("restore", "#22C55E"), ("close", "#F87171")):
            button_ids = {
                node.attrib.get("id")
                for node in ET.parse(theme_dir / f"{button}.svg").iter()
            }
            self.assertIn("active-center", button_ids)
            self.assertIn("hover-center", button_ids)
            self.assertIn("inactive-center", button_ids)
            self.assertIn(path, (theme_dir / f"{button}.svg").read_text())
        self.assertIn("kwin-style-aurorae", build)
        self.assertIn("/usr/share/aurorae/themes/IFBA-Window", build)
        self.assertIn("org.kde.kdecoration3/org.kde.kwin.aurorae.so", build)

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

    def test_ifba_welcome_is_packaged_as_a_kde_first_session_app(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        source = (ROOT / "welcome/ifba_welcome.py").read_text()
        desktop = configparser.ConfigParser(interpolation=None)
        desktop.read(ROOT / "packaging/ifba-os-welcome.desktop")
        autostart = configparser.ConfigParser(interpolation=None)
        autostart.read(ROOT / "packaging/ifba-os-welcome-autostart.desktop")
        tools = json.loads((ROOT / "config/educational-apps.json").read_text())
        installed_tools = {item["package"] for item in tools if item["status"] == "installed"}

        self.assertIn("python3-pyqt6", build)
        self.assertIn("/work/welcome/ifba_welcome.py", build)
        self.assertIn("/etc/xdg/autostart/ifba-os-welcome.desktop", build)
        self.assertIn("thonny libreoffice-writer gcompris-qt", build)
        self.assertTrue({"thonny", "libreoffice-writer", "gcompris-qt"}.issubset(installed_tools))
        self.assertEqual(desktop["Desktop Entry"]["Exec"], "/usr/bin/ifba-welcome")
        self.assertEqual(desktop["Desktop Entry"]["OnlyShowIn"], "KDE;")
        self.assertEqual(autostart["Desktop Entry"]["Exec"], "/usr/bin/ifba-welcome --autostart")
        self.assertIn("https://suap.ifba.edu.br/", source)
        self.assertIn("https://ava.ifba.edu.br/", source)
        self.assertIn("--mode", source)
        self.assertIn("showAtLogin", source)
        self.assertIn("Não mostrar novamente ao entrar", source)
        self.assertNotIn("suap.ifba.edu.br/api", source)
        self.assertNotIn("ava.ifba.edu.br/api", source)


if __name__ == "__main__":
    unittest.main()
