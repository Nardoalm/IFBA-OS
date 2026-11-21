"""Tests for the version-matched Plasma shell lock-screen overlay."""

import json
from pathlib import Path
import tempfile
import unittest

from tools.package_plasma_lockscreen import prepare


ROOT = Path(__file__).resolve().parents[1]
LOCKSCREEN = ROOT / "packaging/plasma/ifbaos-shell/contents/lockscreen"


class PlasmaLockScreenPackagingTests(unittest.TestCase):
    def make_rootfs(self, root: Path) -> Path:
        package = root / "usr/share/plasma/shells/org.kde.plasma.desktop"
        (package / "contents/lockscreen").mkdir(parents=True)
        metadata = {
            "KPackageStructure": "Plasma/Shell",
            "KPlugin": {"Id": "org.kde.plasma.desktop", "Name": "Plasma Desktop"},
            "X-Plasma-APIVersion": "2",
        }
        (package / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
        (package / "contents/lockscreen/Stock.qml").write_text("stock", encoding="utf-8")
        return package

    def test_derives_shell_without_modifying_installed_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            rootfs = Path(tmp)
            original = self.make_rootfs(rootfs)
            original_metadata = (original / "metadata.json").read_bytes()

            target = prepare(rootfs, LOCKSCREEN)

            metadata = json.loads((target / "metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["KPackageStructure"], "Plasma/Shell")
            self.assertEqual(metadata["KPlugin"]["Id"], "org.ifbaos.plasma")
            self.assertTrue((target / "contents/lockscreen/Stock.qml").is_file())
            for filename in ("LockScreen.qml", "LockScreenUi.qml"):
                self.assertEqual(
                    (target / "contents/lockscreen" / filename).read_bytes(),
                    (LOCKSCREEN / filename).read_bytes(),
                )
            self.assertEqual((original / "metadata.json").read_bytes(), original_metadata)
            self.assertEqual(
                (original / "contents/lockscreen/Stock.qml").read_text(encoding="utf-8"),
                "stock",
            )

    def test_refuses_non_shell_or_old_api_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            rootfs = Path(tmp)
            original = self.make_rootfs(rootfs)
            metadata = json.loads((original / "metadata.json").read_text(encoding="utf-8"))
            metadata["X-Plasma-APIVersion"] = "1"
            (original / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare(rootfs, LOCKSCREEN)
            self.assertFalse((rootfs / "usr/share/plasma/shells/org.ifbaos.plasma").exists())

    def test_authentication_stays_with_kscreenlocker_and_system_actions(self):
        ui = (LOCKSCREEN / "LockScreenUi.qml").read_text(encoding="utf-8")
        root = (LOCKSCREEN / "LockScreen.qml").read_text(encoding="utf-8")
        defaults = (ROOT / "packaging/plasma/ifba-os/contents/defaults").read_text(encoding="utf-8")
        shell_config = (ROOT / "packaging/plasma/ifba-os-shell.conf").read_text(encoding="utf-8")
        build = (ROOT / "scripts/build-iso-container.sh").read_text(encoding="utf-8")

        for required in (
            "authenticator.startAuthenticating()",
            "authenticator.respond(passwordField.text)",
            "authenticator.hadPrompt",
            "authenticator.graceLocked",
            "onPromptForSecretChanged",
            "KeyboardIndicator.KeyState",
            "sessionManagement.canShutdown",
            "sessionManagement.requestShutdown()",
            "sessionManagement.canReboot",
            "sessionManagement.requestReboot()",
            "sessionManagement.canSwitchUser",
            "sessionManagement.switchUser()",
            "PlasmaNM.NetworkStatus",
            "PlasmaNM.ConnectionIcon",
            "PlasmaVolume.PreferredDevice.sink",
            "Battery {}",
            'Qt.formatTime(ui.now, "HH:mm")',
            'Qt.locale("pt_BR")',
        ):
            self.assertIn(required, ui)
        self.assertIn("unlockRequested()", root)
        self.assertIn("ShellPackage=org.ifbaos.plasma", defaults)
        self.assertIn("ShellPackage=org.ifbaos.plasma", shell_config)
        self.assertIn("package_plasma_lockscreen.py", build)
        self.assertIn("$ROOTFS/etc/xdg/plasmashellrc", build)
        self.assertIn("$ROOTFS/etc/skel/.config/plasmashellrc", build)
        self.assertIn("$ROOTFS/home/ubuntu/.config/plasmashellrc", build)
        self.assertNotIn('text: "IFBA OS"', ui)
        self.assertNotIn("Apple", ui)


if __name__ == "__main__":
    unittest.main()
