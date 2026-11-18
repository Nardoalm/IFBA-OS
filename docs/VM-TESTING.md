# Virtual machine test checklist

Use a disposable QEMU/UTM/VirtualBox VM with 4 GB RAM, 2 CPUs, and 30 GB virtual disk. Attach the generated ISO as a virtual CD and select live boot. Keep networking in NAT mode; do not mount host directories or pass through personal credentials.

Check that the live desktop boots, the wallpaper renders, the welcome-page shortcut opens, SUAP and AVA links target the official HTTPS domains, package choices are optional, and shutdown/reboot work. This prototype does not install to disk, create institutional accounts, connect to the AI API, or integrate academic data. Record failures and the VM configuration before changing build settings.

## Validation record — 2026-11-18

### VM result

- UTM is installed. The build with SHA-256 `9002e2f38530c1a99da7beb6475d9f62aa4f77d2efe1e43f52ee543c222f8418` reached XFCE and showed the welcome page, supplied wallpaper, and bottom panel. Its SUAP and AVA PNGs appeared as broken images. The final build with re-encoded JPEG portal marks reached GRUB and showed Casper console messages, but a usable desktop was not verified during that run. Do not treat the earlier build as proof that the final ISO works.
- The previous terminal-only failure was explained by the built root filesystem: `startxfce4` was present, but `xinit` and the Xorg server were missing. `--no-install-recommends` had omitted them. The build now explicitly installs `xserver-xorg`, `xinit`, and `lightdm-gtk-greeter`, and pins the LightDM XFCE session and greeter.
- In the booted prior build, the exact user-supplied wallpaper appeared behind the welcome page and the native bottom panel was visible. The final build's wallpaper and panel still need confirmation.
- The updated welcome page and both re-encoded portal logos were visually inspected in the host Electron preview. The final guest shortcut and JPEG logos were not verified. The Whisker menu was visible on the earlier build but could not be opened in the guest; the Super/Windows-key shortcut, SUAP/AVA links, networking, shutdown, and reboot remain unverified.
- Guest networking and `apt update` were not verified; the exact guest error was not captured. The build now removes the container-specific systemd-resolved stub file before creating the SquashFS, because the old rootfs stub contained the Docker host resolver address. This addresses a concrete image contamination risk, but NAT/DNS still needs a guest check.
- Casper printed a missing `/usr/bin/plymouth` message during boot. The `plymouth` package is included in the rootfs, but this console message still appears and needs investigation. Shutdown and reboot remain unchecked. SUAP/AVA were not opened and no account or credentials were entered.

### Offline image/build checks

- Current ISO: `output/ifba-os-ubuntu-24.04-amd64.iso`; SHA-256: `17e9f8b8c6fafb3b77d20822ec36e229558da48cb36cff9c9963b63646723b72`. It is an ISO 9660 image with boot metadata and volume label `IFBA_OS_24_04`. The SquashFS build cache confirms Plymouth, the Whisker plugin, Electron, the wallpaper, the original PNGs, and their re-encoded JPEG display copies are present. The final ISO has not been confirmed to boot to its desktop.
- Previous image metadata checks identified an ISO 9660 image with boot metadata and volume label `IFBA_OS_24_04`; the embedded SquashFS contained NetSurf, the welcome-page HTML, launcher, and wallpaper files.
- The welcome page links only to `https://suap.ifba.edu.br/` and `https://ava.ifba.edu.br/`. Neither service was opened or logged into.
- Host preview: updated Electron UI rendered the supplied wallpaper with its embedded wordmark, the top-left identity and greeting, separate app/activity columns, the SUAP/AVA marks, assistant orb, and honest empty state. The activities block was shifted to leave the central wallpaper mark visible. The host preview does not contain XFCE's native hotbar.
- `node --check` for the app, `bash -n scripts/build-iso.sh scripts/build-iso-container.sh`, XML parsing of XFCE configs, `npm audit --prefix app`, `git diff --check`, and a full ISO rebuild succeeded. The earlier boot confirmed XFCE and the page; the final ISO is awaiting a successful graphical boot.

### Remaining VM checklist

- [ ] Boot the final ISO to an actual desktop and check the Casper Plymouth warning.
- [ ] Confirm that the XFCE bottom panel, IFBA Whisker menu, and Super/Windows-key shortcut appear and work.
- [ ] Confirm the JPEG SUAP/AVA marks load in the guest and the wallpaper remains clear behind the activities panel.
- [ ] Open “Primeiros passos do IFBA OS”; inspect CSS, icon images, and layout.
- [ ] Confirm SUAP/AVA links target their expected HTTPS domains without signing in.
- [ ] Verify NAT networking and DNS from inside the guest.
- [ ] Check display legibility at a common VM resolution, then shutdown and reboot.

Keep the VM disposable: 4 GB RAM, 2 CPUs, 30 GB virtual disk, NAT, no shared host folders, and no credentials. Select the live boot entry only; do not run an installer.
