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

### Current UTM desktop inspection — 2026-11-18

- The UTM guest reached an XFCE desktop with a tall lower panel and desktop launchers, so this visible session was not terminal-only.
- The desktop showed Ubuntu's blue default background, not the selected grayscale IFBA metallic wallpaper; the network tray icon showed a red disconnected mark. These are UI observations, not a diagnosed networking cause.
- UTM's drive menu showed an attached ISO named `ifba-os-ubuntu-24.04-amd64.iso`, but the path and SHA-256 were not established during this inspection. This does not prove the VM booted the current project artifact.
- The VM is QEMU x86_64/Q35, 4 GiB RAM, 2 CPUs, 64 GiB disk, Shared networking (NAT), and e1000 virtual Ethernet. NAT uses the Mac's active uplink; the guest does not need host Wi-Fi credentials.

### Rebuilt Firefox ISO boot — 2026-11-18

- Rebuilt `output/ifba-os-ubuntu-24.04-amd64.iso`; SHA-256 `88901ac4237d49c94003acbafd1f17d3f925acaba2774c743d6563a7218190b1`. `file` reports bootable ISO 9660 with volume label `IFBA_OS_24_04`.
- The UTM CD menu showed the expected ISO filename. Its external file path was not exposed, so the attached media cannot be tied conclusively to this hash. UTM started and displayed the grayscale IFBA OS Plymouth splash, then a text console/login; LightDM and XFCE did not appear during the observed run. The guest was stopped after the check.
- A text login shell was reachable. No guest network diagnostics were collected: QEMU Guest Agent is absent, and UTM `ip-address`/`exec` report that limitation. Therefore DHCP, gateway, DNS, and HTTPS are unverified; the red disconnected icon from the earlier desktop run remains an unresolved symptom.
- Static inspection of the built rootfs confirms `/etc/systemd/system/default.target` points to `graphical.target` and `display-manager.service` points to LightDM. The rootfs includes Firefox `160.0.1~build1` and `firefox-l10n-pt-br`, does not include `netsurf-gtk`, and sets Firefox in the panel, XFCE helper, URL MIME associations, and application alternatives.
- The wallpaper at `/usr/share/backgrounds/ifba-os/wallpaper.png` inside the ISO hashes to the source asset (`51f6f6e1ef6d4067d5427d02d3f7204565a2d7291d41b098893cf8c1eb0532c0`). The same image appeared on the Plymouth splash. Its appearance as the desktop background remains unverified because LightDM/XFCE did not start.
- No host Wi-Fi password was entered or written to project files. No websites, student accounts, API keys, or private data were used.

### Offline checks

- The build cache contains Ubuntu 24.04 amd64, Casper, XFCE 4.18, LightDM, Xorg, NetworkManager, Firefox, Yaru Dark, Yaru icons, Inter, Whisker, and the XFCE panel plugins.
- `display-manager.service` points to LightDM; the latest build script creates the graphical default target.
- The panel is configured natively in Xfconf, with a separate XFCE panel `default.xml` profile. The Xfconf channel is parsed with `xfconf-query` in a D-Bus session and reports two panels and the expected plugin IDs.
- The welcome/Electron prototype remains separate and is not started in the live desktop. SUAP/AVA launchers point to their public HTTPS domains.
- `hdiutil imageinfo` identifies ISO 9660 boot media with volume label `IFBA_OS_24_04`; `bsdtar -tf` confirms the expected boot files; `output/*.iso` remains ignored by Git.

### Desktop checks still required

- [ ] Create a new disposable UTM VM with 4 GB RAM, 2 CPUs, a 30 GB disk, NAT, no host shares, and boot the latest ISO to XFCE.
- [ ] Confirm LightDM/autologin succeeds.
- [ ] Confirm the user-selected grayscale IFBA OS wallpaper and both native XFCE panels render in the latest ISO.
- [ ] Open the Whisker menu by mouse and Super/Windows key; check search, categories, favorites, and session actions.
- [ ] Check app launchers, task switching, workspace pager, Thunar, Terminal, Firefox, settings, dialogs, and notifications.
- [ ] Verify SUAP/AVA launcher target URLs without visiting the sites or signing in.
- [ ] Check network/audio controls, readability at 1366×768 and 1920×1080, shutdown, and reboot.
- [ ] Investigate the previously observed Casper `/usr/bin/plymouth` message if it reappears.

### Stage 4 and final integration additions — 2026-11-18

