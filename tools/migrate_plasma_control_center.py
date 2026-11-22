#!/usr/bin/env python3
"""Remove only the retired IFBA Control Center applet from a cached Live layout."""

from pathlib import Path
import re
import sys


APPLET_SECTION = re.compile(r"^\[Containments\]\[(\d+)\]\[Applets\]\[(\d+)\](?:\[.*\])?$")
SECTION = re.compile(r"^\[.*\]$")
PLUGIN = "plugin=org.ifbaos.controlcenter"


def migrate(path: Path) -> bool:
    if not path.is_file():
        return False
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    sections: list[tuple[str, int, int]] = []
    current = ""
    body: list[str] = []
    for index, line in enumerate(lines):
        stripped = line.rstrip("\r\n")
        if SECTION.fullmatch(stripped):
            if current:
                sections.append((current, section_start, index))
            current = stripped
            section_start = index
    if current:
        sections.append((current, section_start, len(lines)))

    target_roots: set[tuple[str, str]] = set()
    for header, start, end in sections:
        match = APPLET_SECTION.fullmatch(header)
        if match and any(line.strip() == PLUGIN for line in lines[start + 1:end]):
            target_roots.add((match.group(1), match.group(2)))
    if not target_roots:
        return False

    removed_sections: set[str] = set()
    for containment, applet in target_roots:
        root = f"[Containments][{containment}][Applets][{applet}]"
        removed_sections.add(root)
        for header, _, _ in sections:
            if header.startswith(root + "["):
                removed_sections.add(header)

    filtered: list[str] = []
    skip = False
    active_section = ""
    for line in lines:
        stripped = line.rstrip("\r\n")
        if SECTION.fullmatch(stripped):
            active_section = stripped
            skip = active_section in removed_sections
        if skip:
            continue
        match = re.fullmatch(r"(AppletOrder=)([^\r\n]*)(\r?\n)?", line)
        if match and any(active_section == f"[Containments][{containment}][Applets]" for containment, _ in target_roots):
            had_trailing_separator = match.group(2).endswith(";")
            entries = [entry for entry in match.group(2).split(";") if entry]
            entries = [entry for entry in entries if not any(
                active_section == f"[Containments][{containment}][Applets]" and entry == applet
                for containment, applet in target_roots
            )]
            order = ";".join(entries)
            if had_trailing_separator and order:
                order += ";"
            filtered.append(match.group(1) + order + (match.group(3) or "\n"))
        else:
            filtered.append(line)

    path.write_text("".join(filtered), encoding="utf-8")
    return True


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} PLASMA_APPLETSRC", file=sys.stderr)
        return 2
    migrate(Path(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
