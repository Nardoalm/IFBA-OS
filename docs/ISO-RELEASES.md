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

## Next product version

No next artifact has been built or assigned a version. Increment `SYSTEM_VERSION` in `tools/build_metadata.py` as part of the next evidence-based product change, commit the build inputs, and add a new immutable entry here after recording the resulting artifact metadata.
