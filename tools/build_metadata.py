#!/usr/bin/env python3

import argparse
import hashlib
import json
from pathlib import Path


SYSTEM_VERSION = "0.3.6"


def build_info(build_id, commit, date_utc, source_dirty, architecture):
    if architecture not in ("amd64", "arm64"):
        raise ValueError("Unsupported architecture: {}".format(architecture))
    return {
        "schema_version": 1,
        "product": "IFBA OS",
        "system_version": SYSTEM_VERSION,
        "base": "Ubuntu 26.04 LTS",
        "architecture": architecture,
        "build_id": build_id,
        "source_commit": commit,
        "build_date_utc": date_utc,
        "source_dirty": source_dirty == "true",
    }


def write_json(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_iso_manifest(info_path, iso_path, output_path):
    info = json.loads(Path(info_path).read_text(encoding="utf-8"))
    digest = hashlib.sha256()
    size = 0
    with Path(iso_path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    manifest = {
        **info,
        "build_status": "built",
        "runtime_status": "unvalidated",
        "artifact": {
            "file": Path(iso_path).name,
            "sha256": digest.hexdigest(),
            "size_bytes": size,
        },
    }
    write_json(output_path, manifest)


def main(argv=None):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("version")
    build_parser = commands.add_parser("build-info")
    build_parser.add_argument("--output", required=True)
    build_parser.add_argument("--build-id", required=True)
    build_parser.add_argument("--commit", required=True)
    build_parser.add_argument("--date-utc", required=True)
    build_parser.add_argument("--source-dirty", choices=("true", "false"), required=True)
    build_parser.add_argument("--architecture", choices=("amd64", "arm64"), required=True)
    iso_parser = commands.add_parser("iso-manifest")
    iso_parser.add_argument("--build-info", required=True)
    iso_parser.add_argument("--iso", required=True)
    iso_parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if args.command == "version":
        print(SYSTEM_VERSION)
    elif args.command == "build-info":
        write_json(args.output, build_info(args.build_id, args.commit, args.date_utc, args.source_dirty, args.architecture))
    else:
        write_iso_manifest(args.build_info, args.iso, args.output)


if __name__ == "__main__":
    main()
