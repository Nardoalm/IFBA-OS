#!/usr/bin/env python3
"""Verify and organize local IFBA OS ISO artifacts without rewriting history."""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path


NAME = re.compile(r"^ifba-os-ubuntu-(?:24\.04|26\.04)-(amd64|arm64)-v(\d+\.\d+\.\d+)\.iso$")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect(iso, manifest):
    iso, manifest = Path(iso), Path(manifest)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    match = NAME.match(iso.name)
    if not match:
        raise ValueError(f"unsupported ISO filename: {iso.name}")
    arch, version = match.groups()
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


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("verify")
    p.add_argument("iso"); p.add_argument("manifest")
    p = sub.add_parser("migrate")
    p.add_argument("--output", default="output")
    p = sub.add_parser("publish")
    p.add_argument("iso"); p.add_argument("manifest"); p.add_argument("--output", default="output")
    p = sub.add_parser("list")
    p.add_argument("--output", default="output")
    args = parser.parse_args()
    try:
        if args.cmd == "verify":
            d = inspect(args.iso, args.manifest); print(json.dumps(d, indent=2))
        elif args.cmd == "migrate": migrate(args.output)
        elif args.cmd == "publish": publish(args.iso, args.manifest, args.output)
        else:
            root = Path(args.output)
            for m in sorted((root / "versions").glob("v*/*/manifest.json")):
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
