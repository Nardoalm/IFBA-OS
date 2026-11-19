import subprocess
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class XfceDefaultsTests(unittest.TestCase):
    def test_panel_defaults_define_only_the_bottom_main_panel(self):
        channel = ET.parse(ROOT / "packaging/xfce4-panel.xml").getroot()
        panels = channel.find("property[@name='panels']")
        self.assertEqual(
            [node.attrib["value"] for node in panels.findall("value")], ["1"]
        )
        self.assertIsNotNone(panels.find("property[@name='panel-1']"))
        self.assertIsNone(panels.find("property[@name='panel-2']"))
        main_panel = panels.find("property[@name='panel-1']")
        plugin_ids = main_panel.find("property[@name='plugin-ids']")
        self.assertIsNotNone(plugin_ids)
        self.assertNotIn("15", [node.attrib["value"] for node in plugin_ids.findall("value")])
        plugins = channel.find("property[@name='plugins']")
        self.assertIsNone(plugins.find("property[@name='plugin-15']"))

    def test_default_workspace_count_is_one_and_can_remain_user_editable(self):
        channel = ET.parse(ROOT / "packaging/xfwm4.xml").getroot()
        general = channel.find("property[@name='general']")
        workspace_count = general.find("property[@name='workspace_count']")
        self.assertIsNotNone(workspace_count)
        self.assertEqual(workspace_count.attrib["value"], "1")
        self.assertNotIn("locked", workspace_count.attrib)

    def test_xfce_session_does_not_save_and_restore_old_sessions_by_default(self):
        channel = ET.parse(ROOT / "packaging/xfce4-session.xml").getroot()
        general = channel.find("property[@name='general']")
        save_on_exit = general.find("property[@name='SaveOnExit']")
        self.assertIsNotNone(save_on_exit)
        self.assertEqual(save_on_exit.attrib["value"], "false")
        failsafe_name = general.find("property[@name='FailsafeSessionName']")
        self.assertIsNotNone(failsafe_name)
        self.assertEqual(failsafe_name.attrib["value"], "Failsafe")
        failsafe = channel.find("property[@name='sessions']/property[@name='Failsafe']")
        self.assertIsNotNone(failsafe)
        self.assertEqual(
            [
                value.attrib["value"]
                for item in failsafe.findall("property")
                if item.attrib["name"].endswith("_Command")
                for value in item.findall("value")
            ],
            ["xfwm4", "xfsettingsd", "xfce4-panel", "Thunar", "--daemon", "xfdesktop"],
        )

    def test_build_installs_channel_defaults_for_live_and_future_users(self):
        script = (ROOT / "scripts/build-iso-container.sh").read_text()
        for target in (
            "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml",
            "$ROOTFS/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml",
            "$ROOTFS/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml",
            "$ROOTFS/etc/xdg/xfce4/panel/default.xml",
            "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml",
            "$ROOTFS/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml",
            "$ROOTFS/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-session.xml",
        ):
            self.assertIn(target, script)

    def test_repair_script_validates_the_session_and_never_runs_session_changes_as_root(self):
        script_path = ROOT / "tools/fix-xfce-panel.sh"
        script = script_path.read_text()
        subprocess.run(["bash", "-n", str(script_path)], check=True)
        self.assertIn("session changes must run as the logged-in desktop user, never as root", script)
        self.assertIn("panel 1 is not active; no panels were changed", script)
        self.assertIn("xfce4-panel -r", script)
        self.assertIn("--system-defaults", script)

    @unittest.skipIf(os.geteuid() == 0, "session repair intentionally refuses root")
    def test_repair_script_removes_extra_panel_and_pager_with_mocked_xfconf(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            bindir = temp / "bin"
            bindir.mkdir()
            (bindir / "pgrep").write_text("#!/bin/sh\nexit 0\n")
            (bindir / "xfce4-panel").write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$IFBA_PANEL_LOG\"\nexit 0\n"
            )
            (bindir / "xfconf-query").write_text(
                """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "$IFBA_XFCONF_LOG"
property=''
mutating=0
while (( $# > 0 )); do
  case "$1" in
    --property) property="$2"; shift 2 ;;
    --set) mutating=1; shift 2 ;;
    --reset) mutating=1; shift ;;
    --channel|--type) shift 2 ;;
    *) shift ;;
  esac
done
if (( mutating )); then
  [[ "$property" != /panels ]] || touch "$IFBA_PANELS_SET"
  exit 0
fi
case "$property" in
  /panels)
    if [[ -e "$IFBA_PANELS_SET" ]]; then
      printf 'Value is an array with 1 item:\\n1\\n'
    else
      printf 'Value is an array with 2 items:\\n1\\n2\\n'
    fi
    ;;
  /panels/panel-1/position) printf 'Value is a string: p=10;x=0;y=0\\n' ;;
  /panels/panel-1/plugin-ids) printf 'Value is an array with 14 items:\\n1\\n2\\n3\\n4\\n17\\n5\\n6\\n7\\n8\\n9\\n10\\n11\\n12\\n15\\n' ;;
  /panels/panel-2/plugin-ids) printf 'Value is an array with 3 items:\\n13\\n16\\n14\\n' ;;
  /plugins/plugin-15) printf 'Value is a string: pager\\n' ;;
  /plugins/plugin-*) printf 'Value is a string: launcher\\n' ;;
  /general/workspace_count) printf 'Value is an integer: 1\\n' ;;
  *) exit 0 ;;
esac
"""
            )
            for executable in bindir.iterdir():
                executable.chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{bindir}:{env['PATH']}",
                    "DBUS_SESSION_BUS_ADDRESS": "unix:path=/tmp/ifba-test-bus",
                    "DISPLAY": ":0",
                    "IFBA_XFCONF_LOG": str(temp / "xfconf.log"),
                    "IFBA_PANEL_LOG": str(temp / "panel.log"),
                    "IFBA_PANELS_SET": str(temp / "panels-set"),
                }
            )
            result = subprocess.run(
                [str(ROOT / "tools/fix-xfce-panel.sh"), "--session"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            log = (temp / "xfconf.log").read_text()
            self.assertIn("/panels/panel-2 --reset --recursive", log)
            self.assertIn("/plugins/plugin-15 --reset --recursive", log)
            self.assertIn("/general/workspace_count --create --type int --set 1", log)
            plugin_rewrite = next(
                line for line in log.splitlines()
                if "/panels/panel-1/plugin-ids" in line and "--set" in line
            )
            self.assertNotIn("--set 15", plugin_rewrite)
            self.assertIn("-r", (temp / "panel.log").read_text())


if __name__ == "__main__":
    unittest.main()
