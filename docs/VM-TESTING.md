# Virtual machine test checklist

Use a disposable QEMU/UTM/VirtualBox VM with 4 GB RAM, 2 CPUs, and 30 GB virtual disk. Attach the generated ISO as a virtual CD and select live boot. Keep networking in NAT mode; do not mount host directories or pass through personal credentials.

Check that the live desktop boots, the wallpaper renders, the welcome-page shortcut opens, SUAP and AVA links target the official HTTPS domains, package choices are optional, and shutdown/reboot work. This prototype does not install to disk, create institutional accounts, connect to the AI API, or integrate academic data. Record failures and the VM configuration before changing build settings.

## Validation record — 2026-11-18

### VM result

- UTM is installed; the existing VM named `Linux` booted the current IFBA OS ISO into an XFCE desktop as the `ubuntu` live user. This confirms the boot menu, kernel/live startup, LightDM autologin, and graphical session now work. The desktop panel, Home icon, and “Primeiros passos do I...” desktop shortcut were visible.
- The previous terminal-only failure was explained by the built root filesystem: `startxfce4` was present, but `xinit` and the Xorg server were missing. `--no-install-recommends` had omitted them. The build now explicitly installs `xserver-xorg`, `xinit`, and `lightdm-gtk-greeter`, and pins the LightDM XFCE session and greeter.
- The wallpaper did **not** render in the observed desktop; it showed the default solid background. The build now provides the XFCE wallpaper channel both as the live user's configuration and as the system XDG default. This latest adjustment still needs a fresh boot confirmation.
- The shortcut was visible but could not be opened in this run. A CUA click failed at the UTM window boundary, so the local welcome page, its CSS/assets, and SUAP/AVA links were not verified in the guest.
- Guest networking and `apt update` were not verified; the exact guest error was not captured. The build now removes the container-specific systemd-resolved stub file before creating the SquashFS, because the old rootfs stub contained the Docker host resolver address. This addresses a concrete image contamination risk, but NAT/DNS still needs a guest check.
- Shutdown and reboot were not checked. The wallpaper, launcher, network, and power checks remain open; SUAP/AVA were not opened and no account or credentials were entered.

### Offline image/build checks

- Current ISO: `output/ifba-os-ubuntu-24.04-amd64.iso`; SHA-256: `510ebd2499a7bcfcef93d249fde36bae66ef803247503d81a1009746e6b9f6b5`. The image was rebuilt after adding the system XDG wallpaper default, but that change has not yet been confirmed by a fresh VM boot.
- Previous image metadata checks identified an ISO 9660 image with boot metadata and volume label `IFBA_OS_24_04`; the embedded SquashFS contained NetSurf, the welcome-page HTML, launcher, and wallpaper files.
- The welcome page links only to `https://suap.ifba.edu.br/` and `https://ava.ifba.edu.br/`. Neither service was opened or logged into.
- `node --check app/renderer.js`, `bash -n scripts/build-iso.sh scripts/build-iso-container.sh`, `git diff --check`, and the complete ISO rebuild succeeded after the wallpaper-default adjustment. `file` identifies the result as a bootable ISO 9660 image with volume label `IFBA_OS_24_04`.

### Remaining VM checklist

- [ ] Boot the rebuilt ISO again and confirm the wallpaper is visible.
- [ ] Open “Primeiros passos do IFBA OS”; inspect CSS, icon images, and layout.
- [ ] Confirm SUAP/AVA links target their expected HTTPS domains without signing in.
- [ ] Verify NAT networking and DNS from inside the guest.
- [ ] Check display legibility at a common VM resolution, then shutdown and reboot.

Keep the VM disposable: 4 GB RAM, 2 CPUs, 30 GB virtual disk, NAT, no shared host folders, and no credentials. Select the live boot entry only; do not run an installer.
