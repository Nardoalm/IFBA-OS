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

## 0.3.0 — native ARM64 multiarchitecture build, 2026-11-20

- **Artifact:** `output/ifba-os-ubuntu-26.04-arm64-v0.3.0.iso`
- **Build ID:** `ifba-20261120T173559Z-arm64-66f71bdac5cc`
- **Source commit:** `66f71bdac5cc8a08240aa9340627bdfed6095274` (`source_dirty: true`)
- **Base / architecture:** Ubuntu 26.04 LTS / arm64 (AArch64); Plasma 6.6 target
- **Build time:** `2026-11-20T17:35:59Z`
- **Build method:** Native `linux/arm64` Docker build using the isolated `ifba-os-plasma-build-cache-arm64` volume and official Ubuntu Ports archive. The AMD64 cache and existing UTM VM were preserved.
- **Artifact size:** 1,669,216,256 bytes
- **SHA-256:** `e9571211d212d0c1990a8058ff76310ebdef2096f30a4e2078addbf27c08dd40`
- **Changes:** Added architecture-aware build targets, ARM64 package/bootstrap/archive/GRUB settings, a separate ARM64 cache and release metadata. The ARM GRUB helper now installs `mtools`; the first build completed SquashFS but `grub-mkrescue` failed because `mformat` was unavailable. The follow-up build after commit `66f71bd` succeeded. Plasma Look-and-Feel defaults to Breeze Dark and the bottom panel uses full-width length mode.
- **Build checks:** All 66 Python unit tests passed after the `mtools` fix; shell syntax and `git diff --check` passed. The sidecar manifest SHA-256 and byte size match a host recomputation. `file` identifies a bootable ISO 9660 image; ISO listing contains `efi/boot/bootaa64.efi`, `casper/vmlinuz`, `casper/initrd`, and `casper/filesystem.squashfs`; the extracted kernel identifies as AArch64 PE32+. This validates image structure, not guest boot.
- **Source state:** The build metadata says `source_dirty: true` because `assets/plymouth/ifba-os-startup.png` changed locally during the build. That image change was preserved and not included in the build-fix commit. The artifact therefore includes build inputs from a dirty working tree; its exact content is identified by this artifact hash, while the source commit alone does not reproduce the changed splash asset.
- **UTM:** Not boot-tested. The existing `Linux` VM was observed suspended, x86_64, 4 GiB RAM and still attached to the older AMD64 v0.2.1 ISO. A separate ARM VM wizard was opened, but the CUA interface returned `noWindowsAvailable` when opening the ISO file picker, so no ARM VM was saved and no guest boot/runtime claim is made. The old VM was not changed or deleted.
- **Unresolved:** ARM64 boot, graphics, networking, Firefox, IFBA AI, panel behavior and performance remain unverified in a guest. The requested UTM view is not yet updated to the new ISO.

## 0.3.1 — AMD64 parity build, 2026-11-20

- **Artifact:** `output/ifba-os-ubuntu-26.04-amd64-v0.3.1.iso`
- **Build ID:** `ifba-20261120T174613Z-amd64-fe3960ea9231`
- **Source commit:** `fe3960ea923108561caf58e0e5ff4bab31fdbd84` (`source_dirty: false`)
- **Base / architecture:** Ubuntu 26.04 LTS / amd64 (x86_64); Plasma 6.6 target
- **Build time:** `2026-11-20T17:46:13Z`
- **Build method:** Ubuntu 24.04 Docker helper, official Ubuntu archive, and preserved AMD64 Plasma build cache. The ARM64 cache was not modified.
- **Artifact size:** 1,715,800,064 bytes
- **SHA-256:** `ef6039c1a5a103c8ae48cd5396ae939857e347bdf21f3b5c9df93e64d8fd11a4`
- **Changes:** Builds the shared Plasma/IFBA OS desktop for AMD64 at the distinct version 0.3.1, including the same network profile, browser, IFBA AI, panel layout, and current startup artwork inputs as the ARM64 work.
- **Build checks:** All 66 unit tests passed for the committed source inputs; Python compilation and build metadata checks passed. The sidecar manifest hash and size match independent host recomputation. `file` identifies a bootable ISO; its contents include `efi/boot/bootx64.efi`, Casper kernel/initrd and SquashFS; the kernel identifies as x86 bzImage. This validates structure, not guest boot.
- **UTM:** Not runtime-tested. The existing `Linux` VM remains suspended on AMD64 v0.2.1. The CUA file picker returned `noWindowsAvailable`; bundled `utmctl list` returned macOS `OSStatus -1743` because the current execution context is outside Aqua. The new ISO was not attached to a VM, and no desktop, network, Firefox or IFBA AI behavior is claimed.
- **Unresolved:** Both architecture builds still require real UTM boot validation. Network/DHCP/DNS/HTTPS, Firefox, IFBA AI, visual panel, desktop performance, persistence and restart remain unverified for these 0.3.x artifacts.

## Next product version

Product version `0.3.1` is the latest built artifact (AMD64); ARM64 `0.3.0` is its architecture counterpart. Neither has guest runtime validation. Assign a new version (`0.3.2` unless release scope changes) before another ISO build. Preserve all existing artifacts and records.
