#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
IFBA_ARCH="${IFBA_ARCH:?IFBA_ARCH must be set by scripts/build-iso.sh}"
case "$IFBA_ARCH" in
  amd64)
    ARCHIVE=http://archive.ubuntu.com/ubuntu
    BOOT_PACKAGES=(grub-pc-bin grub-efi-amd64-bin mtools)
    INSTALLER_BOOT_PACKAGES=(grub-efi-amd64-signed shim-signed)
    ;;
  arm64)
    ARCHIVE=http://ports.ubuntu.com/ubuntu-ports
    BOOT_PACKAGES=(grub-efi-arm64-bin mtools)
    INSTALLER_BOOT_PACKAGES=(grub-efi-arm64-signed shim-signed)
    ;;
  *)
    printf 'Unsupported architecture: %s\n' "$IFBA_ARCH" >&2
    exit 2
    ;;
esac
KRUNNER_BUILD_PACKAGES=(
  cmake g++ make extra-cmake-modules qt6-base-dev qt6-declarative-dev-tools libkf6coreaddons-dev libkf6i18n-dev \
  libkf6jobwidgets-dev libkf6kio-dev libkf6runner-dev libkf6service-dev
)
if [[ "$IFBA_ARCH" == amd64 ]]; then
  ROOTFS=/var/cache/ifba-rootfs/rootfs-plasma-26.04
else
  ROOTFS=/var/cache/ifba-rootfs/rootfs-plasma-26.04-arm64
fi
ISO=/tmp/ifba-iso
ISO_FILENAME="${IFBA_ISO_FILENAME:?IFBA_ISO_FILENAME must be set by scripts/build-iso.sh}"
OUTPUT_DIR="${IFBA_OUTPUT_DIR:-/work/output}"
BUILD_INFO_FILE="${IFBA_BUILD_INFO_FILE:-/work/output/.ifba-os-build-info.json}"
OUT="$OUTPUT_DIR/$ISO_FILENAME"

apt-get update
apt-get install -y --no-install-recommends debootstrap squashfs-tools xorriso "${BOOT_PACKAGES[@]}" curl gnupg ca-certificates
rm -rf "$ISO"
mkdir -p "$ISO/casper" "$ISO/boot/grub"
if [[ ! -e "$ROOTFS/etc/os-release" ]]; then
  rm -rf "$ROOTFS"
  mkdir -p "$ROOTFS"
  debootstrap --arch="$IFBA_ARCH" resolute "$ROOTFS" "$ARCHIVE"
fi
cat > "$ROOTFS/etc/apt/sources.list" <<SOURCES
deb $ARCHIVE resolute main universe multiverse
deb $ARCHIVE resolute-updates main universe multiverse
deb $ARCHIVE resolute-security main universe multiverse
SOURCES
curl --fail --silent --show-error --location https://packages.mozilla.org/apt/repo-signing-key.gpg --output /tmp/mozilla-archive-keyring.asc
gpg --show-keys --with-colons /tmp/mozilla-archive-keyring.asc | awk -F: '$1 == "fpr" { print $10; exit }' | grep --quiet '^35BAA0B33E9EB396F59CA838C0BA5CE6DC6315A3$'
gpg --dearmor --output "$ROOTFS/tmp/mozilla-archive-keyring.gpg" /tmp/mozilla-archive-keyring.asc
install -D -m 0644 "$ROOTFS/tmp/mozilla-archive-keyring.gpg" "$ROOTFS/usr/share/keyrings/packages.mozilla.org.gpg"
cat > "$ROOTFS/etc/apt/sources.list.d/mozilla.sources" <<'MOZILLA'
Types: deb
URIs: https://packages.mozilla.org/apt
Suites: mozilla
Components: main
Signed-By: /usr/share/keyrings/packages.mozilla.org.gpg
MOZILLA
cat > "$ROOTFS/etc/apt/preferences.d/mozilla-firefox" <<'PREFERENCES'
Package: firefox*
Pin: origin packages.mozilla.org
Pin-Priority: 1000
PREFERENCES
mount --bind /dev "$ROOTFS/dev"
mount -t proc proc "$ROOTFS/proc"
mount --rbind /sys "$ROOTFS/sys"
RESOLV_TARGET="$ROOTFS/run/systemd/resolve/stub-resolv.conf"
mkdir -p "$(dirname "$RESOLV_TARGET")"
touch "$RESOLV_TARGET"
mount --bind /etc/resolv.conf "$RESOLV_TARGET"
cleanup_mounts() {
  umount "$RESOLV_TARGET" 2>/dev/null || true
  umount -R "$ROOTFS/dev" 2>/dev/null || true
  umount "$ROOTFS/proc" 2>/dev/null || true
  umount -R "$ROOTFS/sys" 2>/dev/null || true
}
trap cleanup_mounts EXIT
chroot "$ROOTFS" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get update
chroot "$ROOTFS" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get upgrade -y --with-new-pkgs
chroot "$ROOTFS" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  linux-image-generic casper plymouth plymouth-themes systemd-sysv \
  plasma-desktop plasma-session-wayland plasma-session-x11 kwin-x11 kwin-style-aurorae milou \
  sddm sddm-theme-breeze breeze-gtk-theme breeze-icon-theme breeze-cursor-theme \
  qt-style-kvantum=1.1.5-1 qt-style-kvantum-themes=1.1.5-1 \
  dolphin konsole plasma-discover plasma-nm plasma-pa systemsettings kinfocenter \
  powerdevil power-profiles-daemon upower bluedevil bluez libspa-0.2-bluetooth pipewire-audio ffmpeg kscreen fastfetch \
  xserver-xorg xinit network-manager xdg-utils xdg-user-dirs fonts-inter fonts-noto-core \
  xdg-desktop-portal-kde xdg-desktop-portal-gtk \
  python3-dbus python3-gi gir1.2-gtk-3.0 gnome-keyring libpam-gnome-keyring \
  libsecret-tools python3-xlib python3-pyatspi at-spi2-core gir1.2-atspi-2.0 \
  libnss3 libatk1.0-0 libatk-bridge2.0-0t64 libcups2t64 libasound2t64 \
  libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libdrm2 \
  libxkbcommon0 libpango-1.0-0 firefox firefox-l10n-pt-br sudo dbus-x11 \
  polkitd pkexec qemu-guest-agent locales calamares squashfs-tools efibootmgr kdialog \
  python3-pyqt6 thonny libreoffice-writer gcompris-qt \
  "${INSTALLER_BOOT_PACKAGES[@]}"
