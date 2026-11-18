#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
ROOTFS=/var/cache/ifba-rootfs/rootfs
ISO=/tmp/ifba-iso
OUT=/work/output/ifba-os-ubuntu-24.04-amd64.iso

apt-get update
apt-get install -y --no-install-recommends \
  debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin mtools ca-certificates wget xz-utils

NODE_VERSION=22.23.5
NODE_ARCHIVE="node-v${NODE_VERSION}-linux-x64.tar.xz"
NODE_SHA256=cdeb8670a0c81f51b4dc4ac61919f9b1ad917b304bf8221eb939570663d240f8
wget -nv "https://nodejs.org/dist/v${NODE_VERSION}/${NODE_ARCHIVE}" -O "/tmp/${NODE_ARCHIVE}"
echo "${NODE_SHA256}  /tmp/${NODE_ARCHIVE}" | sha256sum --check
mkdir -p /opt/node-v22
tar -xJf "/tmp/${NODE_ARCHIVE}" --strip-components=1 -C /opt/node-v22
export PATH="/opt/node-v22/bin:$PATH"
node --version
npm --version

npm ci --prefix /work/app --omit=dev --no-audit --no-fund
ELECTRON_INSTALL_PLATFORM=linux ELECTRON_INSTALL_ARCH=x64 \
  node /work/app/node_modules/electron/install.js

if [[ ! -e "$ROOTFS/etc/os-release" ]]; then
  rm -rf "$ROOTFS"
  mkdir -p "$ROOTFS"
  debootstrap --arch=amd64 noble "$ROOTFS" http://archive.ubuntu.com/ubuntu
fi

cat > "$ROOTFS/etc/apt/sources.list" <<'SOURCES'
deb http://archive.ubuntu.com/ubuntu noble main universe multiverse
deb http://archive.ubuntu.com/ubuntu noble-updates main universe multiverse
deb http://security.ubuntu.com/ubuntu noble-security main universe multiverse
SOURCES

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
chroot "$ROOTFS" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  linux-image-generic casper plymouth systemd-sysv xfce4 lightdm lightdm-gtk-greeter \
  xserver-xorg xinit network-manager network-manager-gnome xdg-utils \
  greybird-gtk-theme xfce4-power-manager xfce4-pulseaudio-plugin xfce4-whiskermenu-plugin \
  libnss3 libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 libasound2t64 \
  libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libdrm2 \
  libxkbcommon0 libpango-1.0-0 \
  netsurf-gtk sudo dbus-x11 policykit-1

