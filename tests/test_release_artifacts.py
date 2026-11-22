import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / "tools/release_artifacts.py"
SPEC = importlib.util.spec_from_file_location("release_artifacts", MODULE)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


def make_artifact(root, arch, version, commit="abc123", series="26.04"):
    name = f"ifba-os-ubuntu-{series}-{arch}-v{version}.iso"
    path = root / name
    image = bytearray(32 * release.SECTOR_SIZE)
    pvd = bytearray(release.SECTOR_SIZE)
    pvd[:7] = b"\x01CD001\x01"
    volume_label = "IFBA_OS_" + series.replace(".", "_")
    if tuple(map(int, version.split("."))) >= (0, 3, 0):
        volume_label += "_" + arch
    pvd[40:72] = volume_label.encode("ascii").ljust(32, b" ")
    pvd[80:84] = (32).to_bytes(4, "little")
    pvd[84:88] = (32).to_bytes(4, "big")
    pvd[128:130] = release.SECTOR_SIZE.to_bytes(2, "little")
    pvd[130:132] = release.SECTOR_SIZE.to_bytes(2, "big")
    root = bytearray(34)
    root[0] = 34
    root[2:6] = (19).to_bytes(4, "little")
    root[6:10] = (19).to_bytes(4, "big")
    root[10:14] = release.SECTOR_SIZE.to_bytes(4, "little")
    root[14:18] = release.SECTOR_SIZE.to_bytes(4, "big")
    root[25] = 0x02
    root[28:30] = (1).to_bytes(2, "little")
    root[30:32] = (1).to_bytes(2, "big")
    root[32:34] = b"\x01\x00"
    pvd[156:190] = root
    boot = bytearray(release.SECTOR_SIZE)
    boot[:7] = b"\x00CD001\x01"
    boot[7:39] = release.EL_TORITO_SYSTEM_ID.ljust(32, b"\x00")
    boot[71:75] = (20).to_bytes(4, "little")
    catalog = bytearray(release.SECTOR_SIZE)
    catalog[0] = 1
    catalog[1] = 0xEF if arch == "arm64" else 0
    catalog[30:32] = b"\x55\xAA"
    catalog[32] = 0x88
    if arch == "amd64":
        catalog[64:67] = bytes((0x91, 0xEF, 1))
        catalog[96] = 0x88
    checksum = sum(int.from_bytes(catalog[i:i + 2], "little") for i in range(0, 32, 2)) & 0xFFFF
    catalog[28:30] = ((-checksum) & 0xFFFF).to_bytes(2, "little")
    end = bytearray(release.SECTOR_SIZE)
    end[:7] = b"\xffCD001\x01"
    image[16 * release.SECTOR_SIZE:17 * release.SECTOR_SIZE] = pvd
    image[17 * release.SECTOR_SIZE:18 * release.SECTOR_SIZE] = boot
    image[18 * release.SECTOR_SIZE:19 * release.SECTOR_SIZE] = end
    image[19 * release.SECTOR_SIZE:20 * release.SECTOR_SIZE] = bytes(release.SECTOR_SIZE)
    image[20 * release.SECTOR_SIZE:21 * release.SECTOR_SIZE] = catalog
    path.write_bytes(image)
    data = {
        "architecture": arch,
        "system_version": version,
        "build_id": f"test-{arch}-{version}",
        "source_commit": commit,
        "source_dirty": False,
        "status": "unvalidated",
        "artifact": {"file": name, "sha256": release.sha256(path), "size_bytes": path.stat().st_size},
    }
    manifest = Path(str(path) + ".manifest.json")
    manifest.write_text(json.dumps(data))
    return path, manifest


