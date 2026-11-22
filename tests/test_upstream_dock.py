"""Contracts for the vendored, CPU-independent upstream dock."""
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class UpstreamDockTests(unittest.TestCase):
    def test_config_and_pinned_source(self):
        dock = ROOT / "packaging/plasma/ifba-dock"
        manifest = json.loads((ROOT / "packaging/third-party/plasma-macos-dock/manifest.json").read_text())
        self.assertEqual(manifest["commit"], "ba4f0551ac9c71e9a777451aa1c43db144a10156")
        omitted_icon = "contents/icons/com.github.mattanis.macosdock.png"
        self.assertIn(omitted_icon, manifest["omitted_assets"])
        self.assertFalse((ROOT / "packaging/plasma/ifba-dock" / omitted_icon).exists())
        ET.parse(dock / "contents/config/main.xml")
        metadata = json.loads((dock / "metadata.json").read_text())
        self.assertEqual(metadata["KPlugin"]["Id"], "com.github.mattanis.macosdock")
        self.assertEqual(metadata["KPlugin"]["Icon"], "preferences-desktop-icons")
        self.assertTrue((ROOT / "packaging/third-party/plasma-macos-dock/GPL-2.0-or-later.txt").is_file())
        self.assertTrue((ROOT / "packaging/third-party/plasma-macos-dock/LGPL-2.0-or-later.txt").is_file())

    def test_unmodified_sources_match_recorded_upstream(self):
        import hashlib
        manifest = json.loads((ROOT / "packaging/third-party/plasma-macos-dock/manifest.json").read_text())
        adapted = {
            "contents/config/main.xml",  # remove upstream's extra blank line at EOF
            "contents/ui/code/LayoutMetrics.js",  # same whitespace-only normalization
            "contents/ui/main.qml",
            "contents/ui/Task.qml",
        }
        for name, digest in manifest["files"].items():
            if name not in adapted:
                self.assertEqual(hashlib.sha256((ROOT / "packaging/plasma/ifba-dock" / name).read_bytes()).hexdigest(), digest, name)

    def test_accessibility_and_pipeline(self):
        dock = ROOT / "packaging/plasma/ifba-dock/contents/ui"
        for name in ("main.qml", "Task.qml"):
            self.assertIn("Kirigami.Units.longDuration > 1", (dock / name).read_text())
        background = (dock / "LiquidGlassBackground.qml").read_text()
        self.assertIn('(root.backgroundType === 3 || root.backgroundType === 4) && root.hasBlurPlugin', background)
        self.assertIn('visible: root.backgroundType === 2 || root.backgroundType === 3', background)
        self.assertIn("blurOpacity", background)
        layout = (ROOT / "packaging/plasma/ifba-os/contents/layouts/org.kde.plasma.desktop-layout.js").read_text()
        self.assertIn('tasks.writeConfig("zoomAnimationType", 1)', layout)
        self.assertIn('tasks.writeConfig("containerBackgroundType", 3)', layout)
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        self.assertIn("/work/packaging/plasma/ifba-dock/.", build)
        self.assertIn("/work/packaging/third-party/plasma-macos-dock/.", build)
        self.assertIn('qmlformat "/usr/share/plasma/plasmoids/com.github.mattanis.macosdock/', build)
