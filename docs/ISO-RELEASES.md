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

Matched v0.3.4 images are built for both architectures from the same source commit and verified. Their runtime status remains unvalidated until real guest boots and feature checks are completed; see the v0.3.4 entry below.

## Artifact organization migration — 2026-11-20

All six versioned ISO artifacts and the unversioned 24.04 AMD64 compatibility alias were SHA-256 and byte-size verified against their manifests before migration. The six versioned artifacts are now stored once under `output/versions/vX.Y.Z/{amd64,arm64}/` with one `manifest.json` per artifact. ISO content hashes remained unchanged after the move. Root-level versioned ISO names and their sidecar manifests are relative symlinks to the archived files, preserving existing local references without copying multi-gigabyte images. The unversioned 24.04 AMD64 compatibility path points to the identical v0.1.1 ISO; its legacy sidecar remains available.

The v0.1.0 manifest had a historical filename mismatch (`artifact.file` named the unversioned 24.04 alias), even though the recorded SHA-256 and size matched the versioned v0.1.0 ISO. During migration, only that JSON filename field was corrected to the exact archived ISO name; no ISO bytes changed. This normalization is covered by a regression test.

| Version / architecture | Build ID | Source commit | ISO SHA-256 | Size (bytes) | Runtime status |
|---|---|---|---|---:|---|
| 0.1.0 / amd64 | `ifba-20261119T180608Z-786e4d60b842` | `786e4d60b842f330c2f46189d9ce794df900b57a` | `2f190e1b8b4e842d77e710f1586502cb3d19a90026bf368a2bf5fcd2df1ac344` | 1,362,454,528 | Desktop previously observed; see history above |
| 0.1.1 / amd64 | `ifba-20261120T151145Z-4c09ec5b71b3` | `4c09ec5b71b330ab6a2dc690b0230ca965efb3d1` | `f8b82cd3245b89c45f982197c1d75164fa5e4775562e9a33c69b4a04be83f871` | 1,505,392,640 | Desktop observed; features listed above remain unverified |
| 0.2.0 / amd64 | `ifba-20261120T161731Z-f06990135de4` | `f06990135de490fe5de280bf3e7e9dcabf95fd7a` | `9770ffcfa428e2bf219c1159eba978bf719df284255e1485fd26d768ea75896d` | 1,700,597,760 | Splash/black, no desktop in that observation |
| 0.2.1 / amd64 | `ifba-20261120T164231Z-cc43d4e43747` | `cc43d4e43747a54b84761f5940e2e44583c12520` | `af961e76720e664eb1512485181b277598fa7044a491402dbe163b9698d6c75c` | 1,713,565,696 | Plasma desktop observed; functionality incomplete |
| 0.3.0 / arm64 | `ifba-20261120T173559Z-arm64-66f71bdac5cc` | `66f71bdac5cc8a08240aa9340627bdfed6095274` (dirty source) | `e9571211d212d0c1990a8058ff76310ebdef2096f30a4e2078addbf27c08dd40` | 1,669,216,256 | Not boot-tested in UTM |
| 0.3.1 / amd64 | `ifba-20261120T174613Z-amd64-fe3960ea9231` | `fe3960ea923108561caf58e0e5ff4bab31fdbd84` | `ef6039c1a5a103c8ae48cd5396ae939857e347bdf21f3b5c9df93e64d8fd11a4` | 1,715,800,064 | Not runtime-tested |

At the time of the 2026-11-20 migration, `output/latest/amd64/` pointed to v0.3.1 and `output/latest/arm64/` to v0.3.0, with `complete_pair: false`. The subsequent v0.3.2 build updated these local pointers as documented below. ISO artifacts remain ignored by Git; this table preserves historical identities in tracked documentation.

## 0.3.2 — Matched KScreenLocker build, 2026-11-21

