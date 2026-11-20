# IFBA OS ISO release history

This log identifies generated ISO artifacts. A successful build records source identity and content integrity; it does not by itself prove boot or runtime behavior. New builds must receive a new product version and build ID. See the versioning rules in `AGENTS.md`.

## 0.1.0 — recovery build, 2026-11-19

- **Artifact:** `output/ifba-os-ubuntu-24.04-amd64.iso`
- **Build ID:** `ifba-20261119T180608Z-786e4d60b842`
- **Source commit:** `786e4d60b842f330c2f46189d9ce794df900b57a` (`source_dirty: false`)
- **Base / architecture:** Ubuntu 24.04 LTS / amd64
- **Build method:** new Docker volume `ifba-os-build-cache-recovery`; the original `ifba-os-build-cache` was preserved. The first build stopped on an incorrect XFCE profile path; the rootfs symlink validation was also corrected before this artifact was generated.
- **Artifact size:** 1,362,454,528 bytes
- **SHA-256:** `2f190e1b8b4e842d77e710f1586502cb3d19a90026bf368a2bf5fcd2df1ac344`
- **Build checks:** rootfs required-file and service-target checks passed; SquashFS and hybrid bootable ISO generation succeeded; ISO contains GRUB, Casper kernel/initrd, and SquashFS; computed SHA-256 and byte size match the generated sidecar manifest.
- **Automated checks:** 59 unit tests passed; Bash syntax, Python compilation, packaged XML parsing, and `git diff --check` passed.
- **UTM:** The existing x86_64/Q35 VM had this exact ISO path as boot-index 0, with 4 GiB RAM, 2 CPUs, e1000 Shared/NAT, virtio-gpu, and an existing 64 GiB qcow2 disk. The QEMU command line confirms the project ISO path. Output first reported `Display output is not active`, then showed the custom Plymouth image, followed by kernel/device output. The last visible initramfs line was `Begin: Running /scripts/init-premount ...`; no desktop or guest build ID appeared despite further waiting. QEMU TCG sustained high host CPU use and the UTM window became inaccessible. `utmctl` from the available SSH shell returned macOS OSStatus -1743. The exact QEMU launcher was sent SIGTERM and exited; this was not a guest-level shutdown. The existing virtual disk was preserved. This is failed runtime validation, not a successful desktop boot.
- **Open issues:** Desktop and wallpaper rendering, network, Firefox internet access, IFBA AI runtime, menu/app interactions, shutdown/reboot are unverified on this build. Earlier desktop evidence came from a different artifact and must not be attributed to this one.

### Addendum — later 0.1.0 boot observation, 2026-11-19

This is a later observation of the same artifact, not a replacement or rewrite of the original failed desktop-boot record above.

- **Artifact identity:** Same build `ifba-20261119T180608Z-786e4d60b842`, source commit `786e4d60b842f330c2f46189d9ce794df900b57a`, SHA-256 `2f190e1b8b4e842d77e710f1586502cb3d19a90026bf368a2bf5fcd2df1ac344`; hash and manifest still match.
- **New runtime evidence:** The running UTM/QEMU command line attached this ISO at boot-index 0. The guest advanced past the initramfs and reached the Ubuntu 24.04 text login; the live `ubuntu` account logged in and displayed a shell prompt. The earlier `/scripts/init-premount` message was an intermediate boot status, not the final state of this later observation.
- **Diagnosis status:** Kernel output showed `sr0`, `sda`, e1000/`enp0s1`, and virtio GPU. Read-only SquashFS inspection confirmed Casper, systemd-sysv, LightDM/greeter, XFCE/session, Xorg/core and NetworkManager packages; default target and display-manager symlinks point to graphical.target and LightDM. This confirms the observed guest passed media discovery/root boot and reached userspace, but does not prove LightDM started or isolate why no desktop was visible.
- **Remaining blocker:** UTM input/view control became unavailable from the SSH execution context (`noWindowsAvailable`, `utmctl` OSStatus `-1743`, `screencapture` without a display, and System Events accessibility error `-1719`). The visible shell followed an intentional switch to a text VT, so the graphical VT may not have been in view. No journal/status output for LightDM was captured, no corrective boot change is justified yet, and no new ISO/version was generated.
- **Outstanding checks:** Verify the graphical VT, LightDM/Xorg service state and boot journal; guest build ID; desktop wallpaper/panel/workspace; internet and Firefox; IFBA AI; persistence; and a graceful guest restart. No external or private credentials were used.

