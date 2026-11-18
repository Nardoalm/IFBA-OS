# Virtual machine test checklist

Use a disposable QEMU/UTM/VirtualBox VM with 4 GB RAM, 2 CPUs, and 30 GB virtual disk. Attach the generated ISO as a virtual CD and select live boot. Keep networking in NAT mode; do not mount host directories or pass through personal credentials.

Check that the live desktop boots, the wallpaper renders, the welcome-page shortcut opens, SUAP and AVA links target the official HTTPS domains, package choices are optional, and shutdown/reboot work. This prototype does not install to disk, create institutional accounts, connect to the AI API, or integrate academic data. Record failures and the VM configuration before changing build settings.

## Validation record — 2026-11-18

The live desktop has not yet been booted in a VM. No QEMU, UTM, or VirtualBox executable or application was found on the build host, so desktop rendering, launcher interaction, networking, shutdown, and reboot remain unverified. Do not treat the checks below as a successful VM boot.

Offline image checks completed:

- The ISO is present at `output/ifba-os-ubuntu-24.04-amd64.iso` and its SHA-256 is `319871f316f3cdc10c877b8a7bf127533f29ac600b151d29dd32c56f5ede149b`.
- `file` identifies an ISO 9660 image with boot metadata and volume label `IFBA_OS_24_04`; `xorriso` reads the image and lists the Casper kernel, initrd, filesystem size, and SquashFS.
- The embedded SquashFS listing contains NetSurf, the welcome-page HTML, the desktop launcher, and both wallpaper copies.
- The welcome-page source links only to `https://suap.ifba.edu.br/` and `https://ava.ifba.edu.br/`; neither service was opened or logged into during validation.
- `bash -n scripts/build-iso.sh scripts/build-iso-container.sh` completed successfully.

Next action when a VM application is available: use the checklist above with 4 GB RAM, 2 CPUs, a 30 GB virtual disk, NAT networking, and no host-shared folders or personal credentials. Attach the ISO as a virtual CD and choose its live boot entry; do not run an installer.
