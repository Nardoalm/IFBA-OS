import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / "tools/release_artifacts.py"
SPEC = importlib.util.spec_from_file_location("release_artifacts", MODULE)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


def make_artifact(root, arch, version, commit="abc123"):
    name = f"ifba-os-ubuntu-26.04-{arch}-v{version}.iso"
    path = root / name
    path.write_bytes((arch + version).encode())
    data = {
        "architecture": arch,
        "system_version": version,
        "build_id": f"test-{arch}-{version}",
        "source_commit": commit,
        "status": "unvalidated",
        "artifact": {"file": name, "sha256": release.sha256(path), "size_bytes": path.stat().st_size},
    }
    manifest = Path(str(path) + ".manifest.json")
    manifest.write_text(json.dumps(data))
    return path, manifest


class ReleaseArtifactsTests(unittest.TestCase):
    def test_migrate_preserves_hash_and_legacy_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            iso, manifest = make_artifact(root, "arm64", "0.3.0")
            expected = release.sha256(iso)
            release.migrate(root)
            target = root / "versions/v0.3.0/arm64" / iso.name
            self.assertEqual(release.sha256(target), expected)
            self.assertTrue(iso.is_symlink())
            self.assertEqual(iso.resolve(), target.resolve())
            self.assertEqual(json.loads((target.parent / "manifest.json").read_text())["architecture"], "arm64")
            latest_arm = root / "latest/arm64/manifest.json"
            self.assertTrue(latest_arm.is_symlink())
            self.assertFalse((root / "latest/amd64/manifest.json").exists())
            status = json.loads((root / "latest/release-status.json").read_text())
            self.assertFalse(status["complete_pair"])
            self.assertEqual(status["arm64"]["version"], "0.3.0")

    def test_latest_requires_same_version_and_source_commit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for arch in ("arm64", "amd64"):
                source = root / "incoming"
                source.mkdir(exist_ok=True)
                iso, manifest = make_artifact(source, arch, "0.3.2")
                release.publish(iso, manifest, root)
            for arch in ("arm64", "amd64"):
                latest = list((root / "latest" / arch).iterdir())
                self.assertEqual(len(latest), 2)
                self.assertTrue(all(p.is_symlink() for p in latest))

    def test_latest_refuses_different_source_commits(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "incoming"
            source.mkdir()
            for arch, commit in (("arm64", "abc"), ("amd64", "def")):
                iso, manifest = make_artifact(source, arch, "0.3.2", commit)
                release.publish(iso, manifest, root)
            self.assertFalse(json.loads((root / "latest/release-status.json").read_text())["complete_pair"])

    def test_unmatched_new_version_does_not_advance_latest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "incoming"
            source.mkdir()
            for arch, commit in (("arm64", "old"), ("amd64", "old")):
                iso, manifest = make_artifact(source, arch, "0.3.1", commit)
                release.publish(iso, manifest, root)
            old_target = (root / "latest/arm64/manifest.json").resolve()
            iso, manifest = make_artifact(source, "arm64", "0.3.2", "new")
            release.publish(iso, manifest, root)
            self.assertEqual((root / "latest/arm64/manifest.json").resolve(), old_target)
            status = json.loads((root / "latest/release-status.json").read_text())
            self.assertTrue(status["complete_pair"])
            self.assertEqual(status["version"], "0.3.1")

    def test_migration_refuses_missing_manifest_without_moving_iso(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            iso, _ = make_artifact(root, "arm64", "0.3.0")
            Path(str(iso) + ".manifest.json").unlink()
            with self.assertRaises(ValueError):
                release.migrate(root)
            self.assertTrue(iso.is_file())

    def test_migration_repairs_known_legacy_filename_metadata_without_changing_iso(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            iso, manifest = make_artifact(root, "amd64", "0.1.0")
            expected_name = "ifba-os-ubuntu-24.04-amd64-v0.1.0.iso"
            renamed = iso.with_name(expected_name)
            iso.rename(renamed)
            Path(str(iso) + ".manifest.json").rename(Path(str(renamed) + ".manifest.json"))
            iso = renamed
            manifest = Path(str(iso) + ".manifest.json")
            data = json.loads(manifest.read_text())
            data["artifact"]["file"] = "ifba-os-ubuntu-24.04-amd64.iso"
            manifest.write_text(json.dumps(data))
            expected = release.sha256(iso)
            release.migrate(root)
            archived = root / "versions/v0.1.0/amd64/manifest.json"
            archive_iso = root / "versions/v0.1.0/amd64" / iso.name
            self.assertEqual(release.sha256(archive_iso), expected)
            self.assertEqual(json.loads(archived.read_text())["artifact"]["file"], iso.name)

    def test_publish_rejects_hash_or_version_mismatch_and_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "incoming"
            source.mkdir()
            iso, manifest = make_artifact(source, "amd64", "0.3.2")
            release.publish(iso, manifest, root)
            second = root / "second"
            second.mkdir()
            duplicate, duplicate_manifest = make_artifact(second, "amd64", "0.3.2")
            with self.assertRaises(ValueError):
                release.publish(duplicate, duplicate_manifest, root)
            bad_iso, bad_manifest = make_artifact(second, "arm64", "0.3.2")
            data = json.loads(bad_manifest.read_text())
            data["artifact"]["sha256"] = "bad"
            bad_manifest.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                release.inspect(bad_iso, bad_manifest)


if __name__ == "__main__":
    unittest.main()
