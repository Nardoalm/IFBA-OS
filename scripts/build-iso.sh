#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/output/ifba-os-ubuntu-24.04-amd64.iso"
mkdir -p "$ROOT/output"
docker volume create --name ifba-os-build-cache >/dev/null
docker run --rm --privileged --platform linux/amd64 \
  -v "$ROOT:/work" \
  --mount type=volume,src=ifba-os-build-cache,dst=/var/cache/ifba-rootfs \
  -w /work ubuntu:24.04 bash /work/scripts/build-iso-container.sh
printf 'Created %s\n' "$OUT"
