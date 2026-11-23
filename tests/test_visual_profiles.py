import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packaging/ifba-visual-profile"
MOTION_TOKENS = json.loads((ROOT / "packaging/design-system/tokens.json").read_text())["motion"]


class VisualProfileTests(unittest.TestCase):
    def test_profile_script_is_valid_shell_and_packaged_as_user_tool(self):
        subprocess.run(["sh", "-n", str(SCRIPT)], check=True)
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        desktop = (ROOT / "packaging/ifba-visual-profile.desktop").read_text()
        self.assertIn("/work/packaging/ifba-visual-profile", build)
        self.assertIn("/usr/bin/ifba-visual-profile", build)
        self.assertIn("ifba-visual-profile-dialog", desktop)
        self.assertIn("kdialog", (ROOT / "packaging/ifba-visual-profile-dialog").read_text())

    def test_profiles_write_blur_and_native_minimize_animation(self):
        standard = str(MOTION_TOKENS["duration_standard_ms"])
        slow = str(MOTION_TOKENS["duration_slow_ms"])
        expected = {
            "leve": ("false", "0", "false", standard),
            "equilibrado": ("true", "2", "true", standard),
            "avancado": ("true", "4", "true", slow),
        }
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "calls"
            stub_dir = Path(directory) / "bin"
            stub_dir.mkdir()
            for command in ("kwriteconfig6", "qdbus6", "kreadconfig6"):
                stub = stub_dir / command
                if command == "kwriteconfig6":
                    stub.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$PROFILE_LOG"\n')
                elif command == "kreadconfig6":
                    stub.write_text('''#!/bin/sh
case "$*" in
  *visual-motionrc*DurationStandardMs*) printf '%s\\n' "${MOTION_STANDARD_MS:-180}" ;;
  *visual-motionrc*DurationSlowMs*) printf '%s\\n' "${MOTION_SLOW_MS:-240}" ;;
  *Kvantum*) printf '%s\\n' "${QT_THEME:-PersonalTheme}" ;;
  *kdeglobals*) printf '%s\\n' "${MOTION_FACTOR:-1}" ;;
  *) printf '1\\n' ;;
esac
''')
                else:
                    stub.write_text("#!/bin/sh\nexit 0\n")
                stub.chmod(0o755)

            for name, (enabled, strength, magiclamp, duration) in expected.items():
                log.write_text("")
                environment = os.environ | {
                    "PATH": f"{stub_dir}:/usr/bin:/bin",
                    "PROFILE_LOG": str(log),
                    "MOTION_STANDARD_MS": standard,
                    "MOTION_SLOW_MS": slow,
                }
                result = subprocess.run(["sh", str(SCRIPT), name], env=environment, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = log.read_text().splitlines()
                self.assertEqual(len(calls), 15)
                self.assertIn(f"--group Plugins --key blurEnabled {enabled}", calls[0])
                self.assertIn(f"--group Effect-Blur --key BlurStrength {strength}", calls[1])
                self.assertIn(f"--group Plugins --key magiclampEnabled {magiclamp}", calls[2])
                self.assertIn(f"--group Effect-magiclamp --key AnimationDuration {duration}", calls[3])
                self.assertTrue(all("kwinrc" in call for call in calls))
                animated = "false" if name == "leve" else "true"
                self.assertIn("--key squashEnabled false", calls[4])
                self.assertIn("--key fadeEnabled false", calls[5])
                for index in (6, 7, 8):
                    self.assertTrue(calls[index].endswith(animated))
                self.assertIn(f"--key slidingpopupsEnabled {animated}", calls[11])
                self.assertIn(f"--key fadingpopupsEnabled {animated}", calls[12])
                self.assertIn(f"--key SlideInTime {duration}", calls[13])

            for selected, expected_theme in (("IFBA-Glass", "IFBA-Glass-Opaque"), ("IFBA-Glass-Opaque", "IFBA-Glass-Opaque"), ("PersonalTheme", None)):
                log.write_text("")
                environment["QT_THEME"] = selected
                subprocess.run(["sh", str(SCRIPT), "leve"], env=environment, check=True, capture_output=True)
                theme_calls = [line for line in log.read_text().splitlines() if "--file Kvantum/" in line]
                if expected_theme:
                    self.assertEqual(len(theme_calls), 1)
                    self.assertTrue(theme_calls[0].endswith(expected_theme))
                else:
                    self.assertEqual(theme_calls, [])

    def test_reduced_motion_preference_disables_magic_lamp_without_changing_preference(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "calls"
            stub_dir = Path(directory) / "bin"
            stub_dir.mkdir()
            (stub_dir / "kwriteconfig6").write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$PROFILE_LOG"\n')
            (stub_dir / "kreadconfig6").write_text('''#!/bin/sh
case "$*" in
  *visual-motionrc*DurationStandardMs*) printf '%s\\n' "${MOTION_STANDARD_MS:-180}" ;;
  *visual-motionrc*DurationSlowMs*) printf '%s\\n' "${MOTION_SLOW_MS:-240}" ;;
  *Kvantum*) printf '%s\\n' "${QT_THEME:-PersonalTheme}" ;;
  *kdeglobals*) printf '%s\\n' "${MOTION_FACTOR:-1}" ;;
  *) printf '1\\n' ;;
esac
''')
            (stub_dir / "qdbus6").write_text("#!/bin/sh\nexit 0\n")
            for stub in stub_dir.iterdir():
                stub.chmod(0o755)
            environment = os.environ | {
                "PATH": f"{stub_dir}:/usr/bin:/bin",
                "PROFILE_LOG": str(log),
                "MOTION_FACTOR": "0.0000",
                "MOTION_STANDARD_MS": str(MOTION_TOKENS["duration_standard_ms"]),
                "MOTION_SLOW_MS": str(MOTION_TOKENS["duration_slow_ms"]),
            }
            result = subprocess.run(["sh", str(SCRIPT), "avancado"], env=environment, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = log.read_text().splitlines()
            self.assertIn("--group Plugins --key magiclampEnabled false", calls[2])
            self.assertIn("--group Plugins --key slidingpopupsEnabled false", calls[11])
            self.assertIn("--group Plugins --key fadingpopupsEnabled false", calls[12])
            self.assertIn(
                f"--group Effect-magiclamp --key AnimationDuration {MOTION_TOKENS['duration_slow_ms']}",
                calls[3],
            )
            self.assertNotRegex("\n".join(calls), r"--group KDE|AnimationDurationFactor|AnimationSpeed")

    def test_invalid_profile_fails_without_writing_settings(self):
        result = subprocess.run(["sh", str(SCRIPT), "unknown"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Uso:", result.stderr)

    def test_accessibility_animation_setting_is_never_changed(self):
        script = SCRIPT.read_text()
        self.assertNotIn("AnimationSpeed", script)
        self.assertIn("--key AnimationDurationFactor --default 1", script)
        self.assertIn("factor + 0 == 0", script)
        self.assertNotRegex(script, r"kwriteconfig6[^\n]*AnimationDurationFactor")
        self.assertNotRegex(script, r"\bsudo\s")
        defaults = (ROOT / "packaging/plasma/ifba-os/contents/defaults").read_text()
        self.assertIn("[kwinrc][Effect-Blur]\nBlurStrength=2", defaults)
        self.assertIn(f"[kwinrc][Effect-magiclamp]\nAnimationDuration={MOTION_TOKENS['duration_standard_ms']}", defaults)
        self.assertIn("magiclampEnabled=true", defaults)
        motion_profile = (ROOT / "packaging/design-system/visual-motionrc").read_text()
        self.assertIn(f"DurationStandardMs={MOTION_TOKENS['duration_standard_ms']}", motion_profile)
        self.assertIn(f"DurationSlowMs={MOTION_TOKENS['duration_slow_ms']}", motion_profile)
        self.assertIn("design-system/visual-motionrc", (ROOT / "scripts/build-iso-container.sh").read_text())

    def test_sddm_keeps_native_breeze_theme_with_ifba_branding(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        theme = (ROOT / "packaging/sddm/ifba-theme.conf.user").read_text()
        self.assertIn("/usr/share/sddm/themes/breeze/theme.conf.user", build)
        self.assertIn("logo=/usr/share/ifba-os/assets/icons/ifba-institutional-symbol.png", theme)
        self.assertIn("iconTheme=breeze-dark", theme)
        self.assertIn("type=image", theme)
        self.assertIn("color=#222A34", theme)
        self.assertIn("background=/usr/share/backgrounds/ifba-os/campus-jacobina.jpg", theme)
        self.assertIn("/work/assets/wallpapers/ifba-os-campus-jacobina.jpg", build)
        appearance = (ROOT / "packaging/sddm/20-ifba-appearance.conf").read_text()
        self.assertEqual(appearance.splitlines(), [
            "[General]", "GreeterEnvironment=QT_QPA_PLATFORMTHEME=kde", "",
            "[Theme]", "Current=breeze", "CursorTheme=breeze_cursors",
        ])
        self.assertIn('/etc/sddm.conf.d/20-ifba-appearance.conf', build)
        self.assertIn('if [[ ! -e "$ROOTFS/var/lib/sddm/.config/kdeglobals" ]]; then', build)
        cleanup = (ROOT / "packaging/calamares/shellprocess.conf").read_text()
        self.assertIn("rm -f /etc/sddm.conf.d/10-ifba-os.conf", cleanup)
        self.assertNotIn("20-ifba-appearance.conf", cleanup)


if __name__ == "__main__":
    unittest.main()