| Architecture | Build ID | Source commit | Build time (UTC) | Size (bytes) | SHA-256 | Build status | Runtime status |
|---|---|---|---|---:|---|---|---|
| arm64 | `ifba-20261121T034012Z-arm64-7d5b1507c028` | `7d5b1507c028c3e7e6aca8237f548815c539ca38` | `2026-11-21T03:40:12Z` | 1,974,886,400 | `b47e26dbe181e8648fe21334c74818608accb747a59ad8a508d925b978f3afaa` | built and structurally verified | unvalidated |
| amd64 | `ifba-20261121T034321Z-amd64-7d5b1507c028` | `7d5b1507c028c3e7e6aca8237f548815c539ca38` | `2026-11-21T03:43:21Z` | 2,031,228,928 | `c6eca00164b599547125c77565b57f744c3197457550e9670d3638a6661eafc4` | built and structurally verified | unvalidated |

- **Build method:** Ubuntu 24.04 container helpers and the project’s architecture-specific Plasma rootfs caches. The images embed matching committed source state (`source_dirty: false`). ISO verification confirmed architecture-specific volume labels, boot catalog, kernel/initrd, SquashFS and release metadata.
- **Release pointers:** Both local `output/latest/{arm64,amd64}` pointers now resolve to v0.3.2. `output/latest/release-status.json` records `complete_pair: true` and the shared source commit. Artifacts are local ignored build output, not Git-tracked files.
- **KScreenLocker:** The derived Plasma shell package and QML are present in both root filesystems, selected by the live/new-user defaults, and preserve KDE’s native authenticator/PAM path. Automated source/package tests passed before the build.
- **UTM:** Not booted. The existing ARM64 VM remains stopped with historical v0.3.0 media. UTM’s library window became inaccessible to UI automation, so no disposable VM was created; screenshots and live-session acceptance remain pending. See [`VM-TESTING.md`](VM-TESTING.md).


## 0.3.3 — NetworkManager, IFBA AI and desktop integration, 2026-11-21

| Architecture | Build ID | Source commit | Build time (UTC) | Size (bytes) | SHA-256 | Build status | Runtime status |
|---|---|---|---|---:|---|---|---|
| arm64 | `ifba-20261121T183738Z-arm64-fedfa208f47a` | `fedfa208f47a9ee54d4690a64d410c6af287cb45` | `2026-11-21T18:37:38Z` | 1,962,625,024 | `e5ff90b8222e31aae53d66b26319879990ab03cab1a2e133c6332cdccc8aaaa7` | built and structurally verified | unvalidated |
| amd64 | `ifba-20261121T184747Z-amd64-fedfa208f47a` | `fedfa208f47a9ee54d4690a64d410c6af287cb45` | `2026-11-21T18:47:47Z` | 2,018,887,680 | `326f5781dcccab0affdd2fb27d0f09b56c5c8ec871bdf3c3520039e569468d9e` | built and structurally verified | unvalidated |

- **Build method:** `./scripts/build-iso.sh --both` from a clean detached worktree at commit `fedfa208f47a9ee54d4690a64d410c6af287cb45`; Ubuntu 24.04 helper containers, official Ubuntu 26.04 archive/Ports and existing per-architecture caches. The existing `output/versions` and `output/latest` were reused; historical ISO files and Docker volumes were preserved. Both manifests record `source_dirty: false`.
- **Build checks:** Rootfs package/configuration assertions passed for both architectures. The builder generated each ISO, extracted kernel, initrd, SquashFS and GRUB config for comparison, and published only after checks. `release_artifacts.py verify` passed for both manifests; host SHA-256 and byte-size recomputation matched. `file` identifies both as bootable ISO 9660 DOS/MBR media with architecture-specific labels. This is structural validation only, not proof of Linux boot.
- **Release pointers:** `output/latest/{arm64,amd64}` now resolve to v0.3.3 and `release-status.json` has `complete_pair: true` for the shared commit above.
- **Warnings:** The helper/container emitted expected service-start/D-Bus notices in chroot, `mksquashfs` warnings for `system.posix_acl_*` xattr prefixes, `xorriso` warnings that the volume ID does not follow ISO 9660 text rules, and initramfs fallback from zstd to gzip. Thonny emitted Python `SyntaxWarning`s. These were non-fatal; package/rootfs and ISO checks completed successfully.
- **Automated checks:** 95 tests passed, 2 target-image PyQt6 tests skipped. Bash/POSIX shell syntax, Python compilation, JavaScript syntax and `git diff --check` passed on the committed source.
- **UTM:** A separate ARM64 QEMU wizard was configured with 4096 MiB RAM, four CPU cores and OpenGL disabled. Clicking Browse for the v0.3.3 ISO returned `noWindowsAvailable`; the unsaved wizard was canceled. No VM was created and no existing VM/media was changed. The AMD64 ISO was not attached to a VM. No boot, guest screenshot, desktop, network or Calamares result is claimed. Manual selection paths are in `VM-TESTING.md`.


