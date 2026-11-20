#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
ROOTFS=/var/cache/ifba-rootfs/rootfs-plasma-26.04
ISO=/tmp/ifba-iso
OUT=/work/output/ifba-os-ubuntu-26.04-amd64.iso

apt-get update
apt-get install -y --no-install-recommends debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin mtools curl gnupg ca-certificates
rm -rf "$ISO"
mkdir -p "$ISO/casper" "$ISO/boot/grub"
if [[ ! -e "$ROOTFS/etc/os-release" ]]; then
  rm -rf "$ROOTFS"
  mkdir -p "$ROOTFS"
  debootstrap --arch=amd64 resolute "$ROOTFS" http://archive.ubuntu.com/ubuntu
fi
cat > "$ROOTFS/etc/apt/sources.list" <<'SOURCES'
deb http://archive.ubuntu.com/ubuntu resolute main universe multiverse
deb http://archive.ubuntu.com/ubuntu resolute-updates main universe multiverse
deb http://security.ubuntu.com/ubuntu resolute-security main universe multiverse
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
chroot "$ROOTFS" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  linux-image-generic casper plymouth plymouth-themes systemd-sysv \
  plasma-desktop plasma-session-wayland plasma-session-x11 kwin-x11 \
  sddm sddm-theme-breeze breeze-gtk-theme breeze-icon-theme breeze-cursor-theme \
  dolphin konsole plasma-discover plasma-nm plasma-pa systemsettings \
  xserver-xorg xinit network-manager xdg-utils xdg-user-dirs fonts-inter \
  xdg-desktop-portal-kde xdg-desktop-portal-gtk \
  python3-dbus python3-gi gir1.2-gtk-3.0 gnome-keyring libpam-gnome-keyring \
  libsecret-tools python3-xlib python3-pyatspi at-spi2-core gir1.2-atspi-2.0 \
  libnss3 libatk1.0-0 libatk-bridge2.0-0t64 libcups2t64 libasound2t64 \
  libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libdrm2 \
  libxkbcommon0 libpango-1.0-0 firefox firefox-l10n-pt-br sudo dbus-x11 \
  polkitd pkexec qemu-guest-agent locales
chroot "$ROOTFS" /bin/bash -euxc '
  id ubuntu >/dev/null 2>&1 || useradd -m -s /bin/bash -G sudo ubuntu
  passwd -d ubuntu
  mkdir -p /etc/sddm.conf.d /usr/share/backgrounds/ifba-os /usr/share/ifba-os/assets/wallpapers \
    /usr/share/ifba-os/assets/icons /usr/share/color-schemes /etc/xdg/autostart \
    /usr/share/plasma/look-and-feel \
    /etc/skel/Desktop /etc/skel/.config/autostart /etc/skel/.config/ifba-ai \
    /etc/skel/.local/share/ifba-ai /etc/skel/.cache/ifba-ai \
    /home/ubuntu/Desktop /home/ubuntu/.config/autostart /home/ubuntu/.config/ifba-ai \
    /home/ubuntu/.local/share/ifba-ai /home/ubuntu/.cache/ifba-ai
  printf "[General]\nDisplayServer=x11\n\n[Theme]\nCurrent=breeze\n\n[Autologin]\nUser=ubuntu\nSession=plasma.desktop\nRelogin=false\n" > /etc/sddm.conf.d/10-ifba-os.conf
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
mkdir -p "$ROOTFS/etc/systemd/system/multi-user.target.wants" "$ROOTFS/etc/NetworkManager/system-connections" \
  "$ROOTFS/usr/local/bin" "$ROOTFS/usr/lib/python3/dist-packages" \
  "$ROOTFS/usr/lib/systemd/user/default.target.wants" "$ROOTFS/usr/share/dbus-1/services"
