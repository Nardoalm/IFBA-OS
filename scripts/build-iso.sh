#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/output/ifba-os-ubuntu-26.04-amd64.iso"
BUILD_INFO="$ROOT/output/.ifba-os-build-info.json"
BUILD_CACHE_VOLUME="${IFBA_BUILD_CACHE_VOLUME:-ifba-os-plasma-build-cache}"
BUILD_COMMIT="$(git -C "$ROOT" rev-parse HEAD)"
BUILD_DATE_UTC="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
BUILD_ID="ifba-$(date -u +'%Y%m%dT%H%M%SZ')-${BUILD_COMMIT:0:12}"
SOURCE_DIRTY=false
if ! git -C "$ROOT" diff-index --quiet HEAD --; then
  SOURCE_DIRTY=true
fi
mkdir -p "$ROOT/output"
if [[ ! "$BUILD_CACHE_VOLUME" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]]; then
  printf 'Invalid Docker volume name: %s\n' "$BUILD_CACHE_VOLUME" >&2
  exit 2
fi
trap 'rm -f "$BUILD_INFO"' EXIT
python3 "$ROOT/tools/build_metadata.py" build-info \
  --output "$BUILD_INFO" \
  --build-id "$BUILD_ID" \
  --commit "$BUILD_COMMIT" \
  --date-utc "$BUILD_DATE_UTC" \
  --source-dirty "$SOURCE_DIRTY"
docker volume create --name "$BUILD_CACHE_VOLUME" >/dev/null
docker run --rm --privileged --platform linux/amd64 \
  -v "$ROOT:/work" \
  --mount type=volume,src="$BUILD_CACHE_VOLUME",dst=/var/cache/ifba-rootfs \
  -w /work ubuntu:24.04 bash /work/scripts/build-iso-container.sh
python3 "$ROOT/tools/build_metadata.py" iso-manifest \
  --build-info "$BUILD_INFO" \
  --iso "$OUT" \
  --output "$OUT.manifest.json"
printf 'Created %s\n' "$OUT"
cat "$OUT.manifest.json"