chroot "$ROOTFS" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${KRUNNER_BUILD_PACKAGES[@]}"
mkdir -p "$ROOTFS/tmp/ifba-app-description-runner"
cp -R /work/packaging/plasma/ifba-app-description-runner/. "$ROOTFS/tmp/ifba-app-description-runner/"
chroot "$ROOTFS" cmake -S /tmp/ifba-app-description-runner -B /tmp/ifba-app-description-runner/build \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_TESTING=ON
chroot "$ROOTFS" cmake --build /tmp/ifba-app-description-runner/build --parallel 2
chroot "$ROOTFS" ctest --test-dir /tmp/ifba-app-description-runner/build --output-on-failure
chroot "$ROOTFS" cmake --install /tmp/ifba-app-description-runner/build
rm -rf "$ROOTFS/tmp/ifba-app-description-runner"
# Vendor only audited QML source; build/install no upstream scripts or plugins.
mkdir -p "$ROOTFS/usr/share/plasma/plasmoids/com.github.mattanis.macosdock"
cp -R /work/packaging/plasma/ifba-dock/. "$ROOTFS/usr/share/plasma/plasmoids/com.github.mattanis.macosdock/"
for qml_file in /work/packaging/plasma/ifba-dock/contents/ui/*.qml; do
  chroot "$ROOTFS" /usr/lib/qt6/bin/qmlformat "/usr/share/plasma/plasmoids/com.github.mattanis.macosdock/contents/ui/$(basename "$qml_file")" >/dev/null
done
mkdir -p "$ROOTFS/usr/share/doc/ifba-os/third-party/plasma-macos-dock"
cp -R /work/packaging/third-party/plasma-macos-dock/. "$ROOTFS/usr/share/doc/ifba-os/third-party/plasma-macos-dock/"
chroot "$ROOTFS" env DEBIAN_FRONTEND=noninteractive apt-get purge -y "${KRUNNER_BUILD_PACKAGES[@]}"
chroot "$ROOTFS" env DEBIAN_FRONTEND=noninteractive apt-get autoremove --purge -y
for package in "${KRUNNER_BUILD_PACKAGES[@]}"; do
  if chroot "$ROOTFS" dpkg-query -W -f='${db:Status-Status}' "$package" 2>/dev/null | grep -qx installed; then
    printf 'Build-only dependency remains installed: %s\n' "$package" >&2
    exit 1
  fi
done
chroot "$ROOTFS" /bin/bash -euxc '
  id ubuntu >/dev/null 2>&1 || useradd -m -s /bin/bash -G sudo ubuntu
  passwd -d ubuntu
  mkdir -p /etc/sddm.conf.d /usr/share/backgrounds/ifba-os /usr/share/ifba-os/assets/wallpapers \
    /usr/share/ifba-os/assets/icons /usr/share/color-schemes /etc/xdg/autostart \
    /usr/share/plasma/desktoptheme /usr/share/aurorae/themes /usr/share/Kvantum /etc/xdg/Kvantum \
    /usr/share/doc/ifba-os/third-party/WhiteSur-kde \
    /usr/share/plasma/look-and-feel /etc/gtk-3.0 /etc/gtk-4.0 \
    /etc/skel/Desktop /etc/skel/.config/autostart /etc/skel/.config/ifba-ai \
    /etc/skel/.local/share/ifba-ai /etc/skel/.cache/ifba-ai \
    /home/ubuntu/Desktop /home/ubuntu/.config/autostart /home/ubuntu/.config/ifba-ai \
    /home/ubuntu/.local/share/ifba-ai /home/ubuntu/.cache/ifba-ai
  printf "[General]\nDisplayServer=x11\n\n[Theme]\nCurrent=breeze\n\n[Autologin]\nUser=ubuntu\nSession=plasmax11.desktop\nRelogin=false\n" > /etc/sddm.conf.d/10-ifba-os.conf
  ln -sfn /lib/systemd/system/graphical.target /etc/systemd/system/default.target
  ln -sfn /lib/systemd/system/sddm.service /etc/systemd/system/display-manager.service
  printf "LANG=pt_BR.UTF-8\nLANGUAGE=pt_BR:pt:en\n" > /etc/default/locale
  printf "pt_BR.UTF-8 UTF-8\n" > /etc/locale.gen
  locale-gen pt_BR.UTF-8
  printf "America/Bahia\n" > /etc/timezone
  ln -sfn /usr/share/zoneinfo/America/Bahia /etc/localtime
  update-alternatives --install /usr/bin/x-www-browser x-www-browser /usr/bin/firefox 100
  apt-get clean
  rm -rf /var/lib/apt/lists/* /tmp/*
'
install -D -m 0644 /dev/null "$ROOTFS/etc/ifba-os/live-demo"
mkdir -p "$ROOTFS/etc/systemd/system/multi-user.target.wants" "$ROOTFS/etc/NetworkManager/system-connections" \
  "$ROOTFS/etc/NetworkManager/conf.d" \
  "$ROOTFS/usr/local/bin" "$ROOTFS/usr/lib/python3/dist-packages" \
  "$ROOTFS/usr/lib/systemd/user/default.target.wants" "$ROOTFS/usr/share/dbus-1/services"
ln -sfn /lib/systemd/system/qemu-guest-agent.service "$ROOTFS/etc/systemd/system/multi-user.target.wants/qemu-guest-agent.service"
ln -sfn /usr/lib/systemd/system/NetworkManager.service "$ROOTFS/etc/systemd/system/multi-user.target.wants/NetworkManager.service"
rm -f "$ROOTFS/etc/systemd/system/multi-user.target.wants/systemd-networkd.service" \
  "$ROOTFS/etc/systemd/system/sockets.target.wants/systemd-networkd.socket"
ln -sfn /dev/null "$ROOTFS/etc/systemd/system/systemd-networkd.service"
ln -sfn /dev/null "$ROOTFS/etc/systemd/system/systemd-networkd.socket"
# Ubuntu's vendor 10-globally-managed-devices.conf marks everything except
# Wi-Fi/cellular unmanaged. Override its same-named drop-in, then explicitly
# manage Ethernet without relying on interface names. This matches enp0s1,
# virtio, e1000, and physical Ethernet while preserving Wi-Fi policy.
cat > "$ROOTFS/etc/NetworkManager/conf.d/10-globally-managed-devices.conf" <<'NMCONF'
[keyfile]
unmanaged-devices=
NMCONF
cat > "$ROOTFS/etc/NetworkManager/conf.d/20-ifba-managed-ethernet.conf" <<'NMDEVICE'
[device-ifba-managed-ethernet]
match-device=type:ethernet
managed=1
NMDEVICE
cat > "$ROOTFS/etc/NetworkManager/system-connections/ifba-wired.nmconnection" <<'NETWORK'
[connection]
id=IFBA OS Ethernet
type=ethernet
autoconnect=true
autoconnect-priority=100

[ipv4]
method=auto

[ipv6]
method=auto
NETWORK
chmod 0600 "$ROOTFS/etc/NetworkManager/system-connections/ifba-wired.nmconnection"
LIVE_BASHRC_IS_SKELETON=0
if cmp -s "$ROOTFS/home/ubuntu/.bashrc" "$ROOTFS/etc/skel/.bashrc"; then
  LIVE_BASHRC_IS_SKELETON=1
fi
install -D -m 0644 /work/packaging/konsole/IFBA\ Terminal.profile \
  "$ROOTFS/usr/share/konsole/IFBA Terminal.profile"
install -D -m 0755 /work/packaging/ifba-visual-profile "$ROOTFS/usr/bin/ifba-visual-profile"
install -D -m 0755 /work/packaging/ifba-visual-profile-dialog "$ROOTFS/usr/bin/ifba-visual-profile-dialog"
install -D -m 0644 /work/packaging/design-system/visual-motionrc \
  "$ROOTFS/usr/share/ifba-os/design-system/visual-motionrc"
install -D -m 0644 /work/packaging/ifba-visual-profile.desktop \
  "$ROOTFS/usr/share/applications/ifba-visual-profile.desktop"
install -D -m 0644 /work/packaging/konsole/IFBA\ Glass.colorscheme \
  "$ROOTFS/usr/share/konsole/IFBA Glass.colorscheme"
for home_root in "$ROOTFS/etc/skel" "$ROOTFS/home/ubuntu"; do
  if [[ "$home_root" == "$ROOTFS/etc/skel" || ! -e "$home_root/.local/share/konsole/IFBA Terminal.profile" ]]; then
    install -D -m 0644 /work/packaging/konsole/IFBA\ Terminal.profile \
      "$home_root/.local/share/konsole/IFBA Terminal.profile"
  fi
  if [[ "$home_root" == "$ROOTFS/etc/skel" || ! -e "$home_root/.local/share/konsole/IFBA Glass.colorscheme" ]]; then
    install -D -m 0644 /work/packaging/konsole/IFBA\ Glass.colorscheme \
      "$home_root/.local/share/konsole/IFBA Glass.colorscheme"
  fi
  if [[ ! -e "$home_root/.config/konsolerc" ]]; then
    install -D -m 0644 /dev/null "$home_root/.config/konsolerc"
    cat > "$home_root/.config/konsolerc" <<'KONSOLE'
[Desktop Entry]
DefaultProfile=IFBA Terminal.profile
KONSOLE
  fi
  if [[ ! -e "$home_root/.bashrc" ]]; then
    touch "$home_root/.bashrc"
  fi
  if ! grep -q 'ifba-prompt.sh' "$home_root/.bashrc" && \
    { [[ "$home_root" == "$ROOTFS/etc/skel" ]] || [[ "$LIVE_BASHRC_IS_SKELETON" == 1 ]]; }; then
    cat >> "$home_root/.bashrc" <<'BASHRC'

if [ -r "$HOME/.local/share/ifba-os/ifba-prompt.sh" ]; then
  . "$HOME/.local/share/ifba-os/ifba-prompt.sh"
fi
BASHRC
  fi
  install -D -m 0644 /work/packaging/ifba-prompt.sh \
    "$home_root/.local/share/ifba-os/ifba-prompt.sh"
done
cp /work/assets/wallpapers/ifba-os-desktop.png "$ROOTFS/usr/share/backgrounds/ifba-os/wallpaper.png"
cp /work/assets/wallpapers/ifba-os-desktop.png "$ROOTFS/usr/share/ifba-os/assets/wallpapers/"
install -D -m 0644 /work/assets/wallpapers/ifba-os-lockscreen.png \
  "$ROOTFS/usr/share/backgrounds/ifba-os/lockscreen-wallpaper.png"
install -D -m 0644 /work/packaging/plasma/ifba-os-lockscreen.conf \
  "$ROOTFS/etc/skel/.config/kscreenlockerrc"
if [[ ! -e "$ROOTFS/home/ubuntu/.config/kscreenlockerrc" ]]; then
  install -D -m 0644 /work/packaging/plasma/ifba-os-lockscreen.conf \
    "$ROOTFS/home/ubuntu/.config/kscreenlockerrc"
fi
install -D -m 0644 /work/packaging/plasma/ifba-os-lockscreen.conf \
  "$ROOTFS/etc/xdg/kscreenlockerrc"
install -D -m 0644 /work/packaging/sddm/ifba-theme.conf.user \
  "$ROOTFS/usr/share/sddm/themes/breeze/theme.conf.user"
cp -R /work/assets/icons/. "$ROOTFS/usr/share/ifba-os/assets/icons/"
cp -R /work/ai/ifba_ai "$ROOTFS/usr/lib/python3/dist-packages/"
cp /work/packaging/ifba-ai-ui "$ROOTFS/usr/bin/ifba-ai-ui"
cp /work/packaging/ifba-ai-daemon "$ROOTFS/usr/bin/ifba-ai-daemon"
cp /work/tools/ifba-os-version "$ROOTFS/usr/local/bin/ifba-os-version"
chmod 0755 "$ROOTFS/usr/bin/ifba-ai-ui" "$ROOTFS/usr/bin/ifba-ai-daemon" "$ROOTFS/usr/local/bin/ifba-os-version"
cp /work/packaging/ifba-ai.desktop "$ROOTFS/usr/share/applications/ifba-ai.desktop"
cp /work/packaging/ifba-ai.css "$ROOTFS/usr/share/ifba-os/ifba-ai.css"
cp /work/packaging/org.ifba.OS.AI.service "$ROOTFS/usr/share/dbus-1/services/"
cp /work/packaging/ifba-ai.service "$ROOTFS/usr/lib/systemd/user/"
cp /work/packaging/firefox.desktop /work/packaging/suap-ifba.desktop /work/packaging/ava-ifba.desktop "$ROOTFS/usr/share/applications/"
cp /work/welcome/ifba_welcome.py "$ROOTFS/usr/bin/ifba-welcome"
install -D -m 0644 /work/packaging/design-system/ifba-welcome.qss \
  "$ROOTFS/usr/share/ifba-os/ifba-welcome.qss"
chmod 0755 "$ROOTFS/usr/bin/ifba-welcome"
cp /work/packaging/ifba-os-welcome.desktop "$ROOTFS/usr/share/applications/"
cp /work/packaging/ifba-os-welcome-autostart.desktop "$ROOTFS/etc/xdg/autostart/ifba-os-welcome.desktop"
install -D -m 0644 /work/packaging/ifba-os-welcome-docs.html "$ROOTFS/usr/share/doc/ifba-os/welcome.html"
mkdir -p "$ROOTFS/etc/calamares/modules" "$ROOTFS/etc/calamares/branding/ifba-os"
cp /work/packaging/calamares/settings.conf "$ROOTFS/etc/calamares/settings.conf"
cp /work/packaging/calamares/partition.conf /work/packaging/calamares/unpackfs.conf \
  /work/packaging/calamares/removeuser.conf /work/packaging/calamares/shellprocess.conf \
  /work/packaging/calamares/locale.conf /work/packaging/calamares/keyboard.conf \
  /work/packaging/calamares/users.conf /work/packaging/calamares/displaymanager.conf \
  /work/packaging/calamares/initramfs.conf /work/packaging/calamares/bootloader.conf \
  "$ROOTFS/etc/calamares/modules/"
cp /work/packaging/calamares/branding.desc "$ROOTFS/etc/calamares/branding/ifba-os/branding.desc"
cp /work/packaging/ifba-os-installer "$ROOTFS/usr/bin/ifba-os-installer"
chmod 0755 "$ROOTFS/usr/bin/ifba-os-installer"
cp /work/packaging/ifba-os-installer.desktop "$ROOTFS/usr/share/applications/"
if [[ ! -e "$ROOTFS/home/ubuntu/Desktop/SUAP.desktop" ]]; then
  cp /work/packaging/suap-ifba-link.desktop "$ROOTFS/home/ubuntu/Desktop/SUAP.desktop"
  chmod +x "$ROOTFS/home/ubuntu/Desktop/SUAP.desktop"
fi
if [[ ! -e "$ROOTFS/home/ubuntu/Desktop/AVA-IFBA.desktop" ]]; then
  cp /work/packaging/ava-ifba-link.desktop "$ROOTFS/home/ubuntu/Desktop/AVA-IFBA.desktop"
  chmod +x "$ROOTFS/home/ubuntu/Desktop/AVA-IFBA.desktop"
fi
cp /work/packaging/suap-ifba-link.desktop "$ROOTFS/etc/skel/Desktop/SUAP.desktop"
cp /work/packaging/ava-ifba-link.desktop "$ROOTFS/etc/skel/Desktop/AVA-IFBA.desktop"
if [[ ! -e "$ROOTFS/home/ubuntu/Desktop/IFBA-AI.desktop" ]]; then
  cp /work/packaging/ifba-ai.desktop "$ROOTFS/home/ubuntu/Desktop/IFBA-AI.desktop"
  chmod +x "$ROOTFS/home/ubuntu/Desktop/IFBA-AI.desktop"
fi
if [[ ! -e "$ROOTFS/home/ubuntu/Desktop/IFBA-OS-Installer.desktop" ]]; then
  cp /work/packaging/ifba-os-installer.desktop "$ROOTFS/home/ubuntu/Desktop/IFBA-OS-Installer.desktop"
  chmod +x "$ROOTFS/home/ubuntu/Desktop/IFBA-OS-Installer.desktop"
fi
cp /work/packaging/ifba-ai.desktop "$ROOTFS/etc/skel/Desktop/IFBA-AI.desktop"
chmod +x "$ROOTFS/etc/skel/Desktop/"*.desktop
install -D -m 0644 /work/packaging/color-schemes/IFBA-OS-Dark.colors \
  "$ROOTFS/usr/share/color-schemes/IFBA-OS-Dark.colors"
install -D -m 0644 /work/packaging/gtk/gtk.css "$ROOTFS/etc/gtk-3.0/gtk.css"
install -D -m 0644 /work/packaging/gtk/gtk.css "$ROOTFS/etc/gtk-4.0/gtk.css"
install -D -m 0644 /work/packaging/gtk/settings.ini "$ROOTFS/etc/gtk-3.0/settings.ini"
install -D -m 0644 /work/packaging/gtk/settings.ini "$ROOTFS/etc/gtk-4.0/settings.ini"
for home_root in "$ROOTFS/etc/skel" "$ROOTFS/home/ubuntu"; do
  if [[ ! -e "$home_root/.config/gtk-3.0/gtk.css" ]]; then
    install -D -m 0644 /work/packaging/gtk/gtk.css "$home_root/.config/gtk-3.0/gtk.css"
  fi
  if [[ ! -e "$home_root/.config/gtk-4.0/gtk.css" ]]; then
    install -D -m 0644 /work/packaging/gtk/gtk.css "$home_root/.config/gtk-4.0/gtk.css"
  fi
  if [[ ! -e "$home_root/.config/gtk-3.0/settings.ini" ]]; then
    install -D -m 0644 /work/packaging/gtk/settings.ini "$home_root/.config/gtk-3.0/settings.ini"
  fi
  if [[ ! -e "$home_root/.config/gtk-4.0/settings.ini" ]]; then
    install -D -m 0644 /work/packaging/gtk/settings.ini "$home_root/.config/gtk-4.0/settings.ini"
  fi
done
cat > "$ROOTFS/etc/skel/.config/kdeglobals" <<'KDEGLOBALS'
[General]
ColorScheme=IFBA-OS-Dark
Name=IFBA OS Dark
Font=Inter,10,-1,5,50,0,0,0,0,0
[Icons]
Theme=breeze-dark
[KDE]
LookAndFeelPackage=org.ifbaos.desktop
SingleClick=false
widgetStyle=kvantum
KDEGLOBALS
if [[ ! -e "$ROOTFS/home/ubuntu/.config/kdeglobals" ]]; then
  cp "$ROOTFS/etc/skel/.config/kdeglobals" "$ROOTFS/home/ubuntu/.config/kdeglobals"
fi
install -D -m 0644 "$ROOTFS/etc/skel/.config/kdeglobals" "$ROOTFS/etc/xdg/kdeglobals"
install -D -m 0644 /work/packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark/metadata.json \
  "$ROOTFS/usr/share/plasma/desktoptheme/IFBA-WhiteSur-Dark/metadata.json"
cp -R /work/packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark/. \
  "$ROOTFS/usr/share/plasma/desktoptheme/IFBA-WhiteSur-Dark/"
install -D -m 0644 /work/packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark/colors \
  "$ROOTFS/usr/share/plasma/desktoptheme/IFBA-WhiteSur-Dark/colors"
install -D -m 0644 /work/packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark/plasmarc \
  "$ROOTFS/etc/skel/.config/plasmarc"
install -D -m 0644 /work/packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark/plasmarc \
  "$ROOTFS/etc/xdg/plasmarc"
if [[ ! -e "$ROOTFS/home/ubuntu/.config/plasmarc" ]]; then
  install -D -m 0644 /work/packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark/plasmarc \
    "$ROOTFS/home/ubuntu/.config/plasmarc"
fi
install -D -m 0644 /work/packaging/kvantum/kvantum.kvconfig \
  "$ROOTFS/etc/skel/.config/Kvantum/kvantum.kvconfig"
install -D -m 0644 /work/packaging/kvantum/kvantum.kvconfig \
  "$ROOTFS/etc/xdg/Kvantum/kvantum.kvconfig"
if [[ ! -e "$ROOTFS/home/ubuntu/.config/Kvantum/kvantum.kvconfig" ]]; then
  install -D -m 0644 /work/packaging/kvantum/kvantum.kvconfig \
    "$ROOTFS/home/ubuntu/.config/Kvantum/kvantum.kvconfig"
fi
for kvantum_theme in IFBA-Glass IFBA-Glass-Opaque; do
  install -D -m 0644 "/work/packaging/kvantum/$kvantum_theme/$kvantum_theme.svg" \
    "$ROOTFS/usr/share/Kvantum/$kvantum_theme/$kvantum_theme.svg"
  install -D -m 0644 "/work/packaging/kvantum/$kvantum_theme/$kvantum_theme.kvconfig" \
    "$ROOTFS/usr/share/Kvantum/$kvantum_theme/$kvantum_theme.kvconfig"
done
for upstream_file in LICENSE AUTHORS UPSTREAM.md; do
  install -D -m 0644 "/work/packaging/third-party/WhiteSur-kde/$upstream_file" \
    "$ROOTFS/usr/share/doc/ifba-os/third-party/WhiteSur-kde/$upstream_file"
done
install -D -m 0644 /work/packaging/plasma/ifba-os-shell.conf "$ROOTFS/etc/xdg/plasmashellrc"
install -D -m 0644 /work/packaging/plasma/ifba-os-shell.conf "$ROOTFS/etc/skel/.config/plasmashellrc"
if [[ ! -e "$ROOTFS/home/ubuntu/.config/plasmashellrc" ]]; then
  install -D -m 0644 /work/packaging/plasma/ifba-os-shell.conf "$ROOTFS/home/ubuntu/.config/plasmashellrc"
fi
python3 /work/tools/migrate_plasma_shell.py "$ROOTFS/home/ubuntu/.config/plasmashellrc"
python3 /work/tools/migrate_plasma_control_center.py \
  "$ROOTFS/home/ubuntu/.config/plasma-org.kde.plasma.desktop-appletsrc"
# These are stale build-cache components from the retired UI, not user data.
rm -rf "$ROOTFS/usr/share/plasma/plasmoids/org.ifbaos.controlcenter" \
  "$ROOTFS/usr/share/plasma/shells/org.ifbaos.plasma"
install -D -m 0644 /work/packaging/plasma/ifba-os/metadata.json "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/metadata.json"
install -D -m 0644 /work/packaging/plasma/ifba-os/contents/defaults "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/contents/defaults"
install -D -m 0644 /work/packaging/plasma/ifba-os/contents/layouts/org.kde.plasma.desktop-layout.js "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/contents/layouts/org.kde.plasma.desktop-layout.js"
cp -R /work/packaging/plasma/window-decoration/IFBA-Window \
  "$ROOTFS/usr/share/aurorae/themes/"
for decoration_scale in _x1.25 _x1.5 _x1.75 _x2.0; do
  scaled_theme="IFBA-Window$decoration_scale"
  scaled_theme_dir="$ROOTFS/usr/share/aurorae/themes/$scaled_theme"
  source_theme_dir="/work/packaging/plasma/window-decoration/$scaled_theme"
  install -D -m 0644 "$source_theme_dir/decoration.svg" "$scaled_theme_dir/decoration.svg"
  for decoration_asset in minimize.svg maximize.svg restore.svg close.svg keepabove.svg keepbelow.svg alldesktops.svg; do
    install -D -m 0644 "/work/packaging/plasma/window-decoration/IFBA-Window/$decoration_asset" \
      "$scaled_theme_dir/$decoration_asset"
  done
  sed "s/IFBA-Window/$scaled_theme/g" \
    /work/packaging/plasma/window-decoration/IFBA-Window/metadata.desktop \
    > "$scaled_theme_dir/metadata.desktop"
  sed "s/IFBA-Window/$scaled_theme/g" \
    /work/packaging/plasma/window-decoration/IFBA-Window/metadata.json \
    > "$scaled_theme_dir/metadata.json"
  install -D -m 0644 /work/packaging/plasma/window-decoration/IFBA-Window/IFBA-Windowrc \
    "$scaled_theme_dir/${scaled_theme}rc"
done
install -D -m 0755 /work/packaging/plasma/ifba-os-session-setup "$ROOTFS/usr/local/bin/ifba-os-plasma-session-setup"
chmod 0755 "$ROOTFS/usr/local/bin/ifba-os-plasma-session-setup"
cat > "$ROOTFS/etc/xdg/autostart/ifba-os-plasma-session-setup.desktop" <<'AUTOSTART'
[Desktop Entry]
Type=Application
Name=IFBA OS Desktop Setup
Exec=/usr/local/bin/ifba-os-plasma-session-setup
OnlyShowIn=KDE;
Terminal=false
StartupNotify=false
AUTOSTART
if [[ ! -e "$ROOTFS/home/ubuntu/.config/autostart/ifba-os-plasma-session-setup.desktop" ]]; then
  cp "$ROOTFS/etc/xdg/autostart/ifba-os-plasma-session-setup.desktop" "$ROOTFS/home/ubuntu/.config/autostart/"
fi
cp "$ROOTFS/etc/xdg/autostart/ifba-os-plasma-session-setup.desktop" "$ROOTFS/etc/skel/.config/autostart/"
chroot "$ROOTFS" chown -R ubuntu:ubuntu /home/ubuntu
chmod 0700 "$ROOTFS/home/ubuntu/.config/ifba-ai" "$ROOTFS/home/ubuntu/.local/share/ifba-ai" "$ROOTFS/home/ubuntu/.cache/ifba-ai" \
  "$ROOTFS/etc/skel/.config/ifba-ai" "$ROOTFS/etc/skel/.local/share/ifba-ai" "$ROOTFS/etc/skel/.cache/ifba-ai"
mkdir -p "$ROOTFS/usr/share/plymouth/themes/ifba-os"
cp /work/assets/plymouth/ifba-os-startup.png /work/packaging/plymouth/ifba-os.plymouth /work/packaging/plymouth/ifba-os.script "$ROOTFS/usr/share/plymouth/themes/ifba-os/"
chroot "$ROOTFS" update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth /usr/share/plymouth/themes/ifba-os/ifba-os.plymouth 120
chroot "$ROOTFS" update-alternatives --set default.plymouth /usr/share/plymouth/themes/ifba-os/ifba-os.plymouth
chroot "$ROOTFS" update-initramfs -u -k all
umount "$RESOLV_TARGET" 2>/dev/null || true
umount -R "$ROOTFS/dev" 2>/dev/null || true
umount "$ROOTFS/proc" 2>/dev/null || true
umount -R "$ROOTFS/sys" 2>/dev/null || true
rm -f "$RESOLV_TARGET"
install -D -m 0644 "$BUILD_INFO_FILE" "$ROOTFS/usr/share/ifba-os/build-info.json"
for file in \
  /usr/share/ifba-os/ifba-ai.css \
  /usr/share/ifba-os/ifba-welcome.qss \
  /usr/share/ifba-os/assets/icons/ifba-institutional-symbol.png \
  /usr/share/color-schemes/IFBA-OS-Dark.colors \
  /etc/gtk-3.0/gtk.css \
  /etc/gtk-4.0/gtk.css; do
  test -s "$ROOTFS$file"
done
test -s "$ROOTFS/usr/share/ifba-os/ifba-welcome.qss"
test -x "$ROOTFS/usr/bin/ifba-visual-profile"
test -x "$ROOTFS/usr/bin/ifba-visual-profile-dialog"
test -s "$ROOTFS/usr/share/applications/ifba-visual-profile.desktop"
test -s "$ROOTFS/usr/share/ifba-os/design-system/visual-motionrc"
test -s "$ROOTFS/usr/share/sddm/themes/breeze/theme.conf.user"
for file in /etc/NetworkManager/conf.d/10-globally-managed-devices.conf \
  /etc/NetworkManager/conf.d/20-ifba-managed-ethernet.conf \
  /usr/bin/ifba-visual-profile /usr/bin/ifba-visual-profile-dialog \
  /usr/share/applications/ifba-visual-profile.desktop \
  /usr/share/konsole/IFBA\ Terminal.profile /usr/share/konsole/IFBA\ Glass.colorscheme \
  /usr/share/dbus-1/services/org.ifba.OS.AI.service /usr/lib/systemd/user/ifba-ai.service; do
  test -s "$ROOTFS$file"
done
grep -q '^unmanaged-devices=$' "$ROOTFS/etc/NetworkManager/conf.d/10-globally-managed-devices.conf"
grep -q '^match-device=type:ethernet$' "$ROOTFS/etc/NetworkManager/conf.d/20-ifba-managed-ethernet.conf"
grep -q '^managed=1$' "$ROOTFS/etc/NetworkManager/conf.d/20-ifba-managed-ethernet.conf"
test -L "$ROOTFS/etc/systemd/system/systemd-networkd.service"
test "$(readlink "$ROOTFS/etc/systemd/system/systemd-networkd.service")" = /dev/null
for decoration_file in metadata.desktop metadata.json IFBA-Windowrc decoration.svg minimize.svg maximize.svg restore.svg close.svg; do
  cmp -s "/work/packaging/plasma/window-decoration/IFBA-Window/$decoration_file" \
    "$ROOTFS/usr/share/aurorae/themes/IFBA-Window/$decoration_file"
done
test -s "$ROOTFS/usr/share/plasma/desktoptheme/IFBA-WhiteSur-Dark/metadata.json"
test -s "$ROOTFS/usr/share/plasma/desktoptheme/IFBA-WhiteSur-Dark/widgets/panel-background.svgz"
test -s "$ROOTFS/usr/share/plasma/desktoptheme/IFBA-WhiteSur-Dark/colors"
test -s "$ROOTFS/usr/share/Kvantum/IFBA-Glass/IFBA-Glass.svg"
test -s "$ROOTFS/usr/share/Kvantum/IFBA-Glass-Opaque/IFBA-Glass-Opaque.svg"
test -s "$ROOTFS/usr/share/doc/ifba-os/third-party/WhiteSur-kde/LICENSE"
grep -q '^\[plasmarc\]\[Theme\]$' "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/contents/defaults"
grep -q '^name=IFBA-WhiteSur-Dark$' "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/contents/defaults"
grep -q '^theme=IFBA-Glass$' "$ROOTFS/etc/skel/.config/Kvantum/kvantum.kvconfig"
for decoration_scale in _x1.25 _x1.5 _x1.75 _x2.0; do
  test -s "$ROOTFS/usr/share/aurorae/themes/IFBA-Window$decoration_scale/decoration.svg"
  test -s "$ROOTFS/usr/share/aurorae/themes/IFBA-Window$decoration_scale/IFBA-Window${decoration_scale}rc"
done
find "$ROOTFS/usr/lib" -path '*/qt6/plugins/org.kde.kdecoration3/org.kde.kwin.aurorae.so' -print -quit | grep -q .
for applet in org.kde.milou org.kde.plasma.kickoff org.kde.plasma.kicker \
  org.kde.plasma.appmenu org.kde.plasma.systemtray org.kde.plasma.notifications \
  org.kde.plasma.networkmanagement org.kde.plasma.volume org.kde.plasma.battery \
  org.kde.plasma.bluetooth; do
  find "$ROOTFS/usr/lib" -path "*/qt6/plugins/plasma/applets/$applet.so" -print -quit | grep -q .