## 0.3.4 — Matched Plasma design and stability build, 2026-11-22 UTC

| Architecture | Build ID | Source commit | Build time (UTC) | Size (bytes) | SHA-256 | Build status | Runtime status |
|---|---|---|---|---:|---|---|---|
| arm64 | `ifba-20261122T005234Z-arm64-e7ebe4a27297` | `e7ebe4a27297a656517363162fd8454018ca7709` | `2026-11-22T00:52:34Z` | 2,008,064,000 | `2593fdc64986c3243a77c59d1e41c43b477cfb718e899220c77523770f4bfcd7` | built and structurally verified | unvalidated |
| amd64 | `ifba-20261122T005542Z-amd64-e7ebe4a27297` | `e7ebe4a27297a656517363162fd8454018ca7709` | `2026-11-22T00:55:42Z` | 2,065,125,376 | `25ecc7a64a7b10683263ab7254c69d79e39a412a0ed05f97cdd5c72e801b499c` | built and structurally verified | unvalidated |

- **Build method:** `./scripts/build-iso.sh --both` from clean source commit `e7ebe4a27297a656517363162fd8454018ca7709`; ARM64 and AMD64 used the existing architecture-specific build caches. The manifest source commit is identical and `source_dirty: false` for both.
- **Verification:** Release manifest/hash/size and ISO structure checks passed for both architectures, including boot catalog, architecture metadata and embedded boot/rootfs checks. `file` identifies ISO 9660 DOS/MBR bootable media. These checks do not prove Linux boot or desktop runtime. The full automated suite passed 121 tests with 2 skips before build.
- **Warnings:** Build tools reported unsupported `system.posix_acl_default/access` xattr prefixes from `mksquashfs`; an ISO volume ID requiring ISO 9660 normalization and automatic MBR geometry adjustment from `xorriso`; initramfs fell back from zstd to gzip; and chroot package setup emitted non-fatal service/D-Bus and `/dev/pts` logging notices. Both builds completed with exit status 0 and structural checks passed.
- **Publication:** `output/latest/{arm64,amd64}/` contains the v0.3.4 files and per-architecture manifests; `release-status.json` says `complete_pair: true` with the shared source commit. No v0.3.4 ISO was added to `output/versions/`.
- **Local archive cleanup:** At the owner’s explicit request, older archived ISO files were removed locally. The v0.3.3 AMD64 and v0.3.2 ARM64/AMD64 media are no longer present; their historical identities and hashes remain recorded above. The v0.3.3 ARM64 media and manifest were retained at their original path because the currently running historical UTM VM attaches that file.
- **UTM:** A separate ARM64 QEMU Linux wizard was prepared with 4096 MiB RAM, 4 CPU cores, QEMU and “Boot from ISO image”. The native macOS **Browse…** action failed with `-10005: noWindowsAvailable`; the ISO path remained blank and no new VM was saved or booted. The existing historical ARM64 VM remains on v0.3.3. AMD64 v0.3.4 was not attached. No v0.3.4 guest screenshot or runtime result is claimed. For manual continuation, select `/Users/leonardo/Documents/IFBA-OS/output/latest/arm64/ifba-os-ubuntu-26.04-arm64-v0.3.4.iso` in the current wizard; finish creating a separate test VM and leave historical VMs unchanged.


