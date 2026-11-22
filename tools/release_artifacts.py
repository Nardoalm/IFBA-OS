#!/usr/bin/env python3
"""Verify and organize local IFBA OS ISO artifacts without rewriting history."""

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path


NAME = re.compile(r"^ifba-os-ubuntu-(24\.04|26\.04)-(amd64|arm64)-v(\d+\.\d+\.\d+)\.iso$")
SECTOR_SIZE = 2048
ISO_PVD_OFFSET = 16 * SECTOR_SIZE
EL_TORITO_SYSTEM_ID = b"EL TORITO SPECIFICATION"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_bootable_iso(iso, series, arch, version):
    iso = Path(iso)
    size = iso.stat().st_size
    if size < 19 * SECTOR_SIZE or size % SECTOR_SIZE:
        raise ValueError(f"not a complete ISO 9660 image: {iso}")

    with iso.open("rb") as stream:
        stream.seek(ISO_PVD_OFFSET)
        pvd = stream.read(SECTOR_SIZE)
        if len(pvd) != SECTOR_SIZE or pvd[:7] != b"\x01CD001\x01":
            raise ValueError(f"missing ISO 9660 primary volume descriptor: {iso}")

        label = pvd[40:72].decode("ascii", "replace").rstrip(" ")
        expected_label = "IFBA_OS_" + series.replace(".", "_")
        allowed_labels = {expected_label, expected_label + "_" + arch}
        if label not in allowed_labels:
            raise ValueError(f"unexpected ISO volume label {label!r}: {iso}")
        if tuple(map(int, version.split("."))) >= (0, 3, 0) and label != expected_label + "_" + arch:
            raise ValueError(f"architecture is missing from ISO volume label: {iso}")

        volume_blocks = int.from_bytes(pvd[80:84], "little")
        volume_blocks_be = int.from_bytes(pvd[84:88], "big")
        block_size = int.from_bytes(pvd[128:130], "little")
        block_size_be = int.from_bytes(pvd[130:132], "big")
        if (volume_blocks == 0 or volume_blocks != volume_blocks_be
                or block_size != SECTOR_SIZE or block_size != block_size_be
                or volume_blocks * block_size > size):
            raise ValueError(f"invalid ISO volume geometry: {iso}")

        root = pvd[156:190]
        if len(root) != 34 or root[0] < 34 or root[25] & 0x02 == 0 or root[32:34] != b"\x01\x00":
            raise ValueError(f"invalid ISO root directory record: {iso}")
        root_extent = int.from_bytes(root[2:6], "little")
        root_extent_be = int.from_bytes(root[6:10], "big")
        root_length = int.from_bytes(root[10:14], "little")
        root_length_be = int.from_bytes(root[14:18], "big")
        if (root_extent != root_extent_be or root_length != root_length_be or root_length == 0
                or root_extent + (root_length + SECTOR_SIZE - 1) // SECTOR_SIZE > volume_blocks):
            raise ValueError(f"invalid ISO root directory extent: {iso}")

        boot_catalog_lba = None
        found_terminator = False
        for _ in range(1, 256):
            descriptor = stream.read(SECTOR_SIZE)
            if len(descriptor) != SECTOR_SIZE:
                break
            if descriptor[1:6] != b"CD001" or descriptor[6] != 1:
                raise ValueError(f"invalid ISO volume descriptor sequence: {iso}")
            if descriptor[0] == 0 and descriptor[7:39].rstrip(b"\x00 ") == EL_TORITO_SYSTEM_ID:
                boot_catalog_lba = int.from_bytes(descriptor[71:75], "little")
            if descriptor[0] == 255:
                found_terminator = True
                break
        if boot_catalog_lba is None or not found_terminator or boot_catalog_lba >= volume_blocks:
            raise ValueError(f"missing El Torito boot record or volume descriptor terminator: {iso}")
        stream.seek(boot_catalog_lba * SECTOR_SIZE)
        catalog = stream.read(128)
        expected_platform = 0xEF if arch == "arm64" else 0x00
        checksum = sum(int.from_bytes(catalog[i:i + 2], "little") for i in range(0, 32, 2)) & 0xFFFF
        if (len(catalog) != 128 or catalog[0] != 1 or catalog[1] != expected_platform
                or catalog[30:32] != b"\x55\xAA" or checksum != 0 or catalog[32] != 0x88):
            raise ValueError(f"invalid El Torito boot catalog for {arch}: {iso}")
        if arch == "amd64" and not (catalog[64] == 0x91 and catalog[65] == 0xEF and catalog[96] == 0x88):
            raise ValueError(f"missing AMD64 UEFI boot entry: {iso}")


def inspect(iso, manifest):
    iso, manifest = Path(iso), Path(manifest)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    match = NAME.match(iso.name)
    if not match:
        raise ValueError(f"unsupported ISO filename: {iso.name}")
    series, arch, version = match.groups()
    validate_bootable_iso(iso, series, arch, version)
    artifact = data.get("artifact", {})
    actual_hash = sha256(iso)
    if (data.get("architecture") != arch or data.get("system_version") != version
            or artifact.get("file") != iso.name or artifact.get("sha256") != actual_hash
            or artifact.get("size_bytes") != iso.stat().st_size
            or not data.get("build_id") or not data.get("source_commit")):
        raise ValueError(f"manifest or identity mismatch: {iso}")
    return data


def atomic_link(link, target):
    link, target = Path(link), Path(target)
    link.parent.mkdir(parents=True, exist_ok=True)
    tmp = link.with_name(f".{link.name}.{os.getpid()}.tmp")
    tmp.unlink(missing_ok=True)
    tmp.symlink_to(os.path.relpath(target, link.parent))
    os.replace(tmp, link)


def migrate(root):
    root = Path(root).resolve()
    files = sorted(root.glob("ifba-os-ubuntu-*-v*.iso"))
    seen = set()
    for iso in files:
        if not iso.is_file() or iso.is_symlink() or iso in seen:
            continue
        seen.add(iso)
        manifest = Path(str(iso) + ".manifest.json")
        if not manifest.is_file():
            raise ValueError(f"missing manifest: {manifest}")
        raw = json.loads(manifest.read_text(encoding="utf-8"))
        if (raw.get("system_version") == "0.1.0"
                and raw.get("artifact", {}).get("file") == "ifba-os-ubuntu-24.04-amd64.iso"
                and iso.name == "ifba-os-ubuntu-24.04-amd64-v0.1.0.iso"):
            if (raw.get("architecture") != "amd64"
                    or raw.get("artifact", {}).get("sha256") != sha256(iso)
                    or raw.get("artifact", {}).get("size_bytes") != iso.stat().st_size):
                raise ValueError(f"legacy manifest does not match artifact: {iso}")
            raw["artifact"]["file"] = iso.name
            atomic_json(manifest, raw)
        data = inspect(iso, manifest)
        arch, version = data["architecture"], data["system_version"]
        destdir = root / "versions" / f"v{version}" / arch
        destdir.mkdir(parents=True, exist_ok=True)
        destiso, destmanifest = destdir / iso.name, destdir / "manifest.json"
        if destiso.exists():
            if not destiso.is_file() or sha256(destiso) != data["artifact"]["sha256"]:
                raise ValueError(f"refusing to overwrite historical artifact: {destiso}")
            if destmanifest.exists():
                inspect(destiso, destmanifest)
            else:
                os.replace(manifest, destmanifest)
        elif destmanifest.exists():
            raise ValueError(f"manifest exists without its ISO; refusing overwrite: {destmanifest}")
        else:
            os.replace(iso, destiso)
            os.replace(manifest, destmanifest)
        if sha256(destiso) != data["artifact"]["sha256"]:
            raise ValueError(f"post-move hash mismatch: {destiso}")
        if iso.exists() or iso.is_symlink():
            iso.unlink()
        if manifest.exists() or manifest.is_symlink():
            manifest.unlink()
        atomic_link(iso, destiso)
        atomic_link(manifest, destmanifest)
        print(f"migrated {iso.name} v{version}/{arch} {data['artifact']['sha256']}")
    alias = root / "ifba-os-ubuntu-24.04-amd64.iso"
    alias_manifest = Path(str(alias) + ".manifest.json")
    canonical = root / "versions/v0.1.1/amd64/ifba-os-ubuntu-24.04-amd64-v0.1.1.iso"
    if alias.is_file() and not alias.is_symlink() and canonical.is_file() and sha256(alias) == sha256(canonical):
        alias.unlink()
        atomic_link(alias, canonical)
        print(f"preserved legacy path as symlink: {alias.name}")
    refresh_latest(root)


def refresh_latest(root):
    root = Path(root)
    versions = root / "versions"
    pairs = {}
    for manifest in versions.glob("v*/*/manifest.json"):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        version = data.get("system_version")
        arch = data.get("architecture")
        pairs.setdefault(version, {})[arch] = (manifest.parent / data["artifact"]["file"], manifest, data)
    complete = [(v, d) for v, d in pairs.items()
                if set(d) == {"amd64", "arm64"}
                and d["amd64"][2].get("source_commit") == d["arm64"][2].get("source_commit")]
    latest = root / "latest"
    if complete:
        version, pair = max(complete, key=lambda item: tuple(map(int, item[0].split("."))))
    elif any(latest.glob("*/manifest.json")):
        print("no new matched release; retaining previous latest pointers")
        return
    else:
        pair = {}
        for arch in ("amd64", "arm64"):
            candidates = [(v, d[arch]) for v, d in pairs.items() if arch in d]
            if candidates:
                _, pair[arch] = max(candidates, key=lambda item: tuple(map(int, item[0].split("."))))
        latest.mkdir(parents=True, exist_ok=True)
        status = {"complete_pair": False, "note": "Latest available artifacts have different product versions or source commits."}
        for arch, (iso, manifest, data) in pair.items():
            inspect(iso, manifest)
            atomic_link(latest / arch / iso.name, iso)
            atomic_link(latest / arch / "manifest.json", manifest)
            status[arch] = {"version": data["system_version"], "source_commit": data["source_commit"]}
        atomic_json(latest / "release-status.json", status)
        print("latest points to per-architecture artifacts; there is no matched shared release")
        return
    atomic_json(latest / "release-status.json", {
        "complete_pair": False,
        "note": "Updating latest pointers to a verified matched release.",
    })
    for arch in ("amd64", "arm64"):
        iso, manifest, _ = pair[arch]
        inspect(iso, manifest)
        atomic_link(latest / arch / iso.name, iso)
        atomic_link(latest / arch / "manifest.json", manifest)
    atomic_json(latest / "release-status.json", {
        "complete_pair": True, "version": version,
        "source_commit": pair["amd64"][2]["source_commit"],
    })
    print(f"latest -> v{version} (both architectures, same source commit)")


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def publish(iso, manifest, root):
    data = inspect(iso, manifest)
    if data.get("source_dirty") is not False:
        raise ValueError("refusing to publish an artifact without a clean source tree")
    root = Path(root).resolve()
    version_dir = root / "versions" / f"v{data['system_version']}"
    dest = version_dir / data["architecture"]
    version_dir.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise ValueError(f"release already exists; refusing overwrite: {dest}")
    pending = version_dir / f".{data['architecture']}.pending-{uuid.uuid4().hex}"
    pending.mkdir()
    src_iso, src_manifest = Path(iso), Path(manifest)
    moved = []
    try:
        for src, name in ((src_iso, src_iso.name), (src_manifest, "manifest.json")):
            final = pending / name
            if src.stat().st_dev == pending.stat().st_dev:
                os.replace(src, final)
                moved.append((src, final))
            else:
                shutil.copyfile(src, final)
        inspect(pending / src_iso.name, pending / "manifest.json")
        os.replace(pending, dest)
    except Exception:
        for src, final in reversed(moved):
            if final.exists():
                os.replace(final, src)
        shutil.rmtree(pending, ignore_errors=True)
        raise
    refresh_latest(root)


def preserve_latest_manifest(manifest):
    if not manifest.is_file() or manifest.is_symlink():
        return
    data = json.loads(manifest.read_text(encoding="utf-8"))
    name = data.get("artifact", {}).get("file", "")
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise ValueError(f"cannot archive existing latest manifest: {manifest}")
    archived = manifest.with_name(name + ".manifest.json")
    if archived.exists() or archived.is_symlink():
        if archived.is_symlink() or archived.read_bytes() != manifest.read_bytes():
            raise ValueError(f"conflicting historical manifest: {archived}")
    else:
        os.link(manifest, archived)


def publish_pair(arm64_iso, arm64_manifest, amd64_iso, amd64_manifest, root):
    """Archive the verified pair before advancing the latest references."""
    root = Path(root).resolve()
    artifacts = {
        "arm64": (Path(arm64_iso), Path(arm64_manifest)),
        "amd64": (Path(amd64_iso), Path(amd64_manifest)),
    }
    data_by_arch = {}
    for arch, (iso, manifest) in artifacts.items():
        data = inspect(iso, manifest)
        if data.get("source_dirty") is not False:
            raise ValueError("refusing to publish an artifact without a clean source tree")
        if data.get("architecture") != arch:
            raise ValueError(f"expected {arch} artifact, got {data.get('architecture')}")
        data_by_arch[arch] = data
    arm64 = data_by_arch["arm64"]
    amd64 = data_by_arch["amd64"]
    version = arm64["system_version"]
    if (version != amd64["system_version"]
            or arm64["source_commit"] != amd64["source_commit"]):
        raise ValueError("architecture pair must share product version and source commit")

    root.mkdir(parents=True, exist_ok=True)
    with (root / ".publish-pair.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        archive = root / "versions" / f"v{version}"
        latest = root / "latest"
        if latest.is_symlink() or any((latest / arch).is_symlink() for arch in artifacts):
            raise ValueError("latest and its architecture directories must be real directories")
        for arch, (iso, _) in artifacts.items():
            pointer = latest / arch / iso.name
            target = archive / arch / iso.name
            if (pointer.exists() or pointer.is_symlink()) and (
                not pointer.is_symlink() or pointer.resolve() != target
            ):
                raise ValueError(f"refusing to replace existing ISO path: {pointer}")

        if archive.exists() or archive.is_symlink():
            if archive.is_symlink() or any(
                inspect(archive / arch / iso.name, archive / arch / "manifest.json") != data_by_arch[arch]
                for arch, (iso, _) in artifacts.items()
            ):
                raise ValueError(f"release already exists; refusing overwrite: {archive}")
        else:
            archive.parent.mkdir(parents=True, exist_ok=True)
            pending = archive.with_name(f".{archive.name}.pending-{uuid.uuid4().hex}")
            pending.mkdir()
            try:
                for arch, (src_iso, src_manifest) in artifacts.items():
                    arch_dir = pending / arch
                    arch_dir.mkdir()
                    shutil.copyfile(src_iso, arch_dir / src_iso.name)
                    shutil.copyfile(src_manifest, arch_dir / "manifest.json")
                    inspect(arch_dir / src_iso.name, arch_dir / "manifest.json")
                os.rename(pending, archive)
            finally:
                if pending.exists():
                    shutil.rmtree(pending)

        for arch in artifacts:
            preserve_latest_manifest(latest / arch / "manifest.json")
        status = {
            "complete_pair": False,
            "version": version,
            "source_commit": arm64["source_commit"],
        }
        atomic_json(latest / "release-status.json", status)
        for arch, (iso, _) in artifacts.items():
            atomic_link(latest / arch / iso.name, archive / arch / iso.name)
            atomic_link(latest / arch / "manifest.json", archive / arch / "manifest.json")
        status["complete_pair"] = True
        atomic_json(latest / "release-status.json", status)
    print(f"latest -> v{version} (verified ARM64/AMD64 source pair)")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("verify")
    p.add_argument("iso"); p.add_argument("manifest")
    p = sub.add_parser("migrate")
    p.add_argument("--output", default="output")
    p = sub.add_parser("publish")
    p.add_argument("iso"); p.add_argument("manifest"); p.add_argument("--output", default="output")
    p = sub.add_parser("publish-pair")
    p.add_argument("arm64_iso"); p.add_argument("arm64_manifest")
    p.add_argument("amd64_iso"); p.add_argument("amd64_manifest")
    p.add_argument("--output", default="output")
    p = sub.add_parser("list")
    p.add_argument("--output", default="output")
    args = parser.parse_args()
    try:
        if args.cmd == "verify":
            d = inspect(args.iso, args.manifest); print(json.dumps(d, indent=2))
        elif args.cmd == "migrate": migrate(args.output)
        elif args.cmd == "publish": publish(args.iso, args.manifest, args.output)
        elif args.cmd == "publish-pair":
            publish_pair(args.arm64_iso, args.arm64_manifest, args.amd64_iso, args.amd64_manifest, args.output)
        else:
            root = Path(args.output)
            manifests = list((root / "versions").glob("v*/*/manifest.json"))
            manifests.extend((root / "latest").glob("*/manifest.json"))
            for m in sorted(set(manifests)):
                d = json.loads(m.read_text())
                iso = m.parent / d.get("artifact", {}).get("file", "")
                try:
                    inspect(iso, m)
                    status = d.get("runtime_status", "unvalidated")
                except (OSError, ValueError, json.JSONDecodeError):
                    status = "incomplete-or-invalid"
                print(f"v{d.get('system_version')}\t{d.get('architecture')}\t{d.get('source_commit')}\t{status}\t{iso.name}")
            for iso in sorted((root / ".staging").glob("*.iso")):
                manifest = Path(str(iso) + ".manifest.json")
                status = "incomplete-or-invalid"
                try:
                    inspect(iso, manifest); status = "staged-unpublished"
                except (OSError, ValueError, json.JSONDecodeError):
                    pass
                print(f"staging\tunknown\tunknown\t{status}\t{iso.name}")
            for iso in sorted(root.glob("*.iso")):
                if not iso.is_symlink():
                    print(f"root\tlegacy\tunknown\tunorganized\t{iso.name}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"release error: {exc}", file=sys.stderr); return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
