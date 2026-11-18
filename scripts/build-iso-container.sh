#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
ROOTFS=/var/cache/ifba-rootfs/rootfs
ISO=/tmp/ifba-iso
OUT=/work/output/ifba-os-ubuntu-24.04-amd64.iso

apt-get update
apt-get install -y --no-install-recommends \
  debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin mtools

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
cleanup_mounts() {
  umount -R "$ROOTFS/dev" 2>/dev/null || true
  umount "$ROOTFS/proc" 2>/dev/null || true
  umount -R "$ROOTFS/sys" 2>/dev/null || true
}
trap cleanup_mounts EXIT
cp /etc/resolv.conf "$ROOTFS/etc/resolv.conf"

chroot "$ROOTFS" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get update
chroot "$ROOTFS" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  linux-image-generic casper systemd-sysv xfce4 lightdm network-manager \
  netsurf-gtk sudo dbus-x11 policykit-1

chroot "$ROOTFS" /bin/bash -euxc '
  id ubuntu >/dev/null 2>&1 || useradd -m -s /bin/bash -G sudo ubuntu
  passwd -d ubuntu
  mkdir -p /etc/lightdm/lightdm.conf.d /usr/share/backgrounds/ifba-os
  printf "[Seat:*]\nautologin-user=ubuntu\nautologin-user-timeout=0\n" > /etc/lightdm/lightdm.conf.d/50-ifba-autologin.conf
  apt-get clean
  rm -rf /var/lib/apt/lists/* /tmp/*
'

rm -rf "$ISO"
mkdir -p "$ISO/casper" "$ISO/boot/grub"
cp "$ROOTFS/boot/vmlinuz-"* "$ISO/casper/vmlinuz"
cp "$ROOTFS/boot/initrd.img-"* "$ISO/casper/initrd"
cp /work/assets/wallpapers/ifba-os-graphite.png "$ROOTFS/usr/share/backgrounds/ifba-os/wallpaper.png"
mkdir -p \
  "$ROOTFS/usr/share/ifba-os/app" \
  "$ROOTFS/usr/share/ifba-os/assets" \
  "$ROOTFS/usr/share/ifba-os/assets/wallpapers" \
  "$ROOTFS/home/ubuntu/Desktop" \
  "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml"
cp -R /work/app/. "$ROOTFS/usr/share/ifba-os/app/"
cp -R /work/assets/icons "$ROOTFS/usr/share/ifba-os/assets/"
cp /work/assets/wallpapers/ifba-os-graphite.png "$ROOTFS/usr/share/ifba-os/assets/wallpapers/"
cp /work/packaging/ifba-os-welcome.desktop "$ROOTFS/home/ubuntu/Desktop/IFBA-OS-Welcome.desktop"
cp /work/packaging/xfce4-desktop.xml "$ROOTFS/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml"
chroot "$ROOTFS" chown -R ubuntu:ubuntu /home/ubuntu/Desktop /home/ubuntu/.config
chmod +x "$ROOTFS/home/ubuntu/Desktop/IFBA-OS-Welcome.desktop"
cleanup_mounts

mksquashfs "$ROOTFS" "$ISO/casper/filesystem.squashfs" -comp xz -b 1M -e boot
du -sx --block-size=1 "$ROOTFS" | cut -f1 > "$ISO/casper/filesystem.size"
cat > "$ISO/boot/grub/grub.cfg" <<'GRUB'
set timeout=5
set default=0
menuentry "IFBA OS prototype (live)" {
  linux /casper/vmlinuz boot=casper quiet splash ---
  initrd /casper/initrd
}
GRUB
grub-mkrescue -volid IFBA_OS_24_04 -o "$OUT" "$ISO"
