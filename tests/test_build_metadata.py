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
            "amd64",
        )
        self.assertEqual(info["build_id"], "ifba-20261119T120000Z-abcdef123456")
        self.assertEqual(info["source_commit"], "abcdef1234567890")
        self.assertTrue(info["source_dirty"])
        self.assertEqual(info["base"], "Ubuntu 26.04 LTS")
        self.assertEqual(info["architecture"], "amd64")

    def test_arm64_build_metadata_preserves_architecture(self):
        info = build_metadata.build_info(
            "ifba-20261119T120000Z-abcdef123456",
            "abcdef1234567890",
            "2026-11-19T12:00:00Z",
            "false",
            "arm64",
        )
        self.assertEqual(info["architecture"], "arm64")

    def test_build_metadata_rejects_unknown_architecture(self):
        with self.assertRaises(ValueError):
            build_metadata.build_info(
                "build-1", "abcdef", "2026-11-19T12:00:00Z", "false", "riscv64"
            )

    def test_version_command_matches_embedded_system_version(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/build_metadata.py"), "version"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout.strip(), build_metadata.SYSTEM_VERSION)

    def test_iso_manifest_records_sha256_and_exact_size(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            build_path = directory / "build-info.json"
            iso_path = directory / "test.iso"
            manifest_path = directory / "test.iso.manifest.json"
            build_metadata.write_json(
                build_path,
                build_metadata.build_info("build-1", "abcdef", "2026-11-19T12:00:00Z", "false", "arm64"),
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
                        "architecture": "arm64",
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
            self.assertIn("Architecture: arm64", result.stdout)
            self.assertIn("Source commit: 1234567890abcdef", result.stdout)

    def test_iso_build_has_provenance_and_required_rootfs_guards(self):
        host_build = (ROOT / "scripts/build-iso.sh").read_text(encoding="utf-8")
        container_build = (ROOT / "scripts/build-iso-container.sh").read_text(encoding="utf-8")
        self.assertIn("IFBA_BUILD_CACHE_VOLUME", host_build)
        self.assertIn("build-info", host_build)
        self.assertIn("iso-manifest", host_build)
        self.assertIn("ubuntu:24.04", host_build)
        self.assertIn('v${SYSTEM_VERSION}.iso', host_build)
        self.assertIn('IFBA_ISO_FILENAME="$ISO_FILENAME"', host_build)
        self.assertIn('docker run --rm --privileged --platform "linux/$ARCH"', host_build)
        self.assertIn('ARCHES=(arm64 amd64)', host_build)
        self.assertIn('git -C "$ROOT" rev-parse HEAD', host_build)
        self.assertIn('assert_source_unchanged', host_build)
        self.assertIn('BUILD_ID="ifba-$(date -u +\'%Y%m%dT%H%M%SZ\')-${ARCH}-${BUILD_COMMIT:0:12}"', host_build)
        self.assertIn('release_artifacts.py" publish-pair', host_build)
        self.assertIn('if [[ "${1:-}" == "--both" ]]', host_build)
        self.assertIn('latest remains unchanged until both architectures are built', host_build)
        self.assertIn('ifba-os-ubuntu-26.04-${ARCH}-v${SYSTEM_VERSION}.iso', host_build)
        self.assertIn('OUT="$OUTPUT_DIR/$ISO_FILENAME"', container_build)
        self.assertNotIn("ubuntu:26.04", host_build)
        self.assertLess(
            container_build.index('chroot "$ROOTFS" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get update'),
            container_build.index("apt-get upgrade -y --with-new-pkgs"),
        )
        self.assertLess(
            container_build.index("apt-get upgrade -y --with-new-pkgs"),
            container_build.index('chroot "$ROOTFS" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get install'),
        )
        self.assertIn('test "$(chroot "$ROOTFS" dpkg --print-architecture)" = "$IFBA_ARCH"', container_build)
        self.assertIn("xorriso -osirrox on -indev \"$OUT\"", container_build)
        self.assertIn("unsquashfs -cat", container_build)
        self.assertIn('cmp -s "$VERIFY_DIR/build-info.json" "$BUILD_INFO_FILE"', container_build)
        for required in (
            "wallpaper.png",
            "IFBA-OS-Dark.colors",
            "plasma-session-wayland",
            "sddm.conf.d/10-ifba-os.conf",
            "firefox.desktop",
            "ifba-ai.desktop",
            "suap-ifba.desktop",
            "ava-ifba.desktop",
            "ifba-wired.nmconnection",
            "build-info.json",
        ):
            self.assertIn(required, container_build)
        self.assertIn("grub-efi-arm64-bin", container_build)
        self.assertIn('IFBA_ARCH="$ARCH"', host_build)
        self.assertIn('ARCHIVE=http://ports.ubuntu.com/ubuntu-ports', container_build)
        self.assertIn('BOOT_PACKAGES=(grub-efi-arm64-bin mtools)', container_build)
        self.assertIn('BOOT_PACKAGES=(grub-pc-bin grub-efi-amd64-bin mtools)', container_build)
        self.assertIn('test "$(readlink "$ROOTFS/etc/systemd/system/display-manager.service")" = /lib/systemd/system/sddm.service', container_build)
        self.assertIn('install -D -m 0755 /work/packaging/plasma/ifba-os-session-setup', container_build)
        self.assertIn('"$ROOTFS/etc/systemd/system/multi-user.target.wants/NetworkManager.service"', container_build)

    def test_build_recreates_the_rootfs_and_reuses_only_package_downloads(self):
        host = (ROOT / "scripts/build-iso.sh").read_text()
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        self.assertIn('ROOTFS="$(mktemp -d /var/tmp/ifba-rootfs.XXXXXX)"', build)
        self.assertIn('chmod 0755 "$ROOTFS"', build)
        self.assertIn('dst=/var/cache/ifba-bootstrap', host)
        self.assertIn('BOOTSTRAP_CACHE="/var/cache/ifba-bootstrap/resolute/$IFBA_ARCH"', build)
        self.assertIn('flock "$BOOTSTRAP_CACHE/.lock" debootstrap', build)
        self.assertIn('--cache-dir="$BOOTSTRAP_CACHE"', build)
        self.assertIn('--keyring=/usr/share/keyrings/ubuntu-archive-keyring.gpg resolute "$ROOTFS"', build)
        self.assertNotIn('$ROOTFS/etc/os-release', build)
        self.assertNotIn('/var/cache/ifba-rootfs', host + build)
        self.assertIn('-type l -name ifba-ai.service -print -quit', build)

    def test_casper_manifest_covers_and_checks_the_final_live_payload(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        paths = build.split("casper_payload=(\n", 1)[1].split("\n)", 1)[0].split()
        self.assertEqual(paths, [
            "casper/vmlinuz", "casper/initrd", "casper/filesystem.squashfs",
            "casper/filesystem.size", "boot/grub/grub.cfg",
        ])
        manifest = '(cd "$ISO" && md5sum "${casper_payload[@]}" > md5sum.txt)'
        self.assertLess(build.index(manifest), build.index('grub-mkrescue -volid'))
        self.assertIn('iso_extract+=(-extract "/$file" "$VERIFY_DIR/$file")', build)
        self.assertIn('for file in "${casper_payload[@]}" md5sum.txt;', build)
        self.assertIn('cmp -s "$ISO/md5sum.txt" "$VERIFY_DIR/md5sum.txt"', build)
        self.assertIn('(cd "$VERIFY_DIR" && md5sum --check --strict md5sum.txt)', build)


if __name__ == "__main__":
    unittest.main()
