#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SYSTEM_VERSION="$(python3 "$ROOT/tools/build_metadata.py" version)"
python3 "$ROOT/tools/generate_design_system.py" --check
ARCHES=()
if [[ "${1:-}" == "--both" && $# -eq 1 ]]; then
  ARCHES=(arm64 amd64)
elif [[ "${1:-}" == "--arch" && $# -eq 2 && ( "$2" == arm64 || "$2" == amd64 ) ]]; then
  ARCHES=("$2")
else
  printf 'Usage: %s --arch amd64|arm64 | --both\n' "$0" >&2
  exit 2
fi
if ! git -C "$ROOT" diff-index --quiet HEAD -- || [[ -n "$(git -C "$ROOT" ls-files --others --exclude-standard)" ]]; then
  printf 'Refusing release build from a dirty worktree; commit all build inputs first.\n' >&2
  exit 2
fi
FREE_KIB="$(df -Pk "$ROOT" | awk 'END { print $4 }')"
if [[ ! "$FREE_KIB" =~ ^[0-9]+$ ]] || (( FREE_KIB < 30 * 1024 * 1024 )); then
  printf 'Release build requires at least 30 GiB free on the output filesystem (available: %s KiB).\n' "$FREE_KIB" >&2
  exit 2
fi
BUILD_COMMIT="$(git -C "$ROOT" rev-parse HEAD)"
STAGING="$ROOT/output/.staging"
mkdir -p "$STAGING"
assert_source_unchanged() {
  [[ "$(git -C "$ROOT" rev-parse HEAD)" == "$BUILD_COMMIT" ]] || { echo 'HEAD changed during build' >&2; exit 1; }
  if ! git -C "$ROOT" diff-index --quiet HEAD -- || [[ -n "$(git -C "$ROOT" ls-files --others --exclude-standard)" ]]; then
    echo 'Source worktree changed during build' >&2
    exit 1
  fi
}
for ARCH in "${ARCHES[@]}"; do
  assert_source_unchanged
  ISO_FILENAME="ifba-os-ubuntu-26.04-${ARCH}-v${SYSTEM_VERSION}.iso"
  BUILD_INFO="$STAGING/.ifba-os-build-info-${ARCH}.json"
  OUT="$STAGING/$ISO_FILENAME"
  DEFAULT_BUILD_CACHE_VOLUME="ifba-os-bootstrap-resolute-$ARCH"
  BUILD_CACHE_VOLUME="${IFBA_BUILD_CACHE_VOLUME:-$DEFAULT_BUILD_CACHE_VOLUME}"
  [[ "$BUILD_CACHE_VOLUME" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]] || { echo 'Invalid Docker volume name' >&2; exit 2; }
  BUILD_DATE_UTC="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  BUILD_ID="ifba-$(date -u +'%Y%m%dT%H%M%SZ')-${ARCH}-${BUILD_COMMIT:0:12}"
  python3 "$ROOT/tools/build_metadata.py" build-info --output "$BUILD_INFO" --build-id "$BUILD_ID" --commit "$BUILD_COMMIT" --date-utc "$BUILD_DATE_UTC" --source-dirty false --architecture "$ARCH"
  docker volume create --name "$BUILD_CACHE_VOLUME" >/dev/null
  docker run --rm --privileged --platform "linux/$ARCH" -e IFBA_ARCH="$ARCH" -e IFBA_ISO_FILENAME="$ISO_FILENAME" \
    -e IFBA_OUTPUT_DIR=/work/output/.staging -e IFBA_BUILD_INFO_FILE="/work/output/.staging/.ifba-os-build-info-${ARCH}.json" \
    -v "$ROOT:/work" --mount type=volume,src="$BUILD_CACHE_VOLUME",dst=/var/cache/ifba-bootstrap \
    -w /work ubuntu:24.04 bash /work/scripts/build-iso-container.sh
  assert_source_unchanged
  python3 "$ROOT/tools/build_metadata.py" iso-manifest --build-info "$BUILD_INFO" --iso "$OUT" --output "$OUT.manifest.json"
  rm "$BUILD_INFO"
done

if [[ "${1:-}" == "--both" ]]; then
  assert_source_unchanged
  python3 "$ROOT/tools/release_artifacts.py" publish-pair \
    "$STAGING/ifba-os-ubuntu-26.04-arm64-v${SYSTEM_VERSION}.iso" \
    "$STAGING/ifba-os-ubuntu-26.04-arm64-v${SYSTEM_VERSION}.iso.manifest.json" \
    "$STAGING/ifba-os-ubuntu-26.04-amd64-v${SYSTEM_VERSION}.iso" \
    "$STAGING/ifba-os-ubuntu-26.04-amd64-v${SYSTEM_VERSION}.iso.manifest.json" \
    --output "$ROOT/output"
  rm -f \
    "$STAGING/ifba-os-ubuntu-26.04-arm64-v${SYSTEM_VERSION}.iso" \
    "$STAGING/ifba-os-ubuntu-26.04-arm64-v${SYSTEM_VERSION}.iso.manifest.json" \
    "$STAGING/ifba-os-ubuntu-26.04-amd64-v${SYSTEM_VERSION}.iso" \
    "$STAGING/ifba-os-ubuntu-26.04-amd64-v${SYSTEM_VERSION}.iso.manifest.json"
  printf 'Published verified v%s ARM64/AMD64 pair to output/latest\n' "$SYSTEM_VERSION"
else
  printf 'Staged v%s %s; latest remains unchanged until both architectures are built.\n' \
    "$SYSTEM_VERSION" "${ARCHES[0]}"
fi