ln -sfn /lib/systemd/system/qemu-guest-agent.service "$ROOTFS/etc/systemd/system/multi-user.target.wants/qemu-guest-agent.service"
ln -sfn /usr/lib/systemd/system/NetworkManager.service "$ROOTFS/etc/systemd/system/multi-user.target.wants/NetworkManager.service"
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
cp /work/assets/wallpapers/ifba-os-desktop.png "$ROOTFS/usr/share/backgrounds/ifba-os/wallpaper.png"
cp /work/assets/wallpapers/ifba-os-desktop.png "$ROOTFS/usr/share/ifba-os/assets/wallpapers/"
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
ln -sfn ../ifba-ai.service "$ROOTFS/usr/lib/systemd/user/default.target.wants/ifba-ai.service"
cp /work/packaging/firefox.desktop /work/packaging/suap-ifba.desktop /work/packaging/ava-ifba.desktop "$ROOTFS/usr/share/applications/"
cp /work/packaging/suap-ifba-link.desktop "$ROOTFS/home/ubuntu/Desktop/SUAP.desktop"
cp /work/packaging/ava-ifba-link.desktop "$ROOTFS/home/ubuntu/Desktop/AVA-IFBA.desktop"
cp /work/packaging/suap-ifba-link.desktop "$ROOTFS/etc/skel/Desktop/SUAP.desktop"
cp /work/packaging/ava-ifba-link.desktop "$ROOTFS/etc/skel/Desktop/AVA-IFBA.desktop"
cp /work/packaging/ifba-ai.desktop "$ROOTFS/home/ubuntu/Desktop/IFBA-AI.desktop"
cp /work/packaging/ifba-ai.desktop "$ROOTFS/etc/skel/Desktop/IFBA-AI.desktop"
chmod +x "$ROOTFS/home/ubuntu/Desktop/"*.desktop "$ROOTFS/etc/skel/Desktop/"*.desktop
cat > "$ROOTFS/usr/share/color-schemes/IFBA-OS-Dark.colors" <<'COLORS'
[General]
Name=IFBA OS Dark
ColorScheme=IFBA OS Dark
[Colors:Window]
BackgroundNormal=25,27,29
BackgroundAlternate=34,37,39
ForegroundNormal=238,239,240
ForegroundInactive=154,158,160
[Colors:View]
BackgroundNormal=19,21,23
BackgroundAlternate=30,32,34
ForegroundNormal=238,239,240
ForegroundInactive=154,158,160
[Colors:Button]
BackgroundNormal=38,41,43
BackgroundAlternate=47,50,52
ForegroundNormal=238,239,240
[Colors:Selection]
BackgroundNormal=48,135,70
BackgroundAlternate=39,117,59
ForegroundNormal=255,255,255
[Colors:Tooltip]
BackgroundNormal=35,38,40
BackgroundAlternate=42,45,47
ForegroundNormal=238,239,240
[WM]
activeBackground=25,27,29
activeForeground=255,255,255
inactiveBackground=34,37,39
inactiveForeground=183,186,188
COLORS
cat > "$ROOTFS/etc/skel/.config/kdeglobals" <<'KDEGLOBALS'
[General]
ColorScheme=IFBA-OS-Dark
Name=IFBA OS Dark
[Icons]
Theme=breeze-dark
[KDE]
LookAndFeelPackage=org.ifbaos.desktop
SingleClick=false
KDEGLOBALS
cp "$ROOTFS/etc/skel/.config/kdeglobals" "$ROOTFS/home/ubuntu/.config/kdeglobals"
install -D -m 0644 "$ROOTFS/etc/skel/.config/kdeglobals" "$ROOTFS/etc/xdg/kdeglobals"
install -D -m 0644 /work/packaging/plasma/ifba-os/metadata.json "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/metadata.json"
install -D -m 0644 /work/packaging/plasma/ifba-os/contents/defaults "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/contents/defaults"
install -D -m 0644 /work/packaging/plasma/ifba-os/contents/layouts/org.kde.plasma.desktop-layout.js "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/contents/layouts/org.kde.plasma.desktop-layout.js"
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
cp "$ROOTFS/etc/xdg/autostart/ifba-os-plasma-session-setup.desktop" "$ROOTFS/home/ubuntu/.config/autostart/"
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
install -D -m 0644 /work/output/.ifba-os-build-info.json "$ROOTFS/usr/share/ifba-os/build-info.json"
for file in /usr/share/ifba-os/build-info.json /usr/share/backgrounds/ifba-os/wallpaper.png /usr/share/color-schemes/IFBA-OS-Dark.colors /etc/skel/.config/kdeglobals /etc/sddm.conf.d/10-ifba-os.conf /usr/share/plasma/look-and-feel/org.ifbaos.desktop/metadata.json /usr/share/plasma/look-and-feel/org.ifbaos.desktop/contents/layouts/org.kde.plasma.desktop-layout.js /usr/bin/firefox /usr/bin/ifba-ai-ui /usr/share/applications/ifba-ai.desktop /usr/lib/python3/dist-packages/ifba_ai/ui.py /usr/share/applications/suap-ifba.desktop /usr/share/applications/ava-ifba.desktop /usr/local/bin/ifba-os-plasma-session-setup /etc/NetworkManager/system-connections/ifba-wired.nmconnection; do
  test -s "$ROOTFS$file"
done
cmp -s /work/packaging/plasma/ifba-os/metadata.json "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/metadata.json"
cmp -s /work/packaging/plasma/ifba-os/contents/defaults "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/contents/defaults"
cmp -s /work/packaging/plasma/ifba-os/contents/layouts/org.kde.plasma.desktop-layout.js "$ROOTFS/usr/share/plasma/look-and-feel/org.ifbaos.desktop/contents/layouts/org.kde.plasma.desktop-layout.js"
test -x "$ROOTFS/usr/bin/plasma-apply-wallpaperimage"
test -x "$ROOTFS/usr/local/bin/ifba-os-version"
for package in plasma-workspace plasma-desktop plasma-session-wayland plasma-session-x11 kwin-x11 sddm dolphin konsole plasma-discover systemsettings; do
  chroot "$ROOTFS" dpkg-query -s "$package" | grep -q 'Status: install ok installed'
done
test -L "$ROOTFS/etc/systemd/system/default.target"
test "$(readlink "$ROOTFS/etc/systemd/system/default.target")" = /lib/systemd/system/graphical.target
test -L "$ROOTFS/etc/systemd/system/display-manager.service"
test "$(readlink "$ROOTFS/etc/systemd/system/display-manager.service")" = /lib/systemd/system/sddm.service
test -L "$ROOTFS/etc/systemd/system/multi-user.target.wants/NetworkManager.service"
chroot "$ROOTFS" dpkg-query -W plasma-workspace libqt6core6t64 kwin-wayland kwin-x11 sddm
cp -L "$ROOTFS/boot/vmlinuz" "$ISO/casper/vmlinuz"
cp -L "$ROOTFS/boot/initrd.img" "$ISO/casper/initrd"
mksquashfs "$ROOTFS" "$ISO/casper/filesystem.squashfs" -comp xz -b 1M -processors "$(nproc)" -e boot
du -sx --block-size=1 "$ROOTFS" | cut -f1 > "$ISO/casper/filesystem.size"
cat > "$ISO/boot/grub/grub.cfg" <<'GRUB'
set timeout=5
set default=0
menuentry "IFBA OS prototype (live)" {
  linux /casper/vmlinuz boot=casper splash ---
  initrd /casper/initrd
}
GRUB
grub-mkrescue -volid IFBA_OS_26_04 -o "$OUT" "$ISO"