## 0.3.5 — IFBA AI and Plasma first-run fixes, 2026-11-22 UTC

| Architecture | Build ID | Source commit | Build time (UTC) | Size (bytes) | SHA-256 | Build status | Runtime status |
|---|---|---|---|---:|---|---|---|
| arm64 | `ifba-20261122T013833Z-arm64-03828a82d0ea` | `03828a82d0ea178ca073dcc44f139c91778562c0` | `2026-11-22T01:38:33Z` | 2,008,068,096 | `e2efd2c04c62a320b84c68ce46c3a68e11474819d55606230f000227e0efb0b3` | built and structurally verified | unvalidated |
| amd64 | `ifba-20261122T014140Z-amd64-03828a82d0ea` | `03828a82d0ea178ca073dcc44f139c91778562c0` | `2026-11-22T01:41:40Z` | 2,065,129,472 | `d2a5f830d9b9cbe87d5f30bf6b26ba23110bc4a47134c16cdac599078f364b1f` | built and structurally verified | unvalidated |

- **Build method:** `./scripts/build-iso.sh --both` from clean detached worktree commit `03828a82d0ea178ca073dcc44f139c91778562c0`; Ubuntu 24.04 helper containers generated both Ubuntu 26.04 targets. Both manifests record the same version/source commit and `source_dirty: false`.
- **Verification:** Both `release_artifacts.py verify` commands passed. The build extracted and checked the kernel, initrd, SquashFS and GRUB configuration; the publisher verified each architecture and atomically published the pair. `output/latest/release-status.json` reports `complete_pair: true`. These are build and structural checks, not guest boot/runtime validation.
- **Warnings:** `mksquashfs` reported unrecognized `system.posix_acl_default` and `system.posix_acl_access` xattr prefixes; `xorriso` warned that the volume ID does not follow ISO 9660 text rules and noted automatic MBR geometry adjustment. ARM64 initramfs fell back from zstd to gzip. Qt tooling changed the non-UTF-8 `C` locale to `C.UTF-8`. AMD64 package cleanup reported it could not write an apt log because `/dev/pts` was not mounted. These notices were non-fatal; both builds and structural verification completed with exit status 0.
- **Changes included:** IFBA AI now begins with a visible connection state, renders a no-conversation welcome, presents a recoverable D-Bus error/retry state, and no longer calls the unsupported GTK 3 `ToggleButton.set_group` API. Welcome sizing is bounded to available screen geometry. The native Kickoff launcher with the official IF mark is added to the top panel, and Welcome documents the native Alt+Space KRunner shortcut.
- **Latest and archive:** `output/latest/{arm64,amd64}/` contains only the v0.3.5 pair. Previous v0.3.4 files were replaced there per the owner's request. `output/versions/v0.3.3/arm64/` remains untouched because the historical UTM VM references that exact ISO.
- **Automated/runtime checks:** The complete host suite passed 127 tests with 5 target-platform skips. Separate Ubuntu Linux/Xvfb tests passed 2 GTK assistant runtime cases and 3 Qt Welcome runtime cases. These do not replace live desktop testing.
- **UTM:** No v0.3.5 ISO was attached or booted. UTM still shows the historical ARM64 `IFBA OS` VM (4 vCPUs, 6144 MiB, QEMU/HVF) with v0.3.3 attached; its `virtio-gpu-pci` display is disabled and UTM reports “Display output is not active.” The file picker previously failed with `noWindowsAvailable`. Create a separate test VM and manually select the paths recorded in `VM-TESTING.md`; do not modify the historical VM.

## 0.3.6 — Plasma native-component simplification and release guard fix — 2026-11-22 UTC