### Addendum — 0.1.0 graphical desktop confirmed, 2026-11-19

This is a new observation of the same running 0.1.0 artifact. It supplements the earlier shell/VT observations and leaves their historical records unchanged.

- **Artifact identity:** Product version `0.1.0`, build `ifba-20261119T180608Z-786e4d60b842`, source commit `786e4d60b842f330c2f46189d9ce794df900b57a`, SHA-256 `2f190e1b8b4e842d77e710f1586502cb3d19a90026bf368a2bf5fcd2df1ac344`, size 1,362,454,528 bytes. The current file hash was recomputed and matches this recorded artifact. UTM's active QEMU process attaches the same output path at boot-index 0.
- **Actual visual result:** A current screenshot from the UTM window shows the IFBA OS XFCE desktop, supplied grayscale wallpaper, SUAP and AVA IFBA shortcuts, and one bottom panel with application launchers, status area and clock. The screenshot is 2560×1600. Thus this running boot did pass initramfs and reached the graphical desktop. The screenshot was observed through the UTM computer-use surface and was not saved as a repository artifact.
- **Clarification:** Earlier black/text screens followed `Alt+F1`/`Alt+F2`, which select Linux `tty1`/`tty2`; returning to the graphical display showed the desktop. Those text screens do not establish a persistent boot or LightDM failure. LightDM's exact unit status, guest build ID, and journal remain uncollected.
- **Current issues:** The panel network icon visibly shows disconnected. The IFBA AI optional-setup notification is visible, but Firefox and IFBA AI were not launched during this observation. Menu interaction, workspace count, guest network diagnostics, HTTPS, persistence, shutdown and reboot remain unverified. CUA click actions returned `noWindowsAvailable`, and `utmctl` returned macOS `OSStatus -1743` from the current execution context. No macOS permission was bypassed.
- **Changes/build:** No source changes that affect the artifact and no rebuild were made. The release remains 0.1.0; this addendum does not rewrite prior outcomes or invent a new build/version.
- **Next:** Restore authorized UTM input to query LightDM/Xorg and guest network state, then test menu, Firefox, IFBA AI, settings, workspace defaults and persistence. Do not alter build inputs without a reproduced fault.

### Addendum — live network diagnostic, 2026-11-20

This is additional runtime evidence for the same 0.1.0 ISO; it is not a new build or a replacement for earlier results.

- **Artifact:** The output ISO SHA-256 remains `2f190e1b8b4e842d77e710f1586502cb3d19a90026bf368a2bf5fcd2df1ac344`; UTM's active QEMU process attaches that output path at boot-index 0.
- **Guest evidence:** On the running XFCE live session, `ip -br a` showed `enp0s1 DOWN` with no IPv4/IPv6 address; `nmcli g` reported `disconnected`, `connectivity unknown`, and no guest Wi-Fi hardware. The panel's red disconnected mark agreed with these commands. UTM's active QEMU arguments show an e1000 device on `vmnet-shared`.
- **Static image evidence:** The exact cached rootfs used for the image contains an enabled NetworkManager system service and a root-owned mode-0600 Ethernet connection profile configured for autoconnect and DHCP. This rules out a missing profile in the build cache but does not show that the running guest loaded or activated it.
- **Result:** Network failure is reproduced, but its cause remains unresolved. Further terminal input was garbled under high TCG load. No guest-side setting was changed, no ISO was rebuilt, and Firefox/NVIDIA/HTTPS remain untested in this run. The network feature is not marked fixed.

## 0.1.1 — assistant startup and kernel selection fixes, 2026-11-20

