#!/usr/bin/env bash
# Run with FFmpeg available to package the theme into a fresh root filesystem.
set -euo pipefail

source_dir="$(cd "$(dirname "$0")/.." && pwd)"
theme_dir="${1:?Usage: install-plymouth-theme.sh THEME_DIR}"
frame_rate=12
install -d "$theme_dir"
install -m 0644 "$source_dir/packaging/plymouth/ifba-os.plymouth" \
  "$source_dir/assets/plymouth/ifba-os-startup.png" "$theme_dir/"
ffmpeg -nostdin -y -loglevel error -xerror -i "$source_dir/assets/animations/boot animation.mp4" \
  -map 0:v:0 -an -vf "fps=$frame_rate,scale=960:540:force_original_aspect_ratio=decrease" \
  -threads 1 "$theme_dir/frame-%03d.png"
shopt -s nullglob
frames=("$theme_dir"/frame-*.png)
if (( ${#frames[@]} == 0 )); then
  printf 'The IFBA OS boot video produced no Plymouth frames.\n' >&2
  exit 1
fi
sed -e "s/@FRAME_COUNT@/${#frames[@]}/" -e "s/@FRAME_RATE@/$frame_rate/" \
  "$source_dir/packaging/plymouth/ifba-os.script" > "$theme_dir/ifba-os.script"