| Architecture | Build ID | Source commit | Build time (UTC) | Size (bytes) | SHA-256 | Build status | Runtime status |
|---|---|---|---|---:|---|---|---|
| arm64 | `ifba-20261122T033749Z-arm64-ef8481db8e5e` | `ef8481db8e5e47a11f1c96f6319bccc63d1b969d` | `2026-11-22T03:37:49Z` | 2,018,113,536 | `cf3b620d9ec5ac546ee6eaa1ecfc51dc9e0adbe09ef3b2472d2d73af63b033f9` | built and structurally verified | unvalidated |
| amd64 | `ifba-20261122T034047Z-amd64-ef8481db8e5e` | `ef8481db8e5e47a11f1c96f6319bccc63d1b969d` | `2026-11-22T03:40:47Z` | 2,076,028,928 | `de3d959aa6f5c7d61474208878db19b67e86836c6de116cebabad11d2a395649` | built and structurally verified | unvalidated |

- **Build method:** Official `./scripts/build-iso.sh --both` pipeline from a clean detached worktree at the shared source commit. The v0.3.5 images were first preserved in `output/versions/v0.3.5/`; the verified v0.3.6 pair was then published to `output/latest/`. `release-status.json` reports `complete_pair: true` and the shared commit.
- **Verification:** `tools/release_artifacts.py verify` passed for both architecture/manifest pairs. Embedded build metadata reports `source_dirty: false`; pipeline checks inspected kernel, initrd, rootfs and GRUB configuration. Runtime remains unvalidated: no UTM boot, screenshots, networking, AI interaction or Calamares installation is claimed.
- **Automated checks:** 137 tests passed, 5 skipped because GTK/PyQt target dependencies are unavailable on the host; the build's CTest checks passed 2/2 on each architecture. `git diff --check` and syntax checks passed. Nonfatal build notices included initramfs gzip fallback without `zstd`, SquashFS ACL xattr-prefix notices, xorriso volume-ID/MBR geometry notices, chroot apt logging/D-Bus notices and Qt locale fallback.
- **GitHub release:** Not published; `gh auth status` reports no authenticated GitHub host in this environment.


## 0.3.7 — audio backend and window controls — 2026-11-22 UTC

| Architecture | Build ID | Source commit | Build time (UTC) | Size (bytes) | SHA-256 | Build status | Runtime status |
|---|---|---|---|---:|---|---|---|
| arm64 | `ifba-20261122T135922Z-arm64-cb21dbbfe972` | `cb21dbbfe972c4f2cf5aafd300f51d308105e711` | `2026-11-22T13:59:22Z` | 2,021,965,824 | `610289958067b1dac852ccc5d4d9b79f19bfcc3506563cd3bf43cb377140af55` | built and structurally verified | unvalidated |
| amd64 | `ifba-20261122T140239Z-amd64-cb21dbbfe972` | `cb21dbbfe972c4f2cf5aafd300f51d308105e711` | `2026-11-22T14:02:39Z` | 2,080,104,448 | `1b3262f6dbe63bd4a4e35edd4a871c57bbdab5815ff9654fd092dadd9f377bcf` | built and structurally verified | unvalidated |

- **Build method:** Official `./scripts/build-iso.sh --arch arm64` and `--arch amd64` pipeline from a clean detached worktree at the shared source commit above. Each generated manifest records `source_dirty: false`.
- **Verification:** `tools/release_artifacts.py verify` passed on both staged outputs and both archived files. Independent SHA-256 and size checks match the manifests. `file` identifies both as bootable ISO 9660 DOS/MBR media; the build extracted and checked architecture-specific kernel, initrd, SquashFS and GRUB boot data. These checks do not establish a successful guest boot or runtime behavior.
- **Warnings:** Both builds completed with exit status 0. Nonfatal notices included SquashFS `system.posix_acl_*` xattr prefixes and `xorriso` ISO volume-ID normalization/MBR geometry adjustment. The AMD64 chroot build also reported Qt changing locale `C` to `C.UTF-8`; ARM64 initramfs used gzip because `zstd` was unavailable. AMD64 internal CTest checks passed 2/2.
- **Artifacts:** Archived under `output/versions/v0.3.7/{arm64,amd64}/`. The v0.3.6 `output/latest/` pointers and `release-status.json` were deliberately left untouched: UTM showed a running historical VM with a v0.3.6 ISO filename, but its backing image path could not be established from the VM configuration. This preserves the possibly attached file; v0.3.7 is built and archived but is not the current `latest` pointer.
- **UTM/runtime:** No v0.3.7 guest was booted and no screenshots were captured. Audio playback, YouTube, window decorations, IFBA AI controls, desktop layout, network and Calamares remain unvalidated on these images. Existing UTM VMs were not stopped, reconfigured or modified.
- **GitHub release:** Not published in this build session; check the current `gh` authentication state before uploading assets.