done
find "$ROOTFS/usr/lib" -path '*/kf6/krunner/ifba_app_description_runner.so' -print -quit | grep -q .
test -s "$ROOTFS/usr/share/plasma/plasmoids/org.kde.plasma.icontasks/metadata.json"
test ! -e "$ROOTFS/usr/share/plasma/plasmoids/org.ifbaos.controlcenter"
test ! -e "$ROOTFS/usr/share/plasma/shells/org.ifbaos.plasma"
find "$ROOTFS/usr/lib" -path '*/qt6/plugins/plasma/applets/org.kde.plasma.taskmanager.so' -print -quit | grep -q .
find "$ROOTFS/usr/lib" -path '*/qt6/plugins/plasma/applets/org.kde.plasma.trash.so' -print -quit | grep -q .
for launcher in firefox.desktop org.kde.dolphin.desktop org.kde.konsole.desktop ifba-ai.desktop \
  org.thonny.Thonny.desktop org.kde.gcompris.desktop libreoffice-writer.desktop systemsettings.desktop \
  suap-ifba.desktop ava-ifba.desktop; do
  test -s "$ROOTFS/usr/share/applications/$launcher"
done
cmp -s /work/packaging/plasma/ifba-os/metadata.json "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/metadata.json"
cmp -s /work/packaging/plasma/ifba-os/contents/defaults "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/contents/defaults"
cmp -s /work/packaging/plasma/ifba-os/contents/layouts/org.kde.plasma.desktop-layout.js "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/contents/layouts/org.kde.plasma.desktop-layout.js"
grep -q '^ShellPackage=org.kde.plasma.desktop$' "$ROOTFS/etc/skel/.config/plasmashellrc"
grep -q '^ShellPackage=org.kde.plasma.desktop$' "$ROOTFS/etc/xdg/plasmashellrc"
test -s "$ROOTFS/usr/share/plasma/shells/org.kde.plasma.desktop/contents/lockscreen/LockScreenUi.qml"
test -x "$ROOTFS/usr/bin/plasma-apply-wallpaperimage"
test -x "$ROOTFS/usr/local/bin/ifba-os-version"
for package in plasma-workspace plasma-desktop plasma-session-wayland plasma-session-x11 kwin-x11 kwin-style-aurorae milou sddm dolphin konsole fastfetch plasma-discover plasma-nm plasma-pa systemsettings kinfocenter powerdevil power-profiles-daemon upower bluedevil bluez libspa-0.2-bluetooth pipewire-audio pipewire-pulse wireplumber ffmpeg kscreen qt-style-kvantum qt-style-kvantum-themes calamares squashfs-tools efibootmgr kdialog python3-pyqt6 thonny libreoffice-writer gcompris-qt; do
  chroot "$ROOTFS" dpkg-query -s "$package" | grep -q 'Status: install ok installed'
