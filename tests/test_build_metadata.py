import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_metadata


class BuildMetadataTests(unittest.TestCase):
    def test_embedded_metadata_identifies_version_commit_and_dirty_source(self):
        info = build_metadata.build_info(
            "ifba-20261119T120000Z-abcdef123456",
            "abcdef1234567890",
            "2026-11-19T12:00:00Z",
            "true",
        )
        self.assertEqual(info["build_id"], "ifba-20261119T120000Z-abcdef123456")
        self.assertEqual(info["source_commit"], "abcdef1234567890")
        self.assertTrue(info["source_dirty"])
        self.assertEqual(info["base"], "Ubuntu 24.04 LTS")

    def test_iso_manifest_records_sha256_and_exact_size(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            build_path = directory / "build-info.json"
            iso_path = directory / "test.iso"
            manifest_path = directory / "test.iso.manifest.json"
            build_metadata.write_json(
                build_path,
                build_metadata.build_info("build-1", "abcdef", "2026-11-19T12:00:00Z", "false"),
            )
            payload = b"IFBA OS iso fixture\n"
            iso_path.write_bytes(payload)
            build_metadata.write_iso_manifest(build_path, iso_path, manifest_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["artifact"]["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(manifest["artifact"]["size_bytes"], len(payload))
            self.assertEqual(manifest["artifact"]["file"], "test.iso")

    def test_version_command_prints_embedded_build_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "build-info.json"
            manifest.write_text(
                json.dumps(
                    {
                        "system_version": "0.1.0",
                        "build_id": "ifba-build-7",
                        "source_commit": "1234567890abcdef",
                        "build_date_utc": "2026-11-19T12:00:00Z",
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [str(ROOT / "tools/ifba-os-version"), str(manifest)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Build ID: ifba-build-7", result.stdout)
            self.assertIn("Source commit: 1234567890abcdef", result.stdout)

    def test_iso_build_has_provenance_and_required_rootfs_guards(self):
        host_build = (ROOT / "scripts/build-iso.sh").read_text(encoding="utf-8")
        container_build = (ROOT / "scripts/build-iso-container.sh").read_text(encoding="utf-8")
        self.assertIn("IFBA_BUILD_CACHE_VOLUME", host_build)
        self.assertIn("build-info", host_build)
        self.assertIn("iso-manifest", host_build)
        for required in (
            "wallpaper.png",
            "Yaru-dark/xfwm4/themerc",
            "xfce4-panel.xml",
            "firefox.desktop",
            "ifba-ai.desktop",
            "suap-ifba.desktop",
            "ava-ifba.desktop",
            "ifba-wired.nmconnection",
            "build-info.json",
        ):
            self.assertIn(required, container_build)
        self.assertIn("cmp -s /work/packaging/xfce4-panel.xml", container_build)


if __name__ == "__main__":
    unittest.main()
