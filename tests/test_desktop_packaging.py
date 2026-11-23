"""Static packaging contracts for the native desktop builds."""

import configparser
import gzip
import json
from pathlib import Path
import re
import shutil
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
        layout = (ROOT / "packaging/plasma/ifba-os/contents/layouts/org.kde.plasma.desktop-layout.js").read_text()
        self.assertIn('desktop.writeConfig("Image", "file:///usr/share/backgrounds/ifba-os/campus-jacobina.jpg")', layout)
        self.assertIn("/usr/share/backgrounds/ifba-os/campus-jacobina.jpg", build)
        self.assertIn("/usr/share/backgrounds/ifba-os/wallpaper.png", build)
        self.assertIn("/work/assets/wallpapers/ifba-os-desktop.png", build)
        self.assertIn("/usr/share/plymouth/themes/ifba-os/", build)
        self.assertIn("/work/assets/plymouth/ifba-os-startup.png", build)
        self.assertIn('/work/assets/animations/boot animation.mp4', build)
        self.assertTrue((ROOT / "assets/animations/boot animation.mp4").is_file())
        plymouth_script = (ROOT / "packaging/plymouth/ifba-os.script").read_text()
        self.assertIn("Plymouth.SetBootProgressFunction", plymouth_script)
        self.assertIn("frame-", plymouth_script)
        self.assertIn("boot=casper quiet splash ---", build)
        self.assertIn('lsinitramfs /boot/initrd.img', build)
        self.assertIn('cmp -s "$ISO/casper/initrd" "$VERIFY_DIR/casper/initrd"', build)

    @unittest.skipUnless(shutil.which("ffmpeg"), "requires FFmpeg to package the boot theme")
    def test_plymouth_packaging_decodes_video_and_records_the_whole_sequence(self):
        with tempfile.TemporaryDirectory() as directory:
            theme = Path(directory) / "theme"
            subprocess.run(["bash", str(ROOT / "scripts/install-plymouth-theme.sh"), str(theme)],
                           check=True)
            frames = sorted(theme.glob("frame-*.png"))
            self.assertGreaterEqual(len(frames), 120)
            self.assertLessEqual(len(frames), 121)
            self.assertEqual(frames, [theme / f"frame-{index:03d}.png"
                                      for index in range(1, len(frames) + 1)])
            self.assertNotEqual(frames[0].read_bytes(), frames[len(frames) // 2].read_bytes())
            script = (theme / "ifba-os.script").read_text()
            self.assertIn(f"frame_count = {len(frames)};", script)
            self.assertIn("frame_rate = 12;", script)
            self.assertNotIn("@FRAME_", script)

    def test_dolphin_and_systemsettings_defaults_are_packaged(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        dolphin = configparser.ConfigParser(interpolation=None)
        dolphin.read(ROOT / "packaging/plasma/dolphinrc")
        settings = configparser.ConfigParser(interpolation=None)
        settings.read(ROOT / "packaging/plasma/systemsettingsrc")

        self.assertEqual(dolphin["MainWindow"]["MenuBar"], "Disabled")
        self.assertEqual(dolphin["IconsMode"]["IconSize"], "64")
        self.assertEqual(settings["General"]["ActiveView"], "systemsettings_sidebar_mode")
        self.assertEqual(settings["MainWindow"]["MenuBar"], "Disabled")
        self.assertIn("/etc/xdg/dolphinrc", build)
        self.assertIn("/etc/xdg/systemsettingsrc", build)
        self.assertIn("accentColorFromWallpaper=false", build)

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
        self.assertIn("Image=file:///usr/share/backgrounds/ifba-os/campus-jacobina.jpg", config)
        self.assertTrue((ROOT / "assets/wallpapers/ifba-os-campus-jacobina.jpg").is_file())

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
        self.assertEqual(entry["Desktop Entry"]["StartupWMClass"], "org.ifba.OS.Assistant.Preview")
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
        self.assertIn("self.status.set_text(\"Serviço do assistente indisponível\")", ui)

    def test_assistant_presents_window_before_connecting_to_session_bus(self):
        ui = (ROOT / "ai/ifba_ai/ui.py").read_text()
        activation = ui.split("    def do_activate(self):", 1)[1].split("    def do_startup(self):", 1)[0]
        self.assertLess(activation.index("window.show_all()"), activation.index("window.present()"))
        self.assertLess(activation.index("window.present()"), activation.index("GLib.idle_add(window._connect_service)"))
        self.assertIn('self.retry_service_button = Gtk.Button(label="Tentar novamente")', ui)
        self.assertIn('self.retry_service_button.connect("clicked", self._retry_service)', ui)
        self.assertIn("self.service_connection_started = False", ui)

    def test_assistant_shows_an_empty_state_and_recoverable_service_error(self):
        ui = (ROOT / "ai/ifba_ai/ui.py").read_text()
        loaded = ui.split("    def _on_conversations_loaded(", 1)[1].split("    def _load_settings(", 1)[0]
        failed = ui.split("    def _on_service_error(", 1)[1].split("    def _load_settings(", 1)[0]

        self.assertIn('"IFBA AI\\n\\nConectando ao serviço do assistente…"', ui)
        self.assertIn('self.stack.get_visible_child_name() == "chat"', loaded)
        self.assertIn("self._display_history()", loaded)
        self.assertIn('self.messages_buffer.set_text("IFBA AI\\n\\n" + message)', failed)
        self.assertIn('self.stack.set_visible_child_name("chat")', failed)
        self.assertIn("self.retry_service_button.show()", failed)
        self.assertNotIn("button.set_group(previous)", ui)
        self.assertIn("def _on_reasoning_toggled(self, button, level):", ui)

    def test_top_panel_has_a_visible_ifba_launcher_and_k_runner_hint(self):
        layout = (ROOT / "packaging/plasma/ifba-os/contents/layouts/org.kde.plasma.desktop-layout.js").read_text()
        welcome = (ROOT / "welcome/ifba_welcome.py").read_text()

        self.assertIn('var topLauncher = topPanel.addWidget("org.kde.plasma.kickoff")', layout)
        self.assertIn('topLauncher.writeConfig("icon", "file:///usr/share/ifba-os/assets/icons/ifba-institutional-symbol.png")', layout)
        self.assertIn("A busca do sistema abre com Alt+Espaço.", welcome)

    def test_welcome_window_is_bounded_by_current_display_geometry(self):
        welcome = (ROOT / "welcome/ifba_welcome.py").read_text()

        self.assertIn("screen.availableGeometry()", welcome)
        self.assertIn("int(available.width() * 0.80)", welcome)
        self.assertIn("int(available.height() * 0.72)", welcome)
        self.assertNotIn("self.resize(1020, 760)", welcome)

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
        self.assertNotIn("default.target.wants/ifba-ai.service", build)
        self.assertEqual(service["Service"]["Type"], "dbus")
        self.assertEqual(service["Service"]["BusName"], "org.ifba.OS.AI")
        self.assertEqual(dbus_service["D-BUS Service"]["SystemdService"], "ifba-ai.service")

    def test_live_demo_uses_ephemeral_memory_and_is_removed_by_installer(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        installer = (ROOT / "packaging/calamares/shellprocess.conf").read_text()
        service = (ROOT / "ai/ifba_ai/service.py").read_text()
        daemon = (ROOT / "ai/ifba_ai/daemon.py").read_text()
        ui = (ROOT / "ai/ifba_ai/ui.py").read_text()

        self.assertIn('install -D -m 0644 /dev/null "$ROOTFS/etc/ifba-os/live-demo"', build)
        self.assertIn("/usr/bin/rm -f /etc/ifba-os/live-demo", installer)
        self.assertIn('self.storage = ConversationStore(self.paths, in_memory=self.live_demo)', service)
        self.assertIn('out_signature="bbbs"', daemon)
        self.assertIn("def _on_service_status(self, configured, store_available, live_demo, _model):", ui)
        self.assertIn("não armazena chaves, conversas, memórias ou capturas", ui)

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
        self.assertEqual(float(colors["General"]["Opacity"]), 0.80)
        self.assertTrue(colors["General"].getboolean("Blur"))
        self.assertEqual(profile["General"].getint("TerminalMargin"), 12)
        fetch = json.loads((ROOT / "packaging/konsole/fastfetch.jsonc").read_text())
        self.assertTrue(fetch["logo"]["source"].endswith("/ifba-institutional-symbol.png"))
        self.assertEqual(fetch["logo"]["type"], "sixel")
        self.assertIn("libmagickcore-7.q16-10", build)
        self.assertIn("fastfetch", build)
        self.assertIn("! -e \"$home_root/.config/konsolerc\"", build)
        self.assertIn("! -e \"$home_root/.local/share/konsole/IFBA Terminal.profile\"", build)
        self.assertIn("alias neofetch=", prompt)
        self.assertNotIn("PROMPT_COMMAND=", prompt)
        self.assertNotIn("fastfetch\\n", prompt)

    def test_plasma_launcher_uses_the_official_institutional_symbol(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        layout = (ROOT / "packaging/plasma/ifba-os/contents/layouts/org.kde.plasma.desktop-layout.js").read_text()
        symbol = ROOT / "assets/icons/ifba-institutional-symbol.png"
        self.assertTrue(symbol.is_file())
        self.assertIn('cp -R /work/assets/icons/. "$ROOTFS/usr/share/ifba-os/assets/icons/"', build)
        self.assertNotIn("ifba-mark-placeholder.png", layout)
        self.assertIn("ifba-institutional-symbol.png", layout)
        self.assertIn('topLauncher.writeConfig("menuLabel", "IFBA OS")', layout)

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
            "power-profiles-daemon",
            "bluedevil",
            "bluez",
            "libspa-0.2-bluetooth",
            "kscreen",
            "upower",
        ):
            self.assertIn(package, build)
        self.assertIn('resolute "$ROOTFS" "$ARCHIVE"', build)
        self.assertIn("IFBA-OS-Dark.colors", build)
        self.assertIn("IFBA OS Dark", build)
        self.assertIn("org.ifbaos.desktop", build)
        self.assertEqual(metadata["KPackageStructure"], "Plasma/LookAndFeel")
        self.assertEqual(metadata["KPlugin"]["Id"], "org.ifbaos.desktop")
        top_layout = layout.split("var dock = new Panel", 1)[0]
        top_widgets = re.findall(r'topPanel\.addWidget\("([^"]+)"\)', top_layout)
        self.assertEqual(top_widgets, [
            "org.kde.plasma.kickoff",
            "org.kde.plasma.appmenu",
            "org.kde.plasma.panelspacer",
            "org.kde.milou",
            "org.kde.plasma.systemtray",
            "org.kde.plasma.digitalclock",
        ])
        self.assertIn('topPanel.location = "top"', top_layout)
        self.assertIn("topPanel.height = 36", top_layout)
        self.assertIn("topPanel.floating = false", top_layout)
        self.assertIn('topPanel.opacity = "translucent"', top_layout)
        self.assertIn('topLauncher.writeConfig("icon", "file:///usr/share/ifba-os/assets/icons/ifba-institutional-symbol.png")', layout)
        self.assertIn('topLauncher.writeConfig("systemFavorites", "suspend,logout,reboot,shutdown")', layout)
        self.assertIn('topLauncher.writeConfig("favoritesDisplay", 0)', layout)
        self.assertIn('topLauncher.writeConfig("applicationsDisplay", 0)', layout)
        self.assertIn('topLauncher.writeConfig("alphaSort", true)', layout)
        self.assertIn('globalMenu.writeConfig("compactView", false)', top_layout)
        self.assertNotIn("org.kde.plasma.kicker", top_layout)
        for tray_item in (
            "org.kde.plasma.notifications",
            "org.kde.plasma.networkmanagement",
            "org.kde.plasma.volume",
            "org.kde.plasma.battery",
            "org.kde.plasma.bluetooth",
        ):
            self.assertIn(tray_item, top_layout)
        self.assertIn('clock.writeConfig("dateFormat", "custom")', top_layout)
        self.assertIn("ddd d 'de' MMM yyyy", top_layout)
        self.assertIn('clock.writeConfig("use24hFormat", "2")', top_layout)
        self.assertIn('dock.location = "bottom"', layout)
        self.assertIn('dock.height = 68', layout)
        self.assertIn('dock.addWidget("org.kde.plasma.trash")', layout)
        self.assertIn('dock.opacity = "translucent"', layout)
        self.assertIn('dock.lengthMode = "fit"', layout)
        self.assertIn('dock.alignment = "center"', layout)
        self.assertIn('dock.floating = true', layout)
        self.assertIn('dock.hiding = "none"', layout)
        self.assertNotIn('com.github.mattanis.macosdock', layout)
        for favorite in ("firefox.desktop", "org.kde.dolphin.desktop", "org.kde.konsole.desktop",
                         "ifba-ai.desktop", "systemsettings.desktop"):
            self.assertIn(favorite, layout)
        for widget in ("org.kde.plasma.kickoff", "org.kde.plasma.icontasks",
                       "org.kde.plasma.systemtray", "org.kde.plasma.digitalclock",
                       "org.kde.plasma.panelspacer"):
            self.assertIn(widget, layout)
        dock = layout.split("var dock = new Panel", 1)[1]
        self.assertEqual(re.findall(r'dock(?:Launcher)?\.addWidget\("([^"]+)"\)', dock),
                         ["org.kde.plasma.kickoff", "org.kde.plasma.icontasks", "org.kde.plasma.trash"])
        self.assertEqual(layout.count('.addWidget("org.kde.plasma.kickoff")'), 2)
        ai_desktop = (ROOT / "packaging/ifba-ai.desktop").read_text()
        ai_preview = (ROOT / "ai/ifba_ai/ui_preview.py").read_text()
        self.assertIn("ai-assistant-orb.png", ai_desktop)
        self.assertIn("ifba-institutional-symbol.png", ai_preview)
        launcher_line = re.search(r'tasks\.writeConfig\("launchers", \[(.*?)\]', dock, re.S)
        self.assertIsNotNone(launcher_line)
        self.assertEqual(
            re.findall(r'"(applications:[^"]+)"', launcher_line.group(1)),
            [
                "applications:org.kde.dolphin.desktop",
                "applications:systemsettings.desktop",
                "applications:ifba-ai.desktop",
                "applications:org.kde.konsole.desktop",
                "applications:com.visualstudio.CodeOSS.desktop",
                "applications:firefox.desktop",
                "applications:libreoffice-writer.desktop",
            ],
        )
        self.assertIn('tasks.writeConfig("showToolTips", true)', dock)
        self.assertIn('tasks.writeConfig("groupingStrategy", 1)', dock)
        self.assertIn('tasks.writeConfig("sortingStrategy", 1)', dock)
        for required_file in (
            "/usr/share/plasma/plasmoids/org.kde.plasma.icontasks/metadata.json",
            "org.kde.plasma.taskmanager.so",
            "com.visualstudio.CodeOSS.desktop",
            "org.kde.gcompris.desktop",
            "libreoffice-writer.desktop",
            "suap-ifba.desktop",
            "ava-ifba.desktop",
        ):
            self.assertIn(required_file, build)
        self.assertIn("LookAndFeelPackage=org.ifbaos.desktop", defaults)
        self.assertIn("[kwinrc][Desktops]\nNumber=1", defaults)
        self.assertIn("ButtonsOnLeft=M\nButtonsOnRight=IAX", defaults)
        self.assertIn("library=org.kde.kwin.aurorae", defaults)
        self.assertIn("theme=__aurorae__svg__IFBA-Window", defaults)
        self.assertNotIn("AnimationSpeed=", defaults)
        self.assertIn("magiclampEnabled=true", defaults)
        self.assertIn("overviewEnabled=true", defaults)
        motion = json.loads((ROOT / "packaging/design-system/tokens.json").read_text())["motion"]
        self.assertIn(
            f"[kwinrc][Effect-magiclamp]\nAnimationDuration={motion['duration_standard_ms']}",
            defaults,
        )
        self.assertIn(
            f"[kwinrc][Effect-scale]\nDuration={motion['duration_standard_ms']}",
            defaults,
        )
        self.assertIn("[kwinrc][Effect-overview]", defaults)
        self.assertNotIn('Exec=/usr/local/bin/ifba-os-plasma-session-setup', build)
        self.assertIn('^LookAndFeelPackage=org.ifbaos.desktop$', build)
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
        self.assertIn("Session=plasma.desktop", build)
        self.assertIn("/lib/systemd/system/sddm.service", build)
        self.assertNotIn("xfce4-session", build)
        self.assertNotIn("lightdm", build.lower())

    def test_kickoff_launcher_uses_native_catalog_grid_and_real_session_actions(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        layout = (ROOT / "packaging/plasma/ifba-os/contents/layouts/org.kde.plasma.desktop-layout.js").read_text()
        kickoff = layout.split('var topLauncher = topPanel.addWidget("org.kde.plasma.kickoff")', 1)[1].split("var globalMenu", 1)[0]
        favorites = re.search(r'topLauncher\.writeConfig\("favorites", "([^"]+)"\)', kickoff)
        self.assertIsNotNone(favorites)
        self.assertEqual(favorites.group(1).split(","), [
            "applications:ifba-ai.desktop",
            "applications:firefox.desktop",
            "applications:org.kde.dolphin.desktop",
            "applications:org.kde.konsole.desktop",
            "applications:systemsettings.desktop",
            "applications:suap-ifba.desktop",
            "applications:ava-ifba.desktop",
        ])
        self.assertIn('topLauncher.writeConfig("primaryActions", "3")', kickoff)
        self.assertIn('topLauncher.writeConfig("systemFavorites", "suspend,logout,reboot,shutdown")', kickoff)
        self.assertIn('find "$ROOTFS/usr/lib" -path "*/qt6/plugins/plasma/applets/$applet.so"', build)
        self.assertIn("org.kde.plasma.kickoff", build)
        self.assertIn('cp /work/packaging/firefox.desktop /work/packaging/suap-ifba.desktop /work/packaging/ava-ifba.desktop', build)

    def test_kickoff_description_search_runner_is_built_tested_and_installed(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        runner_dir = ROOT / "packaging/plasma/ifba-app-description-runner"
        cmake = (runner_dir / "CMakeLists.txt").read_text()
        runner = (runner_dir / "appdescriptionrunner.cpp").read_text()
        metadata = json.loads((runner_dir / "ifba_app_description_runner.json").read_text())

        self.assertEqual(metadata["KPlugin"]["Id"], "org.ifba.os.appdescriptionrunner")
        self.assertTrue(metadata["KPlugin"]["EnabledByDefault"])
        self.assertIn("KF6::Runner", cmake)
        self.assertIn("find_package(KF6Service REQUIRED)", cmake)
        self.assertIn("include(CTest)", cmake)
        self.assertIn("KApplicationTrader::query", runner)
        self.assertIn("service->comment()", runner)
        self.assertIn("KIO::ApplicationLauncherJob", runner)
        self.assertIn('"${KRUNNER_BUILD_PACKAGES[@]}"', build)
        self.assertIn("ctest --test-dir /tmp/ifba-app-description-runner/build --output-on-failure", build)
        self.assertIn('apt-get purge -y "${KRUNNER_BUILD_PACKAGES[@]}"', build)
        self.assertIn("Build-only dependency remains installed", build)
        self.assertIn("*/kf6/krunner/ifba_app_description_runner.so", build)

    def test_top_bar_uses_native_system_tray_instead_of_custom_control_center(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        layout = (ROOT / "packaging/plasma/ifba-os/contents/layouts/org.kde.plasma.desktop-layout.js").read_text()
        self.assertNotIn('topPanel.addWidget("org.ifbaos.controlcenter")', layout)
        self.assertIn('topPanel.addWidget("org.kde.plasma.systemtray")', layout)
        self.assertIn('tray.writeConfig("shownItems",', layout)
        self.assertIn("org.kde.plasma.bluetooth", layout)
        self.assertNotIn("ifba-control-center/metadata.json", build)
        self.assertNotIn('install -D -m 0644 /work/packaging/plasma/ifba-control-center', build)
        self.assertIn('test ! -e "$ROOTFS/usr/share/plasma/plasmoids/org.ifbaos.controlcenter"', build)

    def test_live_and_installed_session_policies_are_explicit(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        cleanup = (ROOT / "packaging/calamares/shellprocess.conf").read_text()
        displaymanager = (ROOT / "packaging/calamares/displaymanager.conf").read_text()
        self.assertIn("DisplayServer=x11", build)
        self.assertIn("localedef --inputfile=pt_BR --charmap=UTF-8 pt_BR.UTF-8", build)
        self.assertIn(r"User=ubuntu\nSession=plasma.desktop\nRelogin=false", build)
        sddm_directories = next(line for line in build.splitlines() if line.strip().startswith("mkdir -p /etc/sddm.conf.d"))
        self.assertIn("/var/lib/sddm", sddm_directories)
        self.assertLess(build.index(sddm_directories), build.index(r'printf "[Last]\nSession=plasmax11.desktop\n"'))
        self.assertIn("getent group sddm >/dev/null || groupadd --system sddm", build)
        self.assertIn("getent passwd sddm >/dev/null || useradd --system --gid sddm --home-dir /var/lib/sddm --shell /usr/sbin/nologin sddm", build)
        self.assertIn("install -d -m 0755 -o sddm -g sddm /var/lib/sddm", build)
        self.assertIn(r'printf "[Last]\nSession=plasmax11.desktop\n" > /var/lib/sddm/state.conf', build)
        self.assertIn("chown sddm:sddm /var/lib/sddm/state.conf", build)
        self.assertIn('test -s "$ROOTFS/usr/share/wayland-sessions/plasma.desktop"', build)
        self.assertIn('test -s "$ROOTFS/usr/share/xsessions/plasmax11.desktop"', build)
        self.assertIn("rm -f /etc/sddm.conf.d/10-ifba-os.conf", cleanup)
        self.assertNotIn("state.conf", cleanup)
        self.assertIn("desktopFile: plasmax11.desktop", displaymanager)
        users = (ROOT / "packaging/calamares/users.conf").read_text()
        self.assertIn("doAutologin: false", users)

    def test_kscreenlocker_uses_native_plasma_shell_with_ifba_wallpaper(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        defaults = (ROOT / "packaging/plasma/ifba-os/contents/defaults").read_text()
        shell_config = (ROOT / "packaging/plasma/ifba-os-shell.conf").read_text()
        self.assertIn("ShellPackage=org.kde.plasma.desktop", defaults)
        self.assertIn("ShellPackage=org.kde.plasma.desktop", shell_config)
        self.assertIn("org.ifbaos.plasma", build)  # targeted migration only
        self.assertNotIn("migrate_plasma_shell.py", build)
        self.assertNotIn("package_plasma_lockscreen.py", build)
        self.assertNotIn("/work/packaging/plasma/ifbaos-shell/contents/lockscreen", build)
        self.assertIn("campus-jacobina.jpg", (ROOT / "packaging/plasma/ifba-os-lockscreen.conf").read_text())
        self.assertIn("org.kde.plasma.desktop/contents/lockscreen/LockScreenUi.qml", build)

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

        self.assertEqual(metadata["Desktop Entry"]["x-kde-plugininfo-name"], "IFBA-Window")
        self.assertEqual(theme["General"]["leftbuttons"], "M")
        self.assertEqual(theme["General"]["rightbuttons"], "IAX")
        self.assertEqual(theme["Layout"]["titleheight"], "16")
        for edge in ("titleedgetop", "titleedgebottom", "titleedgetopmaximized", "titleedgebottommaximized"):
            self.assertEqual(theme["Layout"][edge], "6")
        self.assertFalse(theme["General"].getboolean("usetextshadow"))
        colors = json.loads((ROOT / "packaging/design-system/tokens.json").read_text())["colors"]
        for title_state, token in (("activetextcolor", "text_primary"), ("inactivetextcolor", "text_secondary")):
            rgb = bytes.fromhex(colors[token][1:])
            self.assertEqual(theme["General"][title_state], ",".join(map(str, rgb)))
        self.assertEqual(theme["Layout"]["paddingtop"], "20")
        self.assertEqual(theme["Layout"]["paddingbottom"], "79")
        self.assertEqual(theme["Layout"]["paddingleft"], "40")
        self.assertEqual(theme["Layout"]["paddingright"], "40")
        self.assertEqual(theme["Layout"]["buttonwidth"], "16")
        self.assertEqual(theme["Layout"]["buttonheight"], "16")
        for frame in ("decoration-top", "decoration-inactive-top", "decoration-center", "decoration-left"):
            self.assertIn(frame, frame_ids)
        for button in ("minimize", "maximize", "restore", "close"):
            button_ids = {
                node.attrib.get("id")
                for node in ET.parse(theme_dir / f"{button}.svg").iter()
            }
            self.assertTrue({"active-center", "inactive-center", "hover-center", "pressed-center"}
                            <= button_ids, f"incomplete Aurorae control asset {button}.svg")
        self.assertIn("kwin-style-aurorae", build)
        self.assertIn("/usr/share/aurorae/themes/IFBA-Window", build)
        self.assertIn("org.kde.kdecoration3/org.kde.kwin.aurorae.so", build)
        self.assertIn("for decoration_scale in _x1.25 _x1.5 _x1.75 _x2.0; do", build)
        self.assertIn('source_theme_dir="/work/packaging/plasma/window-decoration/$scaled_theme"', build)
        for scale in ("_x1.25", "_x1.5", "_x1.75", "_x2.0"):
            scaled = ROOT / f"packaging/plasma/window-decoration/IFBA-Window{scale}"
            self.assertTrue((scaled / "decoration.svg").is_file())
            self.assertIn(f"IFBA-Window${{decoration_scale}}rc", build)

    def test_live_image_installs_pipewire_audio_stack_and_ffmpeg_for_browser_media(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        self.assertRegex(build, r"powerdevil[^\n]*pipewire-audio[^\n]*ffmpeg")
        self.assertRegex(build, r"for package in[^\n]*pipewire-audio[^\n]*pipewire-pulse[^\n]*wireplumber[^\n]*ffmpeg")

    def test_audited_upstream_theme_components_are_pinned_licensed_and_packaged(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        upstream = (ROOT / "packaging/third-party/WhiteSur-kde/UPSTREAM.md").read_text()
        self.assertIn("cf4df59ce91004f7ea39358b1b8ff917d5c329f7", upstream)
        self.assertTrue((ROOT / "packaging/third-party/WhiteSur-kde/LICENSE").is_file())
        self.assertTrue((ROOT / "packaging/third-party/WhiteSur-kde/AUTHORS").is_file())
        self.assertIn("qt-style-kvantum=1.1.5-1", build)
        self.assertIn("qt-style-kvantum-themes=1.1.5-1", build)
        self.assertIn("/work/packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark", build)
        self.assertIn('"/work/packaging/kvantum/$kvantum_theme/$kvantum_theme.svg"', build)
        self.assertIn('"/work/packaging/kvantum/$kvantum_theme/$kvantum_theme.kvconfig"', build)
        self.assertIn("IFBA-Glass-Opaque", build)
        self.assertIn("/etc/skel/.config/Kvantum/kvantum.kvconfig", build)
        self.assertIn('if [[ ! -e "$ROOTFS/home/ubuntu/.config/Kvantum/kvantum.kvconfig" ]]; then', build)
        theme = json.loads((ROOT / "packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark/metadata.json").read_text())
        self.assertEqual(theme["KPlugin"]["Id"], "IFBA-WhiteSur-Dark")
        self.assertEqual(theme["KPlugin"]["License"], "GPL-3.0")
        self.assertEqual(
            (ROOT / "packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark/colors").read_bytes(),
            (ROOT / "packaging/color-schemes/IFBA-OS-Dark.colors").read_bytes(),
        )
        self.assertFalse(any("wallpaper" in path.name.lower() for path in (ROOT / "packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark").rglob("*")))
        component_roots = (
            ROOT / "packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark",
            ROOT / "packaging/plasma/window-decoration/IFBA-Window",
            ROOT / "packaging/kvantum",
        ) + tuple(sorted((ROOT / "packaging/plasma/window-decoration").glob("IFBA-Window_x*")))
        for component_root in component_roots:
            for path in component_root.rglob("*"):
                self.assertNotIn(path.name, {"install.sh", "uninstall.sh"})
                if path.suffix == ".svg":
                    ET.parse(path)
                elif path.suffix == ".svgz":
                    ET.fromstring(gzip.decompress(path.read_bytes()))
        self.assertFalse(any(path.suffix == ".sh" for component_root in component_roots for path in component_root.rglob("*")))

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
        self.assertLess(sequence.index("grubcfg"), sequence.index("bootloader"))
        self.assertIn("/work/packaging/calamares/grubcfg.conf",
                      (ROOT / "scripts/build-iso-container.sh").read_text())

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
        self.assertIn('codium="${CODIUM_VERSION}" libreoffice-writer gcompris-qt', build)
        self.assertTrue({"codium", "libreoffice-writer", "gcompris-qt"}.issubset(installed_tools))
        self.assertNotIn('("Thonny"', source)
        self.assertIn('("VSCodium", "Editor de código e desenvolvimento", "codium", ())', source)
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

    def test_vscodium_is_pinned_and_verified_for_both_supported_architectures(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        tools = json.loads((ROOT / "config/educational-apps.json").read_text())
        entry = next(item for item in tools if item["id"] == "vscodium")

        self.assertIn("CODIUM_VERSION=1.143.17232", build)
        self.assertIn("https://repo.vscodium.dev/vscodium.gpg", build)
        self.assertIn("9F82ADC6B981F9FE752D1E84EFA45D2860299280", build)
        self.assertIn("https://repo.vscodium.dev/deb", build)
        self.assertIn("Architectures: amd64 arm64", build)
        self.assertIn("988330df203f4d2dbfb9ee0052a0356a27af7c0a2a7ff606424c531ae4a7b538", build)
        self.assertIn("7b0c60ea1592287d44669a63ac09092790f05bbd119e3bccc3f94d7722dcef79", build)
        self.assertIn('codium="${CODIUM_VERSION}"', build)
        self.assertIn("apt-get purge -y thonny", build)
        self.assertIn("dpkg-query -W -f='${Version}' codium", build)
        self.assertEqual(entry["package"], "codium")
        self.assertEqual(entry["version"], "1.143.17232")
        self.assertEqual(entry["status"], "installed")


if __name__ == "__main__":
    unittest.main()
