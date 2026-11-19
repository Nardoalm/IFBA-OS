#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'IFBA OS XFCE repair: %s\n' "$*" >&2
  exit 1
}

say() {
  printf 'IFBA OS XFCE repair: %s\n' "$*"
}

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
template_dir="/usr/share/ifba-os/defaults"
if [[ -d "$root_dir/packaging" ]]; then
  template_dir="$root_dir/packaging"
fi
mode="${1:---session}"

copy_system_defaults() {
  [[ "$EUID" -eq 0 ]] || fail 'system defaults require administrator authorization'
  local source
  for source in xfce4-panel.xml xfwm4.xml xfce4-session.xml; do
    [[ -r "$template_dir/$source" ]] || fail "missing default template: $template_dir/$source"
  done
  install -D -m 0644 "$template_dir/xfce4-panel.xml" \
    /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml
  install -D -m 0644 "$template_dir/xfce4-panel.xml" /etc/xdg/xfce4/panel/default.xml
  install -D -m 0644 "$template_dir/xfwm4.xml" \
    /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml
  install -D -m 0644 "$template_dir/xfce4-session.xml" \
    /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-session.xml
  install -D -m 0644 "$template_dir/xfce4-panel.xml" \
    /etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml
  install -D -m 0644 "$template_dir/xfwm4.xml" \
    /etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml
  install -D -m 0644 "$template_dir/xfce4-session.xml" \
    /etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-session.xml
  say 'installed single-panel, one-workspace defaults for future users'
}

set_array() {
  local property="$1"
  shift
  local -a args=(--channel xfce4-panel --property "$property" --force-array)
  local value
  for value in "$@"; do
    args+=(--type int --set "$value")
  done
  args+=(--create)
  xfconf-query "${args[@]}"
}

apply_session() {
  [[ "$EUID" -ne 0 ]] || fail 'session changes must run as the logged-in desktop user, never as root'
  command -v xfconf-query >/dev/null 2>&1 || fail 'xfconf-query is not installed'
  command -v xfce4-panel >/dev/null 2>&1 || fail 'xfce4-panel is not installed'
  [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]] || fail 'no user D-Bus session is available'
  [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] || fail 'no graphical session is available'
  pgrep -u "$EUID" -x xfce4-panel >/dev/null 2>&1 || fail 'the current user has no running XFCE panel'

  local panels position extra plugin_id plugin_value main_ids property value verify
  local -a panel_ids=()
  panels="$(xfconf-query --channel xfce4-panel --property /panels 2>/dev/null)" || fail 'cannot read active XFCE panel IDs'
  while IFS= read -r value; do
    panel_ids+=("$value")
  done < <(printf '%s\n' "$panels" | awk '/^[[:space:]]*[0-9]+[[:space:]]*$/ { gsub(/[[:space:]]/, ""); print }')
  local has_main=0
  for extra in "${panel_ids[@]}"; do
    [[ "$extra" == 1 ]] && has_main=1
  done
  (( has_main == 1 )) || fail 'panel 1 is not active; no panels were changed'
  position="$(xfconf-query --channel xfce4-panel --property /panels/panel-1/position 2>/dev/null)" || fail 'cannot verify panel 1 position'
  [[ "$position" == *'p=10;'* ]] || fail "panel 1 is not the expected bottom panel ($position); no panels were removed"
  main_ids="$(xfconf-query --channel xfce4-panel --property /panels/panel-1/plugin-ids 2>/dev/null)" || fail 'cannot inspect panel 1 plugins'

  for extra in "${panel_ids[@]}"; do
    [[ "$extra" == 1 ]] && continue
    local extra_ids
    extra_ids="$(xfconf-query --channel xfce4-panel --property "/panels/panel-$extra/plugin-ids" 2>/dev/null || true)"
    xfconf-query --channel xfce4-panel --property "/panels/panel-$extra" --reset --recursive || fail "cannot remove panel $extra settings"
    while IFS= read -r plugin_id; do
      [[ "$plugin_id" =~ ^[0-9]+$ ]] || continue
      if ! printf '%s\n' "$main_ids" | awk '/^[[:space:]]*[0-9]+[[:space:]]*$/ { gsub(/[[:space:]]/, ""); print }' | grep -Fxq "$plugin_id"; then
        xfconf-query --channel xfce4-panel --property "/plugins/plugin-$plugin_id" --reset --recursive >/dev/null 2>&1 || true
      fi
    done < <(printf '%s\n' "$extra_ids" | awk '/^[[:space:]]*[0-9]+[[:space:]]*$/ { gsub(/[[:space:]]/, ""); print }')
  done

  local -a retained_ids=()
  while IFS= read -r plugin_id; do
    [[ "$plugin_id" =~ ^[0-9]+$ ]] || continue
    property="/plugins/plugin-$plugin_id"
    plugin_value="$(xfconf-query --channel xfce4-panel --property "$property" 2>/dev/null || true)"
    if [[ "$plugin_value" == *pager* ]]; then
      xfconf-query --channel xfce4-panel --property "$property" --reset --recursive >/dev/null 2>&1 || true
    else
      retained_ids+=("$plugin_id")
    fi
  done < <(printf '%s\n' "$main_ids" | awk '/^[[:space:]]*[0-9]+[[:space:]]*$/ { gsub(/[[:space:]]/, ""); print }')

  set_array /panels 1
  if (( ${#retained_ids[@]} > 0 )); then
    set_array /panels/panel-1/plugin-ids "${retained_ids[@]}"
  fi
  xfconf-query --channel xfwm4 --property /general/workspace_count --create --type int --set 1
  xfconf-query --channel xfce4-session --property /general/SaveOnExit --create --type bool --set false
  xfce4-panel -r || fail 'panel restart failed'

  verify="$(xfconf-query --channel xfce4-panel --property /panels 2>/dev/null)" || fail 'cannot verify panel list after restart'
  panel_ids=()
  while IFS= read -r value; do
    panel_ids+=("$value")
  done < <(printf '%s\n' "$verify" | awk '/^[[:space:]]*[0-9]+[[:space:]]*$/ { gsub(/[[:space:]]/, ""); print }')
  [[ "${#panel_ids[@]}" -eq 1 && "${panel_ids[0]}" == 1 ]] || fail 'XFCE did not retain exactly panel 1'
  verify="$(xfconf-query --channel xfwm4 --property /general/workspace_count 2>/dev/null)" || fail 'cannot verify workspace count'
  value="$(printf '%s\n' "$verify" | awk '/^Value is an integer:/ { print $NF; exit } /^[[:space:]]*[0-9]+[[:space:]]*$/ { gsub(/[[:space:]]/, ""); print; exit }')"
  [[ "$value" == 1 ]] || fail 'XFWM4 did not retain one workspace'
  say 'panel 1 retained, extra panels removed, workspace count set to one, and panel restarted'
}

case "$mode" in
  --session)
    apply_session
    ;;
  --system-defaults)
    if [[ "$EUID" -ne 0 ]]; then
      command -v pkexec >/dev/null 2>&1 || fail 'pkexec is unavailable; run this mode through an administrator-authorized session'
      exec pkexec "$0" --system-defaults
    fi
    copy_system_defaults
    ;;
  *)
    fail 'usage: fix-xfce-panel.sh [--session|--system-defaults]'
    ;;
esac
