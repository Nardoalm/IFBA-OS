# Virtual machine test checklist

Use a disposable UTM/QEMU/VirtualBox VM with 4 GB RAM, 2 CPUs, a 30 GB virtual disk, and NAT networking. Do not mount host folders or pass through personal credentials. Select the live boot entry only; this ISO is not an installer.

## Validation record — 2026-11-18

### UTM run

- VM configuration: UTM, 4 GB RAM, 2 CPUs, 30 GB virtual disk, Shared Network (NAT), no host shared folders, ISO mounted as boot media.
- The prior ISO reached GRUB but booted to a text console (`Ubuntu 24.04 LTS ... tty2`) instead of starting XFCE. The wallpaper, panels, menu, and desktop launchers were therefore not verified in that run.
- Root filesystem inspection found that `/etc/systemd/system/default.target` was missing. Although LightDM was installed and `display-manager.service` pointed to LightDM, systemd had no graphical default target. The build now explicitly links `default.target` to `graphical.target`.
- The ISO was rebuilt after that correction and again after the AI foundation/chat changes. The current artifact is 1,259,190,272 bytes; SHA-256: `1daf0d3fe6acac2fde16ffb1d341e4840478058f325d095d100517f1408177a4`. `bsdtar` lists the GRUB config, Casper kernel/initrd, and compressed root filesystem in the image. This confirms archive structure only; the current graphical boot remains unverified.
- An isolated VM run was attempted through UTM. The existing `Linux` VM was already running, and `utmctl clone` refused to clone it while running. Its config enables a host folder share, so it was not used for testing and was left unchanged. The UTM window was unavailable through the current UI automation session, so a new disposable VM could not be configured in this run. No claim is made that this ISO reaches XFCE.
- The current ISO includes the Stage 1 assistant foundation and Stage 2 NVIDIA text-chat package. The source test suite passes with mocked API requests. GTK/D-Bus/keyring runtime and a live NVIDIA API request remain unverified.
- Stage 3 visual-guidance code and its X11/AT-SPI packages were added after that ISO was built. Rebuild before any visual runtime test; the final integration stage should produce the next ISO.
- No SUAP/AVA site was opened or logged into. No AI key or academic data was used. Shutdown/reboot from XFCE remain unverified.

### Offline checks

- The build cache contains Ubuntu 24.04 amd64, Casper, XFCE 4.18, LightDM, Xorg, NetworkManager, NetSurf, Yaru Dark, Yaru icons, Inter, Whisker, and the XFCE panel plugins.
- `display-manager.service` points to LightDM; the latest build script creates the graphical default target.
- The panel is configured natively in Xfconf, with a separate XFCE panel `default.xml` profile. The Xfconf channel is parsed with `xfconf-query` in a D-Bus session and reports two panels and the expected plugin IDs.
- The welcome/Electron prototype remains separate and is not started in the live desktop. SUAP/AVA launchers point to their public HTTPS domains.
- `hdiutil imageinfo` identifies ISO 9660 boot media with volume label `IFBA_OS_24_04`; `bsdtar -tf` confirms the expected boot files; `output/*.iso` remains ignored by Git.

### Desktop checks still required

- [ ] Create a new disposable UTM VM with 4 GB RAM, 2 CPUs, a 30 GB disk, NAT, no host shares, and boot the latest ISO to XFCE.
- [ ] Confirm LightDM/autologin succeeds.
- [ ] Confirm the metallic wallpaper and both native XFCE panels render.
- [ ] Open the Whisker menu by mouse and Super/Windows key; check search, categories, favorites, and session actions.
- [ ] Check app launchers, task switching, workspace pager, Thunar, Terminal, NetSurf, settings, dialogs, and notifications.
- [ ] Verify SUAP/AVA launcher target URLs without visiting the sites or signing in.
- [ ] Check network/audio controls, readability at 1366×768 and 1920×1080, shutdown, and reboot.
- [ ] Investigate the previously observed Casper `/usr/bin/plymouth` message if it reappears.

This prototype has no installer, disk persistence, real educational-app installer, live-tested AI connection, or academic-data integration.