- **Artifact:** `output/ifba-os-ubuntu-24.04-amd64-v0.1.1.iso`
- **Build ID:** `ifba-20261120T151145Z-4c09ec5b71b3`
- **Source commit:** `4c09ec5b71b330ab6a2dc690b0230ca965efb3d1` (`source_dirty: false`)
- **Base / architecture:** Ubuntu 24.04 LTS / amd64
- **Build method:** Docker `ubuntu:24.04` with the existing `ifba-os-build-cache` volume. Build used the committed source in a clean detached worktree.
- **Build time:** `2026-11-20T15:11:45Z`
- **Artifact size:** 1,505,392,640 bytes
- **SHA-256:** `f8b82cd3245b89c45f982197c1d75164fa5e4775562e9a33c69b4a04be83f871`
- **Changes:** IFBA AI now shows its GTK window before making bounded, asynchronous D-Bus startup calls, so a slow or unavailable assistant service cannot block initial display. ISO construction now copies the active kernel and initramfs symlinks instead of failing when the cached root filesystem contains multiple kernel versions.
- **Build checks:** Rootfs validation passed; the rootfs imports the GTK/D-Bus assistant modules; `ifba-os-version` reports the embedded version/build/source; ISO 9660 boot structure was inspected. Targeted AI tests passed (13 tests), Python compilation, shell syntax, and `git diff --check` passed.
- **UTM:** The exact versioned ISO path was attached through the UTM file picker and the VM reached a live XFCE desktop. A 2560×1600 screenshot showed one lower panel, SUAP and AVA launchers, and a browser launcher. The desktop background in this view was Ubuntu blue, not the chosen IFBA wallpaper. The panel network indicator was disconnected. The guest `ifba-os-version` command was not queried.
- **Open issues:** IFBA AI window launch was not completed in this VM session; network and Firefox HTTPS remain unverified. Wallpaper, menu actions, persistence, graceful reboot, installer, and Plasma migration are not part of this build and remain open. Do not describe the assistant as runtime validated based on source/tests alone.

## Unversioned legacy artifacts

These hashes and short descriptions are retained from earlier audit records. Those builds predate embedded build metadata; missing IDs, source commits, sizes, or validations are intentionally not inferred.

| Artifact SHA-256 | Known change or observed result |
|---|---|
| `510ebd2499a7bcfcef93d249fde36bae66ef803247503d81a1009746e6b9f6b5` | Added the selected wallpaper as a system Xfdesktop default; ISO structure was reported bootable. |
| `17e9f8b8c6fafb3b77d20822ec36e229558da48cb36cff9c9963b63646723b72` | Included supplied PNG logo assets and encoded JPEGs used by the then separate welcome prototype. |
| `8cd3e892caef4c8614325080e7534c52b95b061d529a9dcbedee78af9f2c6311` | Corrected graphical target and LightDM link; no post-fix UTM boot was recorded for that exact artifact. |
| `da1aac1820a4a7b20555b3541277505b5a3890e35e59fe1d56df2dfcde5ac059` | Packaged the supplied grayscale wallpaper unchanged for desktop and Plymouth; bytes were verified in SquashFS. |
| `88901ac4237d49c94003acbafd1f17d3f925acaba2774c743d6563a7218190b1` | Switched browser packaging to Mozilla Firefox DEB and removed NetSurf; boot and guest network were not validated. |
| `08949f17d8ebd2f676c8b99db18826df048fa6eaa9828f93ce01ec24179f3b07` | Added model/reasoning UI and NVIDIA client changes; UTM showed splash then black display. |
| `6d320c44992edd02f3fe645c7c2016517ab498d00afe7932ce84627195091580` | Corrected default panel/workspace declarations; UTM access was unavailable for this build. |
| `9f6553df2575c710dac809c5a5d28aacdaa949056d2fb059927bc76ff4c9dffe` | Disabled the assistant settings stack transition; boot/runtime was not observed for the exact artifact. |
| `3022cef8989f8052dec5268c1c86b94f762e504e34ca0dd82726338be6e2a658` | Restored the XFCE failsafe session definition. A subsequent UTM run showed an XFCE panel and Firefox, but Firefox was offline and the wallpaper was obscured. |

## 0.2.0 — initial Plasma migration build, 2026-11-20

