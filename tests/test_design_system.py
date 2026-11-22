import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKENS_PATH = ROOT / "packaging/design-system/tokens.json"


def luminance(hex_color):
    values = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    channels = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in values]
    return sum(channel * weight for channel, weight in zip(channels, (0.2126, 0.7152, 0.0722)))


def contrast(first, second):
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


class DesignSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokens = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
        cls.colors = cls.tokens["colors"]
        cls.build = (ROOT / "scripts/build-iso-container.sh").read_text(encoding="utf-8")

    def test_generated_desktop_assets_are_current(self):
        subprocess.run(
            [sys.executable, str(ROOT / "tools/generate_design_system.py"), "--check"],
            cwd=ROOT,
            check=True,
        )

    def test_primary_text_and_interactive_states_meet_contrast_target(self):
        for foreground, background in (
            (self.colors["text_primary"], self.colors["background"]),
            (self.colors["text_primary"], self.colors["surface"]),
            (self.colors["text_secondary"], self.colors["background"]),
            (self.colors["text_secondary"], self.colors["surface"]),
            (self.colors["background"], self.colors["accent"]),
        ):
            with self.subTest(foreground=foreground, background=background):
                self.assertGreaterEqual(contrast(foreground, background), 4.5)

    def test_kde_gtk_konsole_and_aurorae_share_palette_tokens(self):
        color_scheme = (ROOT / "packaging/color-schemes/IFBA-OS-Dark.colors").read_text()
        gtk_css = (ROOT / "packaging/gtk/gtk.css").read_text()
        assistant_css = (ROOT / "packaging/ifba-ai.css").read_text()
        terminal = (ROOT / "packaging/konsole/IFBA Glass.colorscheme").read_text()
        decoration = ROOT / "packaging/plasma/window-decoration/IFBA-Window"
        plasma_colors = (ROOT / "packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark/colors").read_text()
        kvantum = (ROOT / "packaging/kvantum/IFBA-Glass/IFBA-Glass.kvconfig").read_text()
        kvantum_svg = (ROOT / "packaging/kvantum/IFBA-Glass/IFBA-Glass.svg").read_text()
        for color in ("background", "surface", "surface_elevated", "accent", "text_primary", "text_secondary"):
            with self.subTest(token=color):
                self.assertIn(",".join(str(int(self.colors[color][i:i + 2], 16)) for i in (1, 3, 5)), color_scheme)
                self.assertIn(self.colors[color], gtk_css)
                self.assertIn(self.colors[color], assistant_css)
                self.assertIn(",".join(str(int(self.colors[color][i:i + 2], 16)) for i in (1, 3, 5)), terminal)
                self.assertIn(",".join(str(int(self.colors[color][i:i + 2], 16)) for i in (1, 3, 5)), plasma_colors)
        self.assertIn(self.colors["border"], gtk_css)
        self.assertIn(self.colors["border"], assistant_css)
        self.assertIn(self.colors["accent"], (decoration / "maximize.svg").read_text())
        self.assertIn(self.colors["danger"], (decoration / "close.svg").read_text())
        self.assertIn("highlight.color=" + self.colors["accent"], kvantum)
        self.assertIn(self.colors["accent"], kvantum_svg)

    def test_build_installs_shared_defaults_for_live_and_new_users(self):
        for path in (
            "/etc/gtk-3.0/gtk.css", "/etc/gtk-3.0/settings.ini",
            "/etc/gtk-4.0/gtk.css", "/etc/gtk-4.0/settings.ini",
        ):
            self.assertIn(path, self.build)
        self.assertIn('for home_root in "$ROOTFS/etc/skel" "$ROOTFS/home/ubuntu"; do', self.build)
        for profile_path in (".config/gtk-3.0/gtk.css", ".config/gtk-4.0/gtk.css", ".config/gtk-3.0/settings.ini", ".config/gtk-4.0/settings.ini"):
            self.assertIn(f'"$home_root/{profile_path}"', self.build)
        self.assertIn("/work/packaging/color-schemes/IFBA-OS-Dark.colors", self.build)
        self.assertIn("/work/packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark", self.build)
        self.assertIn("qt-style-kvantum=1.1.5-1 qt-style-kvantum-themes=1.1.5-1", self.build)
        self.assertIn('name=IFBA-WhiteSur-Dark', (ROOT / "packaging/plasma/ifba-os/contents/defaults").read_text())
        self.assertIn("/work/packaging/gtk/gtk.css", self.build)
        self.assertIn("/work/packaging/gtk/settings.ini", self.build)
        self.assertIn("/work/packaging/design-system/ifba-welcome.qss", self.build)
        welcome = (ROOT / "welcome/ifba_welcome.py").read_text()
        self.assertIn('STYLE_PATH = Path("/usr/share/ifba-os/ifba-welcome.qss")', welcome)
        self.assertIn("self.setStyleSheet(load_style())", welcome)
        self.assertIn('except OSError:', welcome)
        self.assertIn('/usr/share/ifba-os/ifba-welcome.qss', self.build)
        release_builder = (ROOT / "scripts/build-iso.sh").read_text()
        self.assertIn('tools/generate_design_system.py" --check', release_builder)
        self.assertIn('Font=Noto Sans Mono,10', (ROOT / "packaging/konsole/IFBA Terminal.profile").read_text())

    def test_existing_live_user_preferences_are_not_replaced(self):
        self.assertIn('if [[ ! -e "$ROOTFS/home/ubuntu/.config/kdeglobals" ]]; then', self.build)
        self.assertIn('if [[ ! -e "$ROOTFS/home/ubuntu/.config/plasmarc" ]]; then', self.build)
        self.assertIn('if [[ ! -e "$ROOTFS/home/ubuntu/.config/Kvantum/kvantum.kvconfig" ]]; then', self.build)
        self.assertIn('if [[ ! -e "$ROOTFS/home/ubuntu/.config/kscreenlockerrc" ]]; then', self.build)
        self.assertIn('if [[ ! -e "$ROOTFS/home/ubuntu/.config/plasmashellrc" ]]; then', self.build)
        self.assertIn('rm -f "$ROOTFS/home/ubuntu/.config/autostart/ifba-os-plasma-session-setup.desktop"', self.build)
        self.assertIn('if [[ ! -e "$ROOTFS/home/ubuntu/Desktop/IFBA-AI.desktop" ]]; then', self.build)
        self.assertIn('if [[ ! -e "$ROOTFS/home/ubuntu/Desktop/SUAP.desktop" ]]; then', self.build)
        self.assertNotIn('chmod +x "$ROOTFS/home/ubuntu/Desktop/"*.desktop', self.build)
        self.assertIn('if [[ ! -e "$home_root/.config/gtk-3.0/gtk.css" ]]; then', self.build)
        self.assertIn('if [[ ! -e "$home_root/.config/gtk-4.0/gtk.css" ]]; then', self.build)
        self.assertIn('if [[ ! -e "$home_root/.config/gtk-3.0/settings.ini" ]]; then', self.build)
        self.assertIn('if [[ ! -e "$home_root/.config/gtk-4.0/settings.ini" ]]; then', self.build)
    def test_build_validates_plasma_theme_in_global_theme_defaults(self):
        defaults = (ROOT / "packaging/plasma/ifba-os/contents/defaults").read_text()
        self.assertIn("[plasmarc][Theme]", defaults)
        self.assertIn("name=IFBA-WhiteSur-Dark", defaults)
        self.assertIn("$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/contents/defaults", self.build)
        self.assertIn('/work/packaging/plasma/ifba-os/contents/defaults > "$ROOTFS/etc/xdg/kwinrc"', self.build)
        self.assertNotIn("grep -q '^name=IFBA-WhiteSur-Dark$' \"$ROOTFS/etc/skel/.config/plasmarc\"", self.build)


if __name__ == "__main__":
    unittest.main()
