#!/usr/bin/env python3
"""Migrate only the retired shell selector, preserving the rest of a profile."""

from pathlib import Path
import re
import sys


OLD = "ShellPackage=org.ifbaos.plasma"
NEW = "ShellPackage=org.kde.plasma.desktop"


def migrate(config_file: Path) -> bool:
    if not config_file.is_file():
        return False
    before = config_file.read_text(encoding="utf-8")
    after = re.sub(r"(?m)^ShellPackage=org\.ifbaos\.plasma(?=\r?$)", NEW, before)
    if after == before:
        return False
    config_file.write_text(after, encoding="utf-8")
    return True


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} PLASMASHELLRC", file=sys.stderr)
        return 2
    migrate(Path(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