done
for package in "${INSTALLER_BOOT_PACKAGES[@]}"; do
  chroot "$ROOTFS" dpkg-query -s "$package" | grep -q 'Status: install ok installed'
done
test "$(chroot "$ROOTFS" dpkg --print-architecture)" = "$IFBA_ARCH"
test -L "$ROOTFS/etc/systemd/system/default.target"
test "$(readlink "$ROOTFS/etc/systemd/system/default.target")" = /lib/systemd/system/graphical.target
test -L "$ROOTFS/etc/systemd/system/display-manager.service"
test "$(readlink "$ROOTFS/etc/systemd/system/display-manager.service")" = /lib/systemd/system/sddm.service
test -L "$ROOTFS/etc/systemd/system/multi-user.target.wants/NetworkManager.service"
chroot "$ROOTFS" dpkg-query -W plasma-workspace libqt6core6t64 kwin-wayland kwin-x11 sddm
cp -L "$ROOTFS/boot/vmlinuz" "$ISO/casper/vmlinuz"
cp -L "$ROOTFS/boot/initrd.img" "$ISO/casper/initrd"
mksquashfs "$ROOTFS" "$ISO/casper/filesystem.squashfs" -comp xz -b 1M -processors "$(nproc)"
du -sx --block-size=1 "$ROOTFS" | cut -f1 > "$ISO/casper/filesystem.size"
cat > "$ISO/boot/grub/grub.cfg" <<'GRUB'
set timeout=5
set default=0
menuentry "IFBA OS prototype (live)" {
  linux /casper/vmlinuz boot=casper splash ---
  initrd /casper/initrd
}
GRUB
grub-mkrescue -volid "IFBA_OS_26_04_${IFBA_ARCH}" -o "$OUT" "$ISO"
VERIFY_DIR="$(mktemp -d)"
xorriso -osirrox on -indev "$OUT" \
  -extract /casper/vmlinuz "$VERIFY_DIR/vmlinuz" \
  -extract /casper/initrd "$VERIFY_DIR/initrd" \
  -extract /casper/filesystem.squashfs "$VERIFY_DIR/filesystem.squashfs" \
  -extract /boot/grub/grub.cfg "$VERIFY_DIR/grub.cfg" \
  -end
for file in vmlinuz initrd filesystem.squashfs grub.cfg; do
  test -s "$VERIFY_DIR/$file"
done
unsquashfs -cat "$VERIFY_DIR/filesystem.squashfs" usr/share/ifba-os/build-info.json \
  > "$VERIFY_DIR/build-info.json"
cmp -s "$VERIFY_DIR/build-info.json" "$BUILD_INFO_FILE"
rm -rf "$VERIFY_DIR"
