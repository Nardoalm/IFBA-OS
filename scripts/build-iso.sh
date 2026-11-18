#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/output/ifba-os-ubuntu-24.04-amd64.iso"
mkdir -p "$ROOT/output"
docker run --rm --platform linux/amd64 \
  -v "$ROOT:/work" -w /work \
  ubuntu:24.04 bash -lc '
    set -euo pipefail
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y --no-install-recommends live-build xorriso squashfs-tools
    mkdir -p /tmp/ifba-live && cd /tmp/ifba-live
    lb config --distribution noble --architectures amd64 \
      --binary-images iso-hybrid --archive-areas "main universe multiverse" \
      --debian-installer false --bootappend-live "boot=live components quiet splash" \
      --iso-application "IFBA OS prototype" --iso-volume "IFBA_OS_0_1"
    mkdir -p config/package-lists config/includes.chroot/usr/share/backgrounds/ifba-os
    printf "xfce4\nlightdm\nfirefox\nnetwork-manager\nsudo\n" > config/package-lists/ifba.list.chroot
    cp /work/assets/wallpapers/ifba-os-graphite.png config/includes.chroot/usr/share/backgrounds/ifba-os/wallpaper.png
    lb build
    cp live-image-amd64.hybrid.iso /work/output/ifba-os-ubuntu-24.04-amd64.iso
  '
printf 'Created %s\n' "$OUT"
