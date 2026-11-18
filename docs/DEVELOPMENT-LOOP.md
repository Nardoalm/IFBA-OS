# Development loop record

## Iteration 1 — 2026-11-18

- **Objective:** Inspect the current repo/ISO, attempt UTM VM boot, and improve a safe independent user-facing feature.
- **Initial state:** Clean `development` branch at `2d1462a`; `d15856b` is an ancestor. The existing ISO booted into a terminal instead of a desktop.
- **Diagnosis and implementation:** Inspection of the built package database confirmed XFCE components and `startxfce4` were present but Xorg and `xinit` were absent because the image uses `--no-install-recommends`. Added `xserver-xorg`, `xinit`, and the GTK greeter, and set LightDM's session/greeter explicitly. The VM then reached the XFCE desktop. The rootfs systemd-resolved stub also contained the Docker host resolver; the build now bind-mounts the container resolver only while installing packages and removes the container-specific stub before packaging. The welcome page now describes the app catalogue as saved local choices, not real installs; it saves only eligible app IDs per browser user and gives explicit save/skip feedback. Removed the Plymouth splash request after earlier console output reported missing Plymouth commands.
- **Follow-up:** The booted desktop rendered XFCE's solid default background instead of the IFBA wallpaper. The build now writes the wallpaper channel as both the live user's config and the system XDG default; this adjustment needs another VM boot to verify. The welcome shortcut was visible but not opened because the UTM click failed at the app window boundary.
- **Files:** `app/index.html`, `app/renderer.js`, `scripts/build-iso-container.sh`, `docs/PROJECT-ROADMAP.md`, `docs/DEVELOPMENT-LOOP.md`, `docs/VM-TESTING.md`.
- **Checks/build:** `node --check app/renderer.js`, `bash -n scripts/build-iso.sh scripts/build-iso-container.sh`, `git diff --check`, and a full ISO rebuild succeeded after adding the wallpaper channel as a system XDG default. The current ISO SHA-256 is `510ebd2499a7bcfcef93d249fde36bae66ef803247503d81a1009746e6b9f6b5`; `file` identifies it as a bootable ISO 9660 image.
- **VM results:** UTM displayed the XFCE desktop, top panel, Home icon, and welcome shortcut. The desktop wallpaper was not visible. Launcher behavior, page styles/images, SUAP/AVA target URLs in the guest, guest NAT/DNS, shutdown, and reboot remain unverified. No SUAP/AVA login or AI credentials were used.
- **Commit:** Recorded in the repository history after validation.
- **Next priority:** Boot the current image once more to confirm its wallpaper default, then complete the remaining checklist in `docs/VM-TESTING.md`.
