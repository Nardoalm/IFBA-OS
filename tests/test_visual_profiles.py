import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packaging/ifba-visual-profile"


class VisualProfileTests(unittest.TestCase):
    def test_profile_script_is_valid_shell_and_packaged_as_user_tool(self):
        subprocess.run(["sh", "-n", str(SCRIPT)], check=True)
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        desktop = (ROOT / "packaging/ifba-visual-profile.desktop").read_text()
        self.assertIn("/work/packaging/ifba-visual-profile", build)
        self.assertIn("/usr/bin/ifba-visual-profile", build)
        self.assertIn("ifba-visual-profile-dialog", desktop)
        self.assertIn("kdialog", (ROOT / "packaging/ifba-visual-profile-dialog").read_text())

    def test_profiles_write_only_current_users_blur_settings(self):
        expected = {
            "leve": ("false", "0"),
            "equilibrado": ("true", "2"),
            "avancado": ("true", "4"),
        }
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "calls"
            stub_dir = Path(directory) / "bin"
            stub_dir.mkdir()
            for command in ("kwriteconfig6", "qdbus6"):
                stub = stub_dir / command
                if command == "kwriteconfig6":
                    stub.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$PROFILE_LOG"\n')
                else:
                    stub.write_text("#!/bin/sh\nexit 0\n")
                stub.chmod(0o755)

            for name, (enabled, strength) in expected.items():
                log.write_text("")
                environment = os.environ | {
                    "PATH": f"{stub_dir}:/usr/bin:/bin",
                    "PROFILE_LOG": str(log),
                }
                result = subprocess.run(["sh", str(SCRIPT), name], env=environment, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = log.read_text().splitlines()
                self.assertEqual(len(calls), 2)
                self.assertIn(f"--group Plugins --key blurEnabled {enabled}", calls[0])
                self.assertIn(f"--group Effect-Blur --key BlurStrength {strength}", calls[1])
                self.assertTrue(all("kwinrc" in call for call in calls))

    def test_invalid_profile_fails_without_writing_settings(self):
        result = subprocess.run(["sh", str(SCRIPT), "unknown"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Uso:", result.stderr)

    def test_accessibility_animation_setting_is_never_changed(self):
        script = SCRIPT.read_text()
        self.assertNotIn("AnimationSpeed", script)
        self.assertNotIn("AnimationDurationFactor", script)
        self.assertNotRegex(script, r"\bsudo\s")
        defaults = (ROOT / "packaging/plasma/ifba-os/contents/defaults").read_text()
        self.assertIn("[kwinrc][Effect-Blur]\nBlurStrength=2", defaults)

    def test_sddm_keeps_native_breeze_theme_with_ifba_branding(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        theme = (ROOT / "packaging/sddm/ifba-theme.conf.user").read_text()
        self.assertIn("/usr/share/sddm/themes/breeze/theme.conf.user", build)
        self.assertIn("logo=/usr/share/ifba-os/assets/icons/ifba-institutional-symbol.png", theme)
        self.assertIn("color=#22C55E", theme)
        self.assertIn("background=/usr/share/backgrounds/ifba-os/lockscreen-wallpaper.png", theme)


if __name__ == "__main__":
    unittest.main()
