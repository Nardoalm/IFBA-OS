#!/usr/bin/env python3
"""Build a version-matched Plasma/Shell package with IFBA's KScreenLocker QML."""

import json
from pathlib import Path
import shutil
import sys


BASE_PACKAGE = Path("usr/share/plasma/shells/org.kde.plasma.desktop")
CUSTOM_PACKAGE = Path("usr/share/plasma/shells/org.ifbaos.plasma")
LOCKSCREEN_PARTS = ("LockScreen.qml", "LockScreenUi.qml")


def inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def prepare(rootfs: Path, source: Path) -> Path:
    rootfs = rootfs.resolve(strict=True)
    source = source.resolve(strict=True)
    base = rootfs / BASE_PACKAGE
    target = rootfs / CUSTOM_PACKAGE
    base_real = base.resolve(strict=True)

    if not inside(base_real, rootfs):
        raise ValueError("base Plasma shell resolves outside the root filesystem")
    metadata_path = base / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("KPackageStructure") != "Plasma/Shell":
        raise ValueError("installed desktop package is not a Plasma/Shell package")
    plugin = metadata.get("KPlugin", {})
    if plugin.get("Id") != "org.kde.plasma.desktop":
        raise ValueError("installed desktop shell has an unexpected package ID")
    if int(metadata.get("X-Plasma-APIVersion", "1")) < 2:
        raise ValueError("installed desktop shell lacks the KScreenLocker QML API")

    overlays = {}
    for filename in LOCKSCREEN_PARTS:
        overlay = source / filename
        if not overlay.is_file():
            raise FileNotFoundError(overlay)
        overlays[filename] = overlay

    # Do not preserve links from a system package in the derived package. Refuse
    # links escaping the package and dereference internal links during copying.
    for path in base.rglob("*"):
        if path.is_symlink() and not inside(path.resolve(strict=True), base_real):
            raise ValueError(f"system shell contains an external symlink: {path}")

    if target.exists():
        target_real = target.resolve(strict=True)
        if not inside(target_real, rootfs) or target_real == rootfs:
            raise ValueError("refusing to replace a package outside the root filesystem")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(base, target, symlinks=False)
    copied_metadata_path = target / "metadata.json"
    copied = json.loads(copied_metadata_path.read_text(encoding="utf-8"))
    copied["KPlugin"]["Id"] = "org.ifbaos.plasma"
    copied["KPlugin"]["Name"] = "IFBA OS Plasma Shell"
    copied["KPlugin"]["Description"] = "Plasma shell with the IFBA OS KScreenLocker interface"
    copied_metadata_path.write_text(json.dumps(copied, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")

    lockscreen_dir = target / "contents/lockscreen"
    lockscreen_dir.mkdir(parents=True, exist_ok=True)
    for filename, overlay in overlays.items():
        shutil.copyfile(overlay, lockscreen_dir / filename)

    # Make the new package selectable while preserving the installed package.
    original = json.loads(metadata_path.read_text(encoding="utf-8"))
    if original != metadata:
        raise RuntimeError("base desktop shell metadata changed unexpectedly")
    return target


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} ROOTFS LOCKSCREEN_QML_DIR", file=sys.stderr)
        return 2
    try:
        target = prepare(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Unable to package IFBA Plasma shell: {error}", file=sys.stderr)
        return 1
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
