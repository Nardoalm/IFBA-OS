"""Optional runtime regression for Plasma 6 in a disposable Xvfb session."""

import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("plasmashell", "dbus-run-session", "xvfb-run", "xauth", "qdbus6")


@unittest.skipUnless(all(shutil.which(tool) for tool in REQUIRED), "requires Plasma 6 and Xvfb")
class PlasmaFirstLoginTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.home = Path(self.directory.name)
        self.config = self.home / ".config"
        self.config.mkdir()
        self.applets = self.config / "plasma-org.kde.plasma.desktop-appletsrc"
        # Seed an activity that survives separate test D-Bus sessions. Plasma
        # discards desktop containments whose activity no longer exists.
        self.activity = "b290f06d-605a-407f-8c30-bac52c025e1d"
        (self.config / "kactivitymanagerdrc").write_text(f"[activities]\n{self.activity}=Default\n")
        (self.config / "kdeglobals").write_text("[KDE]\nLookAndFeelPackage=org.ifbaos.desktop\n")
        data = self.home / ".local/share/plasma"
        shutil.copytree(ROOT / "packaging/plasma/ifba-os", data / "look-and-feel/org.ifbaos.desktop")
        plasmoids = data / "plasmoids"
        plasmoids.mkdir()
        (plasmoids / "com.github.mattanis.macosdock").symlink_to(ROOT / "packaging/plasma/ifba-dock")
        runtime = self.home / "runtime"
        runtime.mkdir(mode=0o700)
        self.env = os.environ | {
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.config),
            "XDG_DATA_HOME": str(data.parent),
            "XDG_CACHE_HOME": str(self.home / ".cache"),
            "XDG_RUNTIME_DIR": str(runtime),
            "QT_QPA_PLATFORM": "xcb",
            "QT_QUICK_BACKEND": "software",
            "XDG_SESSION_TYPE": "x11",
            "XDG_CURRENT_DESKTOP": "KDE",
        }

    def start_plasma(self, expected):
        log = self.home / "plasmashell.log"
        state_file = self.home / "live-state.json"
        state_file.unlink(missing_ok=True)
        stop_file = self.home / "stop"
        stop_file.unlink(missing_ok=True)
        query = """
            print(JSON.stringify({
                panels: panels().map(panel => panel.id),
                desktops: desktops().map(desktop => {
                    desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
                    return desktop.readConfig("Image", "");
                })
            }))
        """
        probe = """
            plasmashell --no-respawn &
            shell=$!
            while kill -0 "$shell" 2>/dev/null; do
                if [ -e "$3" ]; then
                    qdbus6 org.kde.plasmashell /MainApplication quit
                    break
                fi
                if qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$2" \
                    >"$1.tmp" 2>/dev/null; then
                    mv "$1.tmp" "$1"
                fi
                sleep 0.1
            done
            wait "$shell"
        """
        with log.open("w") as output, subprocess.Popen(
            ["xvfb-run", "-a", "dbus-run-session", "--", "sh", "-c", probe, "probe", str(state_file), query, str(stop_file)],
            env=self.env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True,
        ) as process:
            try:
                deadline = time.monotonic() + 35
                content = ""
                while process.poll() is None and time.monotonic() < deadline:
                    content = self.applets.read_text() if self.applets.is_file() else ""
                    if state_file.is_file():
                        response = state_file.read_text().strip()
                        live_state = json.loads(response) if response.startswith("{") else None
                        if live_state and live_state["desktops"] and expected(content, live_state):
                            stop_file.touch()
                            self.assertEqual(process.wait(timeout=10), 0)
                            return self.applets.read_text(), live_state
                    time.sleep(0.1)
                state = state_file.read_text() if state_file.is_file() else "(unavailable)"
                self.fail(f"Plasma state: {state}\nSaved layout:\n{content[:3000]}\n{log.read_text()[-1500:]}")
            finally:
                # Everything in this process group belongs to the disposable session.
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                process.wait(timeout=10)

    @staticmethod
    def has_ifba_layout(content, live_state):
        wallpaper = "file:///usr/share/backgrounds/ifba-os/wallpaper.png"
        return (
            len(live_state["panels"]) == 2
            and all(image == wallpaper for image in live_state["desktops"])
            and content.count("plugin=org.kde.panel\n") == 2
            and "plugin=com.github.mattanis.macosdock\n" in content
            and f"Image={wallpaper}\n" in content
        )

    def test_first_login_and_second_login_reuse_the_same_containments(self):
        _, first = self.start_plasma(self.has_ifba_layout)
        _, second = self.start_plasma(self.has_ifba_layout)
        self.assertEqual(sorted(first["panels"]), sorted(second["panels"]))

    def test_screen_mapping_without_saved_containments_can_initialize(self):
        self.applets.write_text("[ScreenMapping]\nitemsOnDisabledScreens=\n")
        self.start_plasma(self.has_ifba_layout)

    def test_existing_desktop_without_panels_is_preserved(self):
        personal_path = self.home / "personal.png"
        shutil.copyfile(ROOT / "assets/wallpapers/ifba-os-desktop.png", personal_path)
        personal = personal_path.as_uri()
        self.applets.write_text(
            f"[Containments][1]\nactivityId={self.activity}\nformfactor=0\nimmutability=1\n"
            "lastScreen=0\nlocation=0\nplugin=org.kde.plasma.folder\nwallpaperplugin=org.kde.image\n\n"
            f"[Containments][1][Wallpaper][org.kde.image][General]\nImage={personal}\n"
        )
        content, state = self.start_plasma(
            lambda saved, live: live["desktops"] == [personal] and f"Image={personal}\n" in saved
        )
        self.assertEqual(state["panels"], [])
        self.assertNotIn("plugin=org.kde.panel\n", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