- The assistant now uses SQLite schema v2, with a migration path from schema v1, per-conversation local summaries, user-configurable context bounds, opt-in memory search/edit/delete, JSON export, and retention controls.
- The assistant GTK window now includes memory/data management and user-initiated local tools. Tools are typed and bounded; file creation requires an expiring exact-operation confirmation, uses exclusive creation, and cannot overwrite an existing file. The model has no tool-calling path.
- A custom Plymouth script theme and the desktop both use the exact user-supplied `/Users/leonardo/Downloads/Logo IFBA OS em Cinza Sutil.png` artwork, copied unchanged to `assets/plymouth/ifba-os-startup.png` and `assets/wallpapers/ifba-os-desktop.png`.
- Automated offline suite: 36 tests pass, including schema migration, memory isolation/deletion/export/retention, sensitive-memory rejection, context limits, app/URL allowlists, folder traversal/symlink refusal, file permissions, non-overwrite behavior, and expired/replayed confirmation rejection.
- The latest ISO was rebuilt and inspected. It contains the selected wallpaper and splash bytes and the graphical target/LightDM links. The UTM boot displayed the custom splash but was still waiting for `NetworkManager.service`; current wallpaper rendering and full XFCE startup remain unverified. GTK/D-Bus assistant tools are also not runtime-verified.

### Corrective rebuild and current UTM run — 2026-11-18

- Rebuilt `output/ifba-os-ubuntu-24.04-amd64.iso`; SHA-256 `08949f17d8ebd2f676c8b99db18826df048fa6eaa9828f93ce01ec24179f3b07`. The UTM QEMU command line confirms that exact path is attached as boot-index 0. `file` identifies bootable ISO 9660 media with volume label `IFBA_OS_24_04`; the build completed successfully.
- The current UTM VM is the existing x86_64/Q35 machine with 4 GiB RAM, 2 CPUs, 64 GiB disk, e1000, and shared NAT. It was started with the rebuilt ISO. The display first showed the custom IFBA OS splash, then went black; after more than seven minutes it had not reached the XFCE desktop. `utmctl ip-address` still reports that QEMU Guest Agent is unavailable, so guest-side commands and network diagnostics could not run. The current desktop and network therefore fail runtime verification; no claim is made that this image currently opens the graphical session.
- A host-side attempt to send a keyboard event to UTM was denied by macOS Accessibility permissions. No host security settings were changed.
- The image contains the selected wallpaper at its configured desktop and Plymouth locations (source wallpaper SHA-256 `51f6f6e1ef6d4067d5427d02d3f7204565a2d7291d41b098893cf8c1eb0532c0`), but appearance as an XFCE desktop wallpaper is not verified. The previous Firefox profile-loading error has not been re-tested inside this latest boot; neither Firefox nor IFBA AI can be claimed to launch successfully in the guest.
- The build now includes `qemu-guest-agent`, a wired DHCP NetworkManager profile, `pt_BR.UTF-8`, `America/Bahia`, corrected home/cache ownership, and the XFCE top/bottom panel configuration. These are build contents, not proof of runtime operation.
- The current UTM session remains started on the custom splash/black display. Do not use the live desktop until the boot hang is diagnosed. No host Wi-Fi password, student data, NVIDIA key, SUAP/AVA login, or private site was used.
- Offline validation for this corrective slice: 48 unit tests pass; Python compilation, shell syntax checks, and `git diff --check` pass. No authenticated NVIDIA request was made. The model registry/payload path is source- and mock-tested only.

### Follow-up UTM boot observation — 2026-11-18

- Rechecked the same ISO and verified its attached path from the running QEMU command line: `/Users/leonardo/Documents/IFBA-OS/output/ifba-os-ubuntu-24.04-amd64.iso`. The ISO hash remains `08949f17d8ebd2f676c8b99db18826df048fa6eaa9828f93ce01ec24179f3b07`.
- The GRUB 2.12 menu and `IFBA OS prototype (live)` entry render. On a subsequent boot, UTM displayed the custom IFBA OS splash, then an inactive/black video output. The exact last observed UTM message was `Display output is not active.` A later restart again rendered GRUB before the output became inactive. Therefore firmware/GRUB and the attached ISO are demonstrably reached; the failure is after GRUB, but these observations do not identify whether the Linux kernel, Casper, systemd, LightDM, or UTM's video path is responsible.
- UTM is using x86_64 QEMU with Q35, 4 GiB RAM, 2 CPUs, `virtio-gpu-pci`, e1000, shared NAT, and `-accel tcg` (software CPU emulation) on this host. This is the existing VM with a 64 GiB virtual disk, not a new disposable 30 GiB VM. No shared folder is configured.
- Attempted a virtual-terminal switch, but no guest console text was captured. `utmctl` from the available shell reports `OSStatus -1743` because it is running from an SSH session; the host Terminal application is also unavailable to the computer-use session. The QEMU Guest Agent did not respond. No boot journal, LightDM/Xorg logs, or guest network state could be collected.
- No source changes or ISO rebuild were justified: the boot failure is not yet localized, so changing services or graphics settings would be speculative. The VM was paused after the observation to stop software emulation without force-stopping its virtual disk.
- Result: **boot failure reproduced, root cause not yet identified, and XFCE desktop not validated**. Wallpaper presence inside the ISO remains a byte-level check only; network, Firefox, AI UI/runtime, shutdown, and reboot remain unverified. No credentials, student data, SUAP/AVA login, or authenticated NVIDIA request were used.

This prototype has no installer, disk persistence, real educational-app installer, live-tested AI connection, or academic-data integration.