## 0.3.8 — VSCodium replaces Thonny — 2026-11-22 UTC

| Architecture | Build ID | Source commit | Build time (UTC) | Size (bytes) | SHA-256 | Build status | Runtime status |
|---|---|---|---|---:|---|---|---|
| arm64 | `ifba-20261122T143449Z-arm64-c9ec60405f4c` | `c9ec60405f4c0a560210cae34991c1354ced49e3` | `2026-11-22T14:34:49Z` | 2,151,831,552 | `01b5cbe0938fb186588d699aeb16e01f38885da68e19e7d9afbe3a1af9fed7e1` | built and structurally verified | unvalidated |
| amd64 | `ifba-20261122T143839Z-amd64-c9ec60405f4c` | `c9ec60405f4c0a560210cae34991c1354ced49e3` | `2026-11-22T14:38:39Z` | 2,219,005,952 | `d41b9a4b0b5acd6933477bc6c3362bb88f469391d36609d65863f4b4e34cd2dc` | built and structurally verified | unvalidated |

- **Build method:** Official `./scripts/build-iso.sh --arch arm64` and `--arch amd64` from clean detached worktree commit `c9ec60405f4c0a560210cae34991c1354ced49e3`; both manifests record `source_dirty: false` and version 0.3.8.
- **VSCodium:** Both rootfs builds installed VSCodium `1.143.17232`, verified the official repository key fingerprint and architecture-specific package SHA-256 from signed APT metadata, confirmed the real `com.visualstudio.CodeOSS.desktop` launcher, and removed any cached Thonny package. The project tests also verify these build contracts.
- **Verification:** Both `release_artifacts.py verify` checks passed; `file` identifies architecture-specific bootable ISO 9660 DOS/MBR images, and the pipeline extracted kernel, initrd, SquashFS and GRUB files. Per-ISO `.sha256` files are in each version directory. This does not prove guest boot or runtime.
- **Tests:** The complete host suite passed 142 tests with 6 target-GTK/PyQt skips. Shell syntax, Python compilation, design-system generated-file check and `git diff --check` passed. Both architecture builds passed their rootfs assertions and internal CTest checks (2/2 each).
- **Warnings:** Nonfatal `mksquashfs` ACL xattr-prefix and `xorriso` volume-ID/MBR geometry notices; Qt changed the AMD64 container locale from `C` to `C.UTF-8`; both initramfs builds used gzip because zstd was unavailable; AMD64 cleanup noted `/dev/pts` was not mounted for apt logging.
- **Local artifacts:** `output/versions/v0.3.8/{arm64,amd64}/`. `output/latest/` was not changed because the active historical ARM64 UTM VM has an unresolved v0.3.6 image path. Inspection also found that `output/latest/amd64/` has a manifest but no ISO, so its old `release-status.json` claim of `complete_pair: true` was corrected to false. No existing VM media was changed.
- **GitHub Release:** Not published. Both ISOs exceed GitHub's 2 GiB per-file release asset limit: ARM64 is 2,151,831,552 bytes and AMD64 is 2,219,005,952 bytes. No partial release was created. The source and local artifacts remain available at the paths above.
- **UTM:** Neither v0.3.8 image was booted; no screenshot or audio/YouTube, VSCodium launch, network, or Calamares runtime result is claimed.
