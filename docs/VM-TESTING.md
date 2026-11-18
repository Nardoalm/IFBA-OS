# Virtual machine test checklist

Use a disposable UTM/QEMU/VirtualBox VM with 4 GB RAM, 2 CPUs, a 30 GB virtual disk, and NAT networking. Do not mount host folders or pass through personal credentials. Select the live boot entry only; this ISO is not an installer.

## Validation record — 2026-11-18

### UTM run

- VM configuration: UTM, 4 GB RAM, 2 CPUs, 30 GB virtual disk, Shared Network (NAT), no host shared folders, ISO mounted as boot media.
- The prior ISO reached GRUB but booted to a text console (`Ubuntu 24.04 LTS ... tty2`) instead of starting XFCE. The wallpaper, panels, menu, and desktop launchers were therefore not verified in that run.
- Root filesystem inspection found that `/etc/systemd/system/default.target` was missing. Although LightDM was installed and `display-manager.service` pointed to LightDM, systemd had no graphical default target. The build now explicitly links `default.target` to `graphical.target`.
- The latest ISO was rebuilt after that correction. SHA-256: `8cd3e892caef4c8614325080e7534c52b95b061d529a9dcbedee78af9f2c6311`. Its graphical boot remains unverified; do not report the native desktop as working until a fresh UTM run reaches XFCE.
- No SUAP/AVA site was opened or logged into. No AI key or academic data was used. Shutdown/reboot from XFCE remain unverified.

### Offline checks

- The build cache contains Ubuntu 24.04 amd64, Casper, XFCE 4.18, LightDM, Xorg, NetworkManager, NetSurf, Yaru Dark, Yaru icons, Inter, Whisker, and the XFCE panel plugins.
- `display-manager.service` points to LightDM; the latest build script creates the graphical default target.
- The panel is configured natively in Xfconf, with a separate XFCE panel `default.xml` profile. The Xfconf channel is parsed with `xfconf-query` in a D-Bus session and reports two panels and the expected plugin IDs.
- The welcome/Electron prototype remains separate and is not started in the live desktop. SUAP/AVA launchers point to their public HTTPS domains.
- `file` identifies the current artifact as a bootable ISO 9660 image with DOS/MBR boot metadata and volume label `IFBA_OS_24_04`; `output/*.iso` remains ignored by Git.

### Desktop checks still required

- [ ] Boot the latest ISO to XFCE and confirm LightDM/autologin succeeds.
- [ ] Confirm the metallic wallpaper and both native XFCE panels render.
- [ ] Open the Whisker menu by mouse and Super/Windows key; check search, categories, favorites, and session actions.
- [ ] Check app launchers, task switching, workspace pager, Thunar, Terminal, NetSurf, settings, dialogs, and notifications.
- [ ] Verify SUAP/AVA launcher target URLs without visiting the sites or signing in.
- [ ] Check network/audio controls, readability at 1366×768 and 1920×1080, shutdown, and reboot.
- [ ] Investigate the previously observed Casper `/usr/bin/plymouth` message if it reappears.

This prototype has no installer, disk persistence, real educational-app installer, AI connection, or academic-data integration.