class ReleaseArtifactsTests(unittest.TestCase):
    def test_publish_pair_places_both_directly_in_latest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "output"
            source = Path(td) / "incoming"
            source.mkdir()
            arm_iso, arm_manifest = make_artifact(source, "arm64", "0.3.4", "release-commit")
            amd_iso, amd_manifest = make_artifact(source, "amd64", "0.3.4", "release-commit")

            release.publish_pair(arm_iso, arm_manifest, amd_iso, amd_manifest, root)

            for arch in ("arm64", "amd64"):
                latest_arch = root / "latest" / arch
                iso = latest_arch / f"ifba-os-ubuntu-26.04-{arch}-v0.3.4.iso"
                manifest = latest_arch / "manifest.json"
                self.assertTrue(iso.is_file())
                self.assertFalse(iso.is_symlink())
                self.assertTrue(manifest.is_file())
                self.assertFalse(manifest.is_symlink())
                self.assertEqual(release.inspect(iso, manifest)["source_commit"], "release-commit")
            status = json.loads((root / "latest/release-status.json").read_text())
            self.assertEqual(status, {
                "complete_pair": True,
                "version": "0.3.4",
                "source_commit": "release-commit",
            })
            self.assertFalse((root / "versions/v0.3.4").exists())

    def test_publish_pair_rejects_mixed_architecture_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "output"
            source = Path(td) / "incoming"
            source.mkdir()
            arm_iso, arm_manifest = make_artifact(source, "arm64", "0.3.4", "commit-a")
            amd_iso, amd_manifest = make_artifact(source, "amd64", "0.3.4", "commit-b")

            with self.assertRaisesRegex(ValueError, "share product version and source commit"):
                release.publish_pair(arm_iso, arm_manifest, amd_iso, amd_manifest, root)
            self.assertFalse((root / "latest").exists())

    def test_publish_refuses_artifacts_built_from_dirty_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "incoming"
            source.mkdir()
            iso, manifest = make_artifact(source, "amd64", "0.3.2")
            data = json.loads(manifest.read_text())
            data["source_dirty"] = True
            manifest.write_text(json.dumps(data))

            with self.assertRaisesRegex(ValueError, "clean source tree"):
                release.publish(iso, manifest, root)
            self.assertTrue(iso.is_file())
            self.assertFalse((root / "versions/v0.3.2/amd64").exists())

    def test_inspect_rejects_self_consistent_manifest_for_non_iso_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            iso, manifest = make_artifact(root, "amd64", "0.3.2")
            iso.write_bytes(b"not an ISO, with a matching checksum")
            data = json.loads(manifest.read_text())
            data["artifact"]["sha256"] = release.sha256(iso)
            data["artifact"]["size_bytes"] = iso.stat().st_size
            manifest.write_text(json.dumps(data))

            with self.assertRaisesRegex(ValueError, "not a complete ISO"):
                release.inspect(iso, manifest)

    def test_inspect_rejects_an_iso_with_a_mismatched_architecture_label(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            iso, manifest = make_artifact(root, "amd64", "0.3.2")
            with iso.open("r+b") as stream:
                stream.seek(16 * release.SECTOR_SIZE + 40)
                stream.write(b"IFBA_OS_26_04_arm64".ljust(32, b" "))
            data = json.loads(manifest.read_text())
            data["artifact"]["sha256"] = release.sha256(iso)
            data["artifact"]["size_bytes"] = iso.stat().st_size
            manifest.write_text(json.dumps(data))

            with self.assertRaisesRegex(ValueError, "unexpected ISO volume label"):
                release.inspect(iso, manifest)

    def test_inspect_rejects_amd64_iso_without_a_uefi_boot_entry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            iso, manifest = make_artifact(root, "amd64", "0.3.2")
            with iso.open("r+b") as stream:
                stream.seek(20 * release.SECTOR_SIZE + 64)
                stream.write(bytes(1))
            data = json.loads(manifest.read_text())
            data["artifact"]["sha256"] = release.sha256(iso)
            manifest.write_text(json.dumps(data))

            with self.assertRaisesRegex(ValueError, "missing AMD64 UEFI"):
                release.inspect(iso, manifest)

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
            iso, manifest = make_artifact(root, "amd64", "0.1.0", series="24.04")
            expected_name = "ifba-os-ubuntu-24.04-amd64-v0.1.0.iso"
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
