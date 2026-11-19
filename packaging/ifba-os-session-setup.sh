#!/usr/bin/env bash
set -euo pipefail

wallpaper=/usr/share/backgrounds/ifba-os/wallpaper.png
command -v xfconf-query >/dev/null
[[ -r "$wallpaper" ]]

if command -v systemctl >/dev/null 2>&1; then
  systemctl --user import-environment DISPLAY XAUTHORITY DBUS_SESSION_BUS_ADDRESS || true
fi
if command -v dbus-update-activation-environment >/dev/null 2>&1; then
  dbus-update-activation-environment --systemd DISPLAY XAUTHORITY || true
fi

# Wait for Xfdesktop to register its real output and workspace properties.
for attempt in {1..30}; do
  if ! pgrep -x xfdesktop >/dev/null 2>&1; then
    sleep 1
    continue
  fi
  mapfile -t wallpaper_paths < <(
    xfconf-query --channel xfce4-desktop --list 2>/dev/null \
      | grep -E '^/backdrop/screen[0-9]+/monitor[^/]+/workspace[0-9]+/last-image$' || true
  )
  (( ${#wallpaper_paths[@]} > 0 )) && break
  sleep 1
done

if (( ${#wallpaper_paths[@]} == 0 )); then
  wallpaper_paths=(/backdrop/screen0/monitor0/workspace0/last-image)
fi

for path in "${wallpaper_paths[@]}"; do
  xfconf-query --channel xfce4-desktop --property "$path" \
    --create --type string --set "$wallpaper"
  style_path="${path%/last-image}/image-style"
  xfconf-query --channel xfce4-desktop --property "$style_path" \
    --create --type int --set 5
done

xfdesktop --reload >/dev/null 2>&1 || true
