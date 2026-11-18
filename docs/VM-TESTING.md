# Virtual machine test checklist

Use a disposable UTM/QEMU/VirtualBox VM with 4 GB RAM, 2 CPUs, a 30 GB virtual disk, and NAT networking. Do not mount host folders or pass through personal credentials. Select the live boot entry only; this ISO is not an installer.

## Validation record — 2026-11-18

### UTM run

- The existing UTM `Linux` VM is x86_64/Q35 with 4 GB RAM, 2 CPUs, a 64 GiB virtual disk, Shared Network (NAT), and the project ISO attached as its CD. No host directory is configured in its saved `Sharing` settings. This is an existing VM, not the requested fresh disposable 30 GB test profile.
- Its already-running session initially showed `Ubuntu 24.04 LTS ... tty2`; this was an old session. After a cold restart with the graphical-target correction, XFCE did start and its bottom panel appeared. The desktop field was black and the wallpaper was not visible in that earlier image.
- The user then specified `/Users/leonardo/Downloads/Logo IFBA OS em Cinza Sutil.png` as the desktop wallpaper. The source file was copied unchanged to both the desktop wallpaper asset and the Plymouth splash asset. The rebuilt ISO has SHA-256 `da1aac1820a4a7b20555b3541277505b5a3890e35e59fe1d56df2dfcde5ac059`; `unsquashfs -cat` confirmed the wallpaper and splash bytes inside the ISO match the source (SHA-256 `51f6f6e1ef6d4067d5427d02d3f7204565a2d7291d41b098893cf8c1eb0532c0`). GRUB, Casper kernel/initrd, and `filesystem.squashfs` are present.
- After restarting UTM with that rebuilt ISO, the latest boot remained on the custom Plymouth splash. Revealing systemd messages showed `NetworkManager.service` still in its start job after about 3 minutes 10 seconds; no desktop was visible at the time of observation. This is a reproduced startup delay to investigate. The latest wallpaper is verified inside the ISO, but its desktop appearance is not yet verified in this boot.
- The root filesystem contains `/etc/systemd/system/default.target -> /lib/systemd/system/graphical.target` and `display-manager.service -> /lib/systemd/system/lightdm.service`. `graphical.target` pulls in LightDM. These static checks do not prove the current live boot reaches the desktop.
- No SUAP/AVA site was opened or logged into. No AI key or academic data was used. App launchers, network/audio controls, shutdown/reboot from the latest image, and the current wallpaper display remain unverified.

### Offline checks

- The build cache contains Ubuntu 24.04 amd64, Casper, XFCE 4.18, LightDM, Xorg, NetworkManager, NetSurf, Yaru Dark, Yaru icons, Inter, Whisker, and the XFCE panel plugins.
- `display-manager.service` points to LightDM; the latest build script creates the graphical default target.
- The panel is configured natively in Xfconf, with a separate XFCE panel `default.xml` profile. The Xfconf channel is parsed with `xfconf-query` in a D-Bus session and reports two panels and the expected plugin IDs.
- The welcome/Electron prototype remains separate and is not started in the live desktop. SUAP/AVA launchers point to their public HTTPS domains.
- `hdiutil imageinfo` identifies ISO 9660 boot media with volume label `IFBA_OS_24_04`; `bsdtar -tf` confirms the expected boot files; `output/*.iso` remains ignored by Git.

### Desktop checks still required

- [ ] Create a new disposable UTM VM with 4 GB RAM, 2 CPUs, a 30 GB disk, NAT, no host shares, and boot the latest ISO to XFCE.
- [ ] Confirm LightDM/autologin succeeds.
- [ ] Confirm the user-selected grayscale IFBA OS wallpaper and both native XFCE panels render in the latest ISO.
- [ ] Open the Whisker menu by mouse and Super/Windows key; check search, categories, favorites, and session actions.
- [ ] Check app launchers, task switching, workspace pager, Thunar, Terminal, NetSurf, settings, dialogs, and notifications.
- [ ] Verify SUAP/AVA launcher target URLs without visiting the sites or signing in.
- [ ] Check network/audio controls, readability at 1366×768 and 1920×1080, shutdown, and reboot.
- [ ] Investigate the previously observed Casper `/usr/bin/plymouth` message if it reappears.

### Stage 4 and final integration additions — 2026-11-18

- The assistant now uses SQLite schema v2, with a migration path from schema v1, per-conversation local summaries, user-configurable context bounds, opt-in memory search/edit/delete, JSON export, and retention controls.
- The assistant GTK window now includes memory/data management and user-initiated local tools. Tools are typed and bounded; file creation requires an expiring exact-operation confirmation, uses exclusive creation, and cannot overwrite an existing file. The model has no tool-calling path.
- A custom Plymouth script theme and the desktop both use the exact user-supplied `/Users/leonardo/Downloads/Logo IFBA OS em Cinza Sutil.png` artwork, copied unchanged to `assets/plymouth/ifba-os-startup.png` and `assets/wallpapers/ifba-os-desktop.png`.
- Automated offline suite: 36 tests pass, including schema migration, memory isolation/deletion/export/retention, sensitive-memory rejection, context limits, app/URL allowlists, folder traversal/symlink refusal, file permissions, non-overwrite behavior, and expired/replayed confirmation rejection.
- The latest ISO was rebuilt and inspected. It contains the selected wallpaper and splash bytes and the graphical target/LightDM links. The UTM boot displayed the custom splash but was still waiting for `NetworkManager.service`; current wallpaper rendering and full XFCE startup remain unverified. GTK/D-Bus assistant tools are also not runtime-verified.

This prototype has no installer, disk persistence, real educational-app installer, live-tested AI connection, or academic-data integration.
