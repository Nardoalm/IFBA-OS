#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
ROOTFS=/var/cache/ifba-rootfs/rootfs
ISO=/tmp/ifba-iso
OUT=/work/output/ifba-os-ubuntu-24.04-amd64.iso

apt-get update
apt-get install -y --no-install-recommends \
  debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin mtools curl gnupg ca-certificates

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

# Use Mozilla's maintained DEB build instead of Ubuntu Noble's Firefox-to-Snap
# transition package, which is unsuitable for this snap-free live rootfs.
curl --fail --silent --show-error --location \
  https://packages.mozilla.org/apt/repo-signing-key.gpg \
  --output /tmp/mozilla-archive-keyring.asc
gpg --show-keys --with-colons /tmp/mozilla-archive-keyring.asc | \
  awk -F: '$1 == "fpr" { print $10; exit }' | \
  grep --quiet '^35BAA0B33E9EB396F59CA838C0BA5CE6DC6315A3$'
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
  linux-image-generic casper plymouth plymouth-themes systemd-sysv xfce4 lightdm lightdm-gtk-greeter \
  xserver-xorg xinit network-manager network-manager-gnome xdg-utils \
  yaru-theme-gtk yaru-theme-icon fonts-inter \
  xfce4-power-manager xfce4-pulseaudio-plugin xfce4-whiskermenu-plugin xfce4-genmon-plugin \
  xfce4-terminal thunar xfce4-appfinder xfce4-settings xfce4-notifyd \
  python3-dbus python3-gi gir1.2-gtk-3.0 gnome-keyring libpam-gnome-keyring libsecret-tools \
  python3-xlib python3-pyatspi at-spi2-core gir1.2-atspi-2.0 \
  libnss3 libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 libasound2t64 \
  libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libdrm2 \
  libxkbcommon0 libpango-1.0-0 \
  firefox firefox-l10n-pt-br sudo dbus-x11 policykit-1 qemu-guest-agent locales

# The build cache persists between runs, so remove NetSurf left by older images.
if chroot "$ROOTFS" dpkg-query -W -f='${Status}' netsurf-gtk 2>/dev/null | grep -q 'install ok installed'; then
  chroot "$ROOTFS" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get remove -y netsurf-gtk
fi

# The root filesystem is cached between builds; remove the older fullscreen dashboard.
rm -f "$ROOTFS/etc/xdg/autostart/ifba-os-welcome.desktop" \
  "$ROOTFS/home/ubuntu/Desktop/IFBA-OS-Welcome.desktop" \
  "$ROOTFS/etc/skel/Desktop/IFBA-OS-Welcome.desktop" \
  "$ROOTFS/usr/share/applications/ifba-os-welcome.desktop" \
  "$ROOTFS/home/ubuntu/.config/autostart/ifba-os-welcome.desktop" \
  "$ROOTFS/usr/bin/ifba-os-welcome"
rm -rf "$ROOTFS/usr/share/ifba-os/app" "$ROOTFS/usr/lib/ifba-os/electron"