chroot "$ROOTFS" /bin/bash -euxc '
  id ubuntu >/dev/null 2>&1 || useradd -m -s /bin/bash -G sudo ubuntu
  passwd -d ubuntu
  mkdir -p /var/crash /etc/lightdm/lightdm.conf.d /usr/share/backgrounds/ifba-os \
    /usr/share/xfce4/helpers /usr/share/icons/hicolor/128x128/apps \
    /usr/lib/ifba-os/electron /usr/local/bin /etc/xdg/autostart \
    /etc/xdg/xfce4/xfconf/xfce-perchannel-xml /etc/xdg/xfce4/panel \
    /etc/xdg/xfce4
  printf "[Seat:*]\nuser-session=xfce\ngreeter-session=lightdm-gtk-greeter\nautologin-user=ubuntu\nautologin-user-timeout=0\n" > /etc/lightdm/lightdm.conf.d/50-ifba-autologin.conf
  update-alternatives --install /usr/bin/x-www-browser x-www-browser /usr/bin/netsurf-gtk 50
  apt-get clean
    rm -rf /var/lib/apt/lists/* /tmp/*
'

rm -rf "$ISO"
mkdir -p "$ISO/casper" "$ISO/boot/grub"
cp "$ROOTFS/boot/vmlinuz-"* "$ISO/casper/vmlinuz"
cp "$ROOTFS/boot/initrd.img-"* "$ISO/casper/initrd"
cp /work/assets/wallpapers/ifba-os-desktop.png "$ROOTFS/usr/share/backgrounds/ifba-os/wallpaper.png"
mkdir -p \
  "$ROOTFS/usr/share/ifba-os/app" \
  "$ROOTFS/usr/share/ifba-os/assets" \
  "$ROOTFS/usr/share/ifba-os/assets/wallpapers" \
  "$ROOTFS/etc/xdg/xfce4/xfconf/xfce-perchannel-xml" \
  "$ROOTFS/etc/xdg/xfce4/panel" \
  "$ROOTFS/etc/xdg/xfce4" \
  "$ROOTFS/etc/xdg/autostart" \
  "$ROOTFS/usr/share/xfce4/helpers" \
  "$ROOTFS/usr/share/icons/hicolor/128x128/apps" \
  "$ROOTFS/usr/lib/ifba-os/electron" \
  "$ROOTFS/usr/local/bin" \
  "$ROOTFS/home/ubuntu/Desktop" \
  "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml" \
  "$ROOTFS/home/ubuntu/.config/xfce4" \
  "$ROOTFS/home/ubuntu/.config"
cp /work/app/package.json /work/app/package-lock.json /work/app/main.js \
  /work/app/preload.js /work/app/index.html /work/app/renderer.js \
  /work/app/style.css "$ROOTFS/usr/share/ifba-os/app/"
cp -R /work/app/node_modules/electron/dist/. "$ROOTFS/usr/lib/ifba-os/electron/"
cp -R /work/assets/icons "$ROOTFS/usr/share/ifba-os/assets/"
cp /work/assets/wallpapers/ifba-os-desktop.png "$ROOTFS/usr/share/ifba-os/assets/wallpapers/"
cp /work/packaging/ifba-os-welcome.desktop "$ROOTFS/home/ubuntu/Desktop/IFBA-OS-Welcome.desktop"
cp /work/packaging/ifba-os-welcome.desktop "$ROOTFS/etc/xdg/autostart/ifba-os-welcome.desktop"
cp /work/packaging/netsurf.desktop "$ROOTFS/home/ubuntu/Desktop/Navegador-Web.desktop"
cp /work/packaging/netsurf.desktop "$ROOTFS/usr/share/applications/netsurf.desktop"
cp /work/packaging/xfce4-desktop.xml "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml"
cp /work/packaging/xfce4-desktop.xml "$ROOTFS/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml"
cp /work/packaging/xfce4-panel.xml "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml"
cp /work/packaging/xfce4-panel.xml "$ROOTFS/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml"
cp /work/packaging/xfce4-panel.xml "$ROOTFS/etc/xdg/xfce4/panel/default.xml"
cp /work/packaging/xfce4-keyboard-shortcuts.xml "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-keyboard-shortcuts.xml"
cp /work/packaging/xfce4-netsurf-helper.desktop "$ROOTFS/usr/share/xfce4/helpers/netsurf.desktop"
cp /work/packaging/xfce4-helpers.rc "$ROOTFS/etc/xdg/xfce4/helpers.rc"
cp /work/packaging/xfce4-helpers.rc "$ROOTFS/home/ubuntu/.config/xfce4/helpers.rc"
cp /work/assets/icons/ifba-mark-placeholder.png "$ROOTFS/usr/share/icons/hicolor/128x128/apps/ifba-os-menu.png"
chroot "$ROOTFS" gtk-update-icon-cache -f /usr/share/icons/hicolor
cat > "$ROOTFS/usr/share/ifba-os/mimeapps.list" <<'MIME'
[Default Applications]
x-scheme-handler/http=netsurf.desktop
x-scheme-handler/https=netsurf.desktop
text/html=netsurf.desktop
application/xhtml+xml=netsurf.desktop
MIME
cp "$ROOTFS/usr/share/ifba-os/mimeapps.list" "$ROOTFS/etc/xdg/mimeapps.list"
cp "$ROOTFS/usr/share/ifba-os/mimeapps.list" "$ROOTFS/home/ubuntu/.config/mimeapps.list"
cat > "$ROOTFS/usr/bin/ifba-os-welcome" <<'LAUNCHER'
#!/bin/sh
exec /usr/lib/ifba-os/electron/electron /usr/share/ifba-os/app "$@"
LAUNCHER
cat > "$ROOTFS/etc/xdg/autostart/ifba-network-indicator.desktop" <<'NETWORK'
[Desktop Entry]
Type=Application
Name=IFBA OS Network Indicator
Exec=nm-applet
OnlyShowIn=XFCE;
Terminal=false
NETWORK
chmod +x "$ROOTFS/usr/bin/ifba-os-welcome"
chroot "$ROOTFS" chown -R ubuntu:ubuntu /home/ubuntu/Desktop /home/ubuntu/.config
chmod +x "$ROOTFS/home/ubuntu/Desktop/IFBA-OS-Welcome.desktop" "$ROOTFS/home/ubuntu/Desktop/Navegador-Web.desktop"
cleanup_mounts
rm -f "$RESOLV_TARGET"

mksquashfs "$ROOTFS" "$ISO/casper/filesystem.squashfs" -comp xz -b 1M -e boot
du -sx --block-size=1 "$ROOTFS" | cut -f1 > "$ISO/casper/filesystem.size"
cat > "$ISO/boot/grub/grub.cfg" <<'GRUB'
set timeout=5
set default=0
menuentry "IFBA OS prototype (live)" {
  linux /casper/vmlinuz boot=casper quiet ---
  initrd /casper/initrd
}
GRUB
grub-mkrescue -volid IFBA_OS_24_04 -o "$OUT" "$ISO"
