"""Regression checks for the native Plasma lock screen configuration."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.migrate_plasma_control_center import migrate as migrate_control_center


ROOT = Path(__file__).resolve().parents[1]


class PlasmaNativeLockTests(unittest.TestCase):
    def test_new_and_live_profiles_select_the_stock_plasma_shell(self):
        defaults = (ROOT / "packaging/plasma/ifba-os/contents/defaults").read_text()
        shell_config = (ROOT / "packaging/plasma/ifba-os-shell.conf").read_text()
        build = (ROOT / "scripts/build-iso-container.sh").read_text()

        self.assertIn("ShellPackage=org.kde.plasma.desktop", defaults)
        self.assertIn("ShellPackage=org.kde.plasma.desktop", shell_config)
        self.assertNotIn("migrate_plasma_shell.py", build)
        self.assertNotIn("migrate_plasma_control_center.py", build)
        self.assertIn('test ! -e "$ROOTFS/usr/share/plasma/shells/org.ifbaos.plasma"', build)
        self.assertIn("org.kde.plasma.desktop/contents/lockscreen/LockScreenUi.qml", build)
        self.assertNotIn("package_plasma_lockscreen.py", build)
        self.assertNotIn("/work/packaging/plasma/ifbaos-shell/contents/lockscreen", build)
        self.assertIn("test ! -e \"$ROOTFS/usr/share/plasma/plasmoids/org.ifbaos.controlcenter\"", build)

    def test_migration_changes_only_the_retired_shell_selector(self):
        migration = ROOT / "tools/migrate_plasma_shell.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "plasmashellrc"
            before = "[Shell]\nShellPackage=org.ifbaos.plasma\n[General]\nFoo=bar\n"
            config.write_text(before)

            subprocess.run([sys.executable, str(migration), str(config)], check=True)
            after = config.read_text()
            self.assertEqual(
                after,
                "[Shell]\nShellPackage=org.kde.plasma.desktop\n[General]\nFoo=bar\n",
            )
            subprocess.run([sys.executable, str(migration), str(config)], check=True)
            self.assertEqual(config.read_text(), after)

    def test_unrelated_user_shell_choice_is_preserved(self):
        migration = ROOT / "tools/migrate_plasma_shell.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "plasmashellrc"
            before = "[Shell]\nShellPackage=com.example.custom\n[General]\nFoo=bar\n"
            config.write_text(before)

            subprocess.run([sys.executable, str(migration), str(config)], check=True)
            self.assertEqual(config.read_text(), before)

    def test_cached_panel_migration_removes_only_retired_control_center_widget(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            appletsrc = Path(temp_dir) / "plasma-org.kde.plasma.desktop-appletsrc"
            before = (
                "[Containments][1][Applets]\nAppletOrder=10;11;12;\n"
                "[Containments][1][Applets][10]\nplugin=org.kde.plasma.systemtray\n"
                "[Containments][1][Applets][11]\nplugin=org.ifbaos.controlcenter\n"
                "[Containments][1][Applets][11][Configuration]\nfoo=bar\n"
                "[Containments][1][Applets][12]\nplugin=com.github.mattanis.macosdock\n"
            )
            appletsrc.write_text(before)

            self.assertTrue(migrate_control_center(appletsrc))
            after = appletsrc.read_text()
            self.assertNotIn("org.ifbaos.controlcenter", after)
            self.assertNotIn("foo=bar", after)
            self.assertIn("AppletOrder=10;12;", after)
            self.assertIn("plugin=org.kde.plasma.systemtray", after)
            self.assertIn("plugin=com.github.mattanis.macosdock", after)
            self.assertFalse(migrate_control_center(appletsrc))
            self.assertEqual(appletsrc.read_text(), after)

    def test_ifba_lock_wallpaper_remains_on_native_kde_locker(self):
        config = (ROOT / "packaging/plasma/ifba-os-lockscreen.conf").read_text()
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        self.assertIn("WallpaperPlugin=org.kde.image", config)
        self.assertIn("Image=/usr/share/backgrounds/ifba-os/lockscreen-wallpaper.png", config)
        self.assertIn("/etc/skel/.config/kscreenlockerrc", build)
        self.assertIn("/etc/xdg/kscreenlockerrc", build)


if __name__ == "__main__":
    unittest.main()