chroot "$ROOTFS" /bin/bash -euxc '
  id ubuntu >/dev/null 2>&1 || useradd -m -s /bin/bash -G sudo ubuntu
  passwd -d ubuntu
  mkdir -p /var/crash /etc/lightdm/lightdm.conf.d /usr/share/backgrounds/ifba-os \
    /usr/share/xfce4/helpers /usr/share/icons/hicolor/128x128/apps \
    /usr/lib/ifba-os /usr/local/bin /etc/xdg/autostart \
    /etc/xdg/xfce4/xfconf/xfce-perchannel-xml /etc/xdg/xfce4/panel \
    /etc/xdg/xfce4 /etc/skel/Desktop /etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml \
    /etc/skel/.config/autostart \
    /etc/skel/.config/ifba-ai /etc/skel/.local/share/ifba-ai /etc/skel/.cache/ifba-ai \
    /etc/skel/.config/gtk-3.0 /etc/gtk-3.0
  printf "[Seat:*]\nuser-session=xfce\ngreeter-session=lightdm-gtk-greeter\nautologin-user=ubuntu\nautologin-user-timeout=0\n" > /etc/lightdm/lightdm.conf.d/50-ifba-autologin.conf
  printf "[greeter]\nbackground=/usr/share/backgrounds/ifba-os/wallpaper.png\ntheme-name=Yaru-dark\nicon-theme-name=Yaru\nfont-name=Inter 10\n" > /etc/lightdm/lightdm-gtk-greeter.conf
  # debootstrap defaults to multi-user.target; start LightDM and XFCE in the live image.
  ln -sfn /lib/systemd/system/graphical.target /etc/systemd/system/default.target
  printf "LANG=pt_BR.UTF-8\nLANGUAGE=pt_BR:pt:en\n" > /etc/default/locale
  printf "pt_BR.UTF-8 UTF-8\n" > /etc/locale.gen
  locale-gen pt_BR.UTF-8
  printf "America/Bahia\n" > /etc/timezone
  ln -sfn /usr/share/zoneinfo/America/Bahia /etc/localtime
  update-alternatives --install /usr/bin/x-www-browser x-www-browser /usr/bin/firefox 100
  apt-get clean
    rm -rf /var/lib/apt/lists/* /tmp/*
'

mkdir -p "$ROOTFS/etc/systemd/system/multi-user.target.wants"
ln -sfn /lib/systemd/system/qemu-guest-agent.service \
  "$ROOTFS/etc/systemd/system/multi-user.target.wants/qemu-guest-agent.service"
mkdir -p "$ROOTFS/etc/NetworkManager/system-connections"
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

rm -rf "$ISO"
mkdir -p "$ISO/casper" "$ISO/boot/grub"
cp "$ROOTFS/boot/vmlinuz-"* "$ISO/casper/vmlinuz"
cp "$ROOTFS/boot/initrd.img-"* "$ISO/casper/initrd"
cp /work/assets/wallpapers/ifba-os-desktop.png "$ROOTFS/usr/share/backgrounds/ifba-os/wallpaper.png"
mkdir -p \
  "$ROOTFS/usr/share/plymouth/themes/ifba-os" \
  "$ROOTFS/usr/share/ifba-os/assets" \
  "$ROOTFS/usr/share/ifba-os/assets/wallpapers" \
  "$ROOTFS/etc/xdg/xfce4/xfconf/xfce-perchannel-xml" \
  "$ROOTFS/etc/xdg/xfce4/panel" \
  "$ROOTFS/etc/xdg/xfce4" \
  "$ROOTFS/etc/xdg/autostart" \
  "$ROOTFS/usr/share/xfce4/helpers" \
  "$ROOTFS/usr/share/icons/hicolor/128x128/apps" \
  "$ROOTFS/usr/lib/ifba-os" \
  "$ROOTFS/usr/local/bin" \
  "$ROOTFS/home/ubuntu/Desktop" \
  "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml" \
  "$ROOTFS/home/ubuntu/.config/xfce4" \
  "$ROOTFS/home/ubuntu/.config/xfce4/panel" \
  "$ROOTFS/home/ubuntu/.config/autostart" \
  "$ROOTFS/etc/skel/.config/xfce4/panel" \
  "$ROOTFS/home/ubuntu/.config/gtk-3.0" \
  "$ROOTFS/home/ubuntu/.config" \
  "$ROOTFS/home/ubuntu/.config/ifba-ai" \
  "$ROOTFS/home/ubuntu/.local/share/ifba-ai" \
  "$ROOTFS/home/ubuntu/.cache/ifba-ai" \
  "$ROOTFS/etc/skel/.local/share/ifba-ai" \
  "$ROOTFS/etc/skel/.cache/ifba-ai" \
  "$ROOTFS/usr/lib/systemd/user/default.target.wants" \
  "$ROOTFS/usr/share/dbus-1/services" \
  "$ROOTFS/usr/lib/python3/dist-packages"
cp /work/assets/plymouth/ifba-os-startup.png "$ROOTFS/usr/share/plymouth/themes/ifba-os/ifba-os-startup.png"
cp /work/packaging/plymouth/ifba-os.plymouth "$ROOTFS/usr/share/plymouth/themes/ifba-os/ifba-os.plymouth"
cp /work/packaging/plymouth/ifba-os.script "$ROOTFS/usr/share/plymouth/themes/ifba-os/ifba-os.script"
cp -R /work/ai/ifba_ai "$ROOTFS/usr/lib/python3/dist-packages/"
cp /work/packaging/ifba-ai-ui "$ROOTFS/usr/bin/ifba-ai-ui"
cp /work/packaging/ifba-ai-daemon "$ROOTFS/usr/bin/ifba-ai-daemon"
chmod 0755 "$ROOTFS/usr/bin/ifba-ai-ui" "$ROOTFS/usr/bin/ifba-ai-daemon"
cp /work/packaging/ifba-ai.desktop "$ROOTFS/usr/share/applications/ifba-ai.desktop"
cp /work/packaging/ifba-ai.css "$ROOTFS/usr/share/ifba-os/ifba-ai.css"
cp /work/packaging/org.ifba.OS.AI.service "$ROOTFS/usr/share/dbus-1/services/org.ifba.OS.AI.service"
cp /work/packaging/ifba-ai.service "$ROOTFS/usr/lib/systemd/user/ifba-ai.service"
ln -sfn ../ifba-ai.service "$ROOTFS/usr/lib/systemd/user/default.target.wants/ifba-ai.service"
chmod 0700 "$ROOTFS/home/ubuntu/.config/ifba-ai" "$ROOTFS/home/ubuntu/.local/share/ifba-ai" \
  "$ROOTFS/home/ubuntu/.cache/ifba-ai" "$ROOTFS/etc/skel/.config/ifba-ai" \
  "$ROOTFS/etc/skel/.local/share/ifba-ai" "$ROOTFS/etc/skel/.cache/ifba-ai"
cp -R /work/assets/icons "$ROOTFS/usr/share/ifba-os/assets/"
cp /work/assets/wallpapers/ifba-os-desktop.png "$ROOTFS/usr/share/ifba-os/assets/wallpapers/"
cp /work/packaging/firefox.desktop "$ROOTFS/usr/share/applications/firefox.desktop"
cp /work/packaging/suap-ifba.desktop "$ROOTFS/usr/share/applications/suap-ifba.desktop"
cp /work/packaging/ava-ifba.desktop "$ROOTFS/usr/share/applications/ava-ifba.desktop"
cp /work/packaging/suap-ifba-link.desktop "$ROOTFS/home/ubuntu/Desktop/SUAP.desktop"
cp /work/packaging/ava-ifba-link.desktop "$ROOTFS/home/ubuntu/Desktop/AVA-IFBA.desktop"
cp /work/packaging/suap-ifba-link.desktop "$ROOTFS/etc/skel/Desktop/SUAP.desktop"
cp /work/packaging/ava-ifba-link.desktop "$ROOTFS/etc/skel/Desktop/AVA-IFBA.desktop"
cp /work/packaging/xfce4-desktop.xml "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml"
cp /work/packaging/xfce4-desktop.xml "$ROOTFS/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml"
cp /work/packaging/xfce4-desktop.xml "$ROOTFS/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml"
cp /work/packaging/xfce4-panel.xml "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml"
cp /work/packaging/xfce4-panel.xml "$ROOTFS/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml"
cp /work/packaging/xfce4-panel.xml "$ROOTFS/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml"
cp /work/packaging/xfce4-panel.xml "$ROOTFS/etc/xdg/xfce4/panel/default.xml"
cat > "$ROOTFS/home/ubuntu/.config/xfce4/panel/genmon-13.rc" <<'GENMON'
Command=/usr/lib/ifba-os/ifba-os-greeting.sh
UseLabel=0
UpdatePeriod=60000
GENMON
cp "$ROOTFS/home/ubuntu/.config/xfce4/panel/genmon-13.rc" "$ROOTFS/etc/skel/.config/xfce4/panel/genmon-13.rc"
cp /work/packaging/xfce4-keyboard-shortcuts.xml "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-keyboard-shortcuts.xml"
cp /work/packaging/xfce4-keyboard-shortcuts.xml "$ROOTFS/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-keyboard-shortcuts.xml"
cp /work/packaging/xfce4-xsettings.xml "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml"
cp /work/packaging/xfce4-xsettings.xml "$ROOTFS/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml"
cp /work/packaging/xfce4-xsettings.xml "$ROOTFS/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml"
cp /work/packaging/xfwm4.xml "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml"
cp /work/packaging/xfwm4.xml "$ROOTFS/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml"
cp /work/packaging/xfwm4.xml "$ROOTFS/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml"
cp /work/packaging/gtk.css "$ROOTFS/etc/gtk-3.0/gtk.css"
cp /work/packaging/gtk.css "$ROOTFS/home/ubuntu/.config/gtk-3.0/gtk.css"
cp /work/packaging/gtk.css "$ROOTFS/etc/skel/.config/gtk-3.0/gtk.css"
cp /work/packaging/ifba-os-greeting.sh "$ROOTFS/usr/lib/ifba-os/ifba-os-greeting.sh"
chmod +x "$ROOTFS/usr/lib/ifba-os/ifba-os-greeting.sh"
cp /work/packaging/ifba-os-session-setup.sh "$ROOTFS/usr/local/bin/ifba-os-session-setup"
chmod 0755 "$ROOTFS/usr/local/bin/ifba-os-session-setup"
cp /work/packaging/xfce4-firefox-helper.desktop "$ROOTFS/usr/share/xfce4/helpers/firefox.desktop"
cp /work/packaging/xfce4-helpers.rc "$ROOTFS/etc/xdg/xfce4/helpers.rc"
cp /work/packaging/xfce4-helpers.rc "$ROOTFS/home/ubuntu/.config/xfce4/helpers.rc"
cp /work/assets/icons/ifba-mark-placeholder.png "$ROOTFS/usr/share/icons/hicolor/128x128/apps/ifba-os-menu.png"
chroot "$ROOTFS" gtk-update-icon-cache -f /usr/share/icons/hicolor
cat > "$ROOTFS/usr/share/ifba-os/mimeapps.list" <<'MIME'
[Default Applications]
x-scheme-handler/http=firefox.desktop
x-scheme-handler/https=firefox.desktop
text/html=firefox.desktop
application/xhtml+xml=firefox.desktop
MIME
cp "$ROOTFS/usr/share/ifba-os/mimeapps.list" "$ROOTFS/etc/xdg/mimeapps.list"
cp "$ROOTFS/usr/share/ifba-os/mimeapps.list" "$ROOTFS/home/ubuntu/.config/mimeapps.list"
cat > "$ROOTFS/etc/xdg/autostart/ifba-network-indicator.desktop" <<'NETWORK'
[Desktop Entry]
Type=Application
Name=IFBA OS Network Indicator
Exec=nm-applet
OnlyShowIn=XFCE;
Terminal=false
NETWORK
cat > "$ROOTFS/etc/xdg/autostart/ifba-os-session-setup.desktop" <<'SESSION'
[Desktop Entry]
Type=Application
Name=IFBA OS Session Setup
Comment=Apply desktop defaults for the active display
Exec=/usr/local/bin/ifba-os-session-setup
OnlyShowIn=XFCE;
Terminal=false
StartupNotify=false
SESSION
cp "$ROOTFS/etc/xdg/autostart/ifba-os-session-setup.desktop" \
  "$ROOTFS/home/ubuntu/.config/autostart/ifba-os-session-setup.desktop"
cp "$ROOTFS/etc/xdg/autostart/ifba-os-session-setup.desktop" \
  "$ROOTFS/etc/skel/.config/autostart/ifba-os-session-setup.desktop"
chroot "$ROOTFS" chown -R ubuntu:ubuntu /home/ubuntu
chmod 0700 "$ROOTFS/home/ubuntu/.cache" "$ROOTFS/home/ubuntu/.local"
chmod +x "$ROOTFS/home/ubuntu/Desktop/SUAP.desktop" "$ROOTFS/home/ubuntu/Desktop/AVA-IFBA.desktop"
chroot "$ROOTFS" update-alternatives --install \
  /usr/share/plymouth/themes/default.plymouth default.plymouth \
  /usr/share/plymouth/themes/ifba-os/ifba-os.plymouth 120
chroot "$ROOTFS" update-alternatives --set default.plymouth \
  /usr/share/plymouth/themes/ifba-os/ifba-os.plymouth
chroot "$ROOTFS" update-initramfs -u -k all
cp "$ROOTFS/boot/initrd.img-"* "$ISO/casper/initrd"
cleanup_mounts
rm -f "$RESOLV_TARGET"

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
grub-mkrescue -volid IFBA_OS_24_04 -o "$OUT" "$ISO"