- **Artifact:** `output/ifba-os-ubuntu-26.04-amd64-v0.2.0.iso`
- **Build ID:** `ifba-20261120T161731Z-f06990135de4`
- **Source commit:** `f06990135de490fe5de280bf3e7e9dcabf95fd7a` (`source_dirty: false`)
- **Base / architecture:** Ubuntu 26.04 / amd64; Plasma 6.6 target
- **Build time:** `2026-11-20T16:17:31Z`
- **Build method:** Docker helper `ubuntu:24.04` with the isolated Plasma build cache; the `ubuntu:26.04` helper could not extract the bootstrap rootfs in this environment (`tar: Function not implemented`).
- **Artifact size:** 1,700,597,760 bytes
- **SHA-256:** `9770ffcfa428e2bf219c1159eba978bf719df284255e1485fd26d768ea75896d`
- **Build checks:** Build completed; manifest records the source commit and clean source state. The ISO is preserved under its versioned filename. Package/session rootfs inspection was performed during diagnosis of the next build.
- **UTM:** The exact 0.2.0 ISO booted through GRUB and showed the custom IFBA OS Plymouth splash. At the time of observation the display remained on the splash/black screen, with no desktop visible. This was an incomplete initial observation; a later boot of 0.2.1 below confirms the desktop can start after the session correction.
- **Unresolved at this build:** The X11 SDDM session selection did not correspond to the installed X11 session desktop file. Do not treat this artifact as a desktop-validated release.

## 0.2.1 — Plasma X11 session correction, 2026-11-20

- **Artifact:** `output/ifba-os-ubuntu-26.04-amd64-v0.2.1.iso`
- **Build ID:** `ifba-20261120T164231Z-cc43d4e43747`
- **Source commit:** `cc43d4e43747a54b84761f5940e2e44583c12520` (`source_dirty: false`)
- **Base / architecture:** Ubuntu 26.04 / amd64; Plasma 6.6 target
- **Build time:** `2026-11-20T16:42:31Z`
- **Build method:** Docker helper `ubuntu:24.04` with the isolated Plasma build cache. Output is versioned so rebuilding a later product version does not replace this artifact.
- **Artifact size:** 1,713,565,696 bytes
- **SHA-256:** `af961e76720e664eb1512485181b277598fa7044a491402dbe163b9698d6c75c`
- **Changes:** SDDM now selects `plasmax11.desktop`, which is the installed X11 Plasma session, instead of `plasma.desktop`, which is the Wayland session. Added metadata-derived versioned ISO naming.
- **Build checks:** 64 unit tests passed on the source commit; shell syntax, Python compilation, and `git diff --check` passed before build. SquashFS inspection confirmed `/usr/share/xsessions/plasmax11.desktop` invokes `/usr/bin/startplasma-x11`; SDDM is configured for X11 and autologin. Manifest and artifact hash/size match.
- **UTM:** The running `Linux` VM shows the supplied metallic IFBA OS wallpaper, desktop shortcuts for AVA IFBA, IFBA AI and SUAP, and a working-looking Plasma bottom panel with application launcher, browser/file-manager/terminal launchers, system tray and clock. The screen is the Plasma desktop, not the Plymouth splash; this corrects the preliminary black/splash-only observation made before the graphical session finished. UTM is left running this version so it can be observed. The panel appears light-colored and centered rather than the intended dark IFBA styling. A click attempt on the IFBA AI desktop shortcut did not produce a visible assistant window; further app-launch testing is pending, so the assistant is not runtime-validated.
- **Still unverified:** Exact guest build ID, SDDM/journal diagnostics, menu and shortcut interactions, Firefox network access, guest internet/DNS/HTTPS, IFBA AI functionality/API, workspace count, display scaling, persistence across restart, graceful shutdown/reboot, and Wayland session.

## Next product version

Product version `0.2.1` is the latest built artifact. The next release inputs assign `0.3.0` for the multiarchitecture feature set; commit them before building ARM64. If a separate AMD64 artifact is subsequently built, assign it a distinct semantic product version first and preserve all existing 0.2.x artifacts and records. Network, application behavior, styling and restart persistence still need validation.
