#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/output/ifba-os-ubuntu-24.04-amd64.iso"
mkdir -p "$ROOT/output"
docker run --rm --privileged --platform linux/amd64 \
  -v "$ROOT:/work" -w /work \
  ubuntu:24.04 bash -lc '
    set -euo pipefail
    export DEBIAN_FRONTEND=noninteractive
    apt-get update && apt-get install -y --no-install-recommends debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin mtools
    ROOTFS=/tmp/ifba-rootfs
    ISO=/tmp/ifba-iso
    debootstrap --arch=amd64 noble "$ROOTFS" http://archive.ubuntu.com/ubuntu
    mount --bind /dev "$ROOTFS/dev"
    mount -t proc proc "$ROOTFS/proc"
    mount --rbind /sys "$ROOTFS/sys"
    cp /etc/resolv.conf "$ROOTFS/etc/resolv.conf"
    chroot "$ROOTFS" /bin/bash -euxc "
      export DEBIAN_FRONTEND=noninteractive
      apt-get update
      apt-get install -y --no-install-recommends linux-image-generic casper systemd-sysv xfce4 lightdm network-manager firefox sudo dbus-x11 policykit-1
      useradd -m -s /bin/bash -G sudo ubuntu
      passwd -d ubuntu
      mkdir -p /usr/share/backgrounds/ifba-os
      printf '[Seat:*]\\nautologin-user=ubuntu\\nautologin-user-timeout=0\\n' > /etc/lightdm/lightdm.conf.d/50-ifba-autologin.conf
      update-initramfs -u -k all
      apt-get clean
      rm -rf /var/lib/apt/lists/* /tmp/*
    "
    mkdir -p "$ISO/casper" "$ISO/boot/grub"
    cp "$ROOTFS/boot/vmlinuz-"* "$ISO/casper/vmlinuz"
    cp "$ROOTFS/boot/initrd.img-"* "$ISO/casper/initrd"
    cp /work/assets/wallpapers/ifba-os-graphite.png "$ROOTFS/usr/share/backgrounds/ifba-os/wallpaper.png"
    mksquashfs "$ROOTFS" "$ISO/casper/filesystem.squashfs" -comp xz -b 1M -e boot
    du -sx --block-size=1 "$ROOTFS" | cut -f1 > "$ISO/casper/filesystem.size"
    cat > "$ISO/boot/grub/grub.cfg" <<EOF
set timeout=5
set default=0
menuentry "IFBA OS prototype (live)" {
  linux /casper/vmlinuz boot=casper quiet splash ---
  initrd /casper/initrd
}
EOF
    grub-mkrescue -o /work/output/ifba-os-ubuntu-24.04-amd64.iso "$ISO"
    umount -R "$ROOTFS/dev" || true
    umount "$ROOTFS/proc" || true
    umount -R "$ROOTFS/sys" || true
  '
printf 'Created %s\n' "$OUT"
