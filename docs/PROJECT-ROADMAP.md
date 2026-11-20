# IFBA OS project roadmap

`DONE` means implementation has evidence in this repository or a recorded runtime check. A mock, screenshot, or package candidate alone does not prove a system feature is operational.

## Current implementation

- [ ] **IN_PROGRESS · P0** The detailed audit matrix in [`FINAL-AUDIT.md`](FINAL-AUDIT.md) retains the 0.1.1/XFCE evidence; its KDE runtime update records the latest 0.2.1 desktop. Plasma app/network behavior, guest build ID, persistence and shutdown/restart remain unverified. Track every image in [`ISO-RELEASES.md`](ISO-RELEASES.md).

- [ ] **IN_PROGRESS · P0** Latest built artifacts remain Ubuntu 26.04/Plasma 6.6 amd64 ISO 0.2.1. UTM visibly reaches Plasma with supplied wallpaper, AVA/IFBA AI/SUAP shortcuts, and one pale centered panel. Multiarchitecture builder inputs are being implemented for amd64 and arm64; no ARM64 ISO or VM boot is validated yet. App and network behavior remain unverified.
- [ ] **IN_PROGRESS · P0** Embedded build metadata, guest `ifba-os-version`, external final ISO SHA-256 manifest, and fail-fast rootfs checks are implemented. Version 0.1.0 and its matching host manifest are verified; the guest reached a shell, but guest identity command remains unverified.
- [ ] **IN_PROGRESS · P0** The legacy XFCE defaults declare one lower panel/workspace and are preserved in `legacy/xfce4`. The active KDE source defines a one-time native Plasma first-run layout. ISO 0.2.1 visibly starts Plasma and shows one bottom panel; its intended styling and workspace count are not validated.
- [ ] **IN_PROGRESS · P1** The new builder packages an IFBA OS Dark KDE color scheme and native Plasma global-theme layout. Window decorations, system settings appearance, icons, splash/login styling, animations, accessibility, GTK/KDE consistency, and actual app/window appearance remain to be reviewed in UTM.
- [ ] **IN_PROGRESS · P0** Native SUAP and AVA desktop links use public HTTPS URLs; the rebuilt ISO sets Firefox as default. Confirm link launching and HTTPS in the current graphical session, without logging in.
- [ ] **IN_PROGRESS · P0** Plasma ISO 0.2.1 now reaches the desktop in UTM. Collect guest build ID, network/route/DNS/HTTPS, Firefox and IFBA AI launch, and restart evidence without using personal credentials. Do not count visually present panel items or shortcuts as proof their actions work.
- [ ] **IN_PROGRESS · P0** Add matching ARM64 build and UTM test path without replacing the existing AMD64 VM or ISO. Both architectures must produce native package sets, architecture-accurate metadata, bootloader media and their own runtime evidence.
- [x] **DONE · P2** Keep the Electron welcome-screen prototype separate in `app/`; it is not included or auto-launched by the native XFCE ISO.
- [x] **DONE · P2** Maintain an educational package candidate list at `config/educational-apps.json`. It is not installed or connected to an installer.
- [x] **DONE · P2** Use user-supplied SUAP and EaD IFBA images for launcher tiles. This does not establish authorization for institutional endorsement.
- [ ] **IN_PROGRESS · P1** Native GTK assistant, per-user D-Bus service, private XDG/SQLite storage, Secret Service, NVIDIA SSE streaming, bounded context, cancellation, visual guidance, learning-memory controls and typed user-initiated tools remain in source. The KDE migration now routes its approved Settings action to a fixed KDE app-ID allowlist while retaining XFCE behavior. GTK/keyring/API/VM runtime checks remain unverified.
- [ ] **IN_PROGRESS · P0** The top panel says `Olá, [nome]!` and falls back to `Olá, estudante!`; real matrícula login remains blocked by the shared passwordless live account and the lack of an installer or authorized account-provisioning service.

## What comes from Linux Educacional

- No code, packages, desktop configuration, or assets have been copied from Linux Educacional (including a UFPR-associated version) into IFBA OS.
- The only related project idea so far is a curated catalogue of optional educational applications. The current candidate list is maintained in this repository and is not evidence of imported LE content.
- [ ] **TODO · P1** Research and document exact LE/UFPR releases, provenance, package manifests, and licenses before adopting any specific component.

## Remaining checklist

### KDE Plasma migration

- [x] Preserve the last XFCE implementation at local branch `legacy/xfce4` (`4c09ec5`); keep active work on `development`.
- [x] Verify package availability in official Ubuntu 26.04 LTS amd64 repositories; select Ubuntu 26.04 LTS and Plasma 6.6 as the migration target.
- [x] Add an isolated Ubuntu 26.04 LTS/Plasma 6.6 build recipe using official `resolute` repositories, separate rootfs cache and versioned output path.
- [x] Add build declarations for Plasma/KWin/SDDM, Dolphin, Konsole, Discover, System Settings, network/audio widgets, X11 and Wayland session packages.
- [x] Package the supplied wallpaper, IFBA dark green color scheme, native global theme, one-time first-run panel/workspace layout, and IFBA AI launcher; runtime application is still unverified.
- [x] Build the version 0.2.1 ISO with the corrected X11 SDDM session; UTM visibly reaches the Plasma desktop.
- [ ] Verify in UTM the single floating lower panel, menu, task switching, KRunner, wallpaper, AI app and one initial workspace.
- [ ] Validate Wayland on UTM and retain X11 as a fallback only if its actual session is available and works. Current live profile is configured for X11 to reduce VM compatibility risk; the Wayland packages are installed by the source build recipe.
- [ ] Test SDDM, Firefox, IFBA AI, NetworkManager, SUAP/AVA launchers, screen-reader/keyboard paths, persistence and recovery in UTM.
- [x] Product version `0.2.1` is built from commit `cc43d4e`; hash, package/session inspection and UTM desktop observation are recorded in `ISO-RELEASES.md`.

### Multiarchitecture and performance

- [x] Add one `--arch amd64|arm64` build interface, isolated ARM64 rootfs/cache, architecture-specific archive, bootloader, output filename, build ID and embedded architecture field while preserving the existing AMD64 cache and default command.
- [ ] Build version 0.3.0 for ARM64, verify UEFI ARM64 payload and boot the new image in a separate native UTM VM.
- [ ] Build a distinct later version for AMD64 and confirm the existing AMD64 pathway still resolves/builds and the existing VM/artifacts are preserved.
- [ ] Measure comparable boot, idle CPU/RAM, Dolphin, Firefox, IFBA AI and responsiveness on emulated AMD64 and virtualized ARM64. Do not infer performance from architecture alone.
- [ ] Validate network/DHCP/DNS/HTTPS, Firefox and IFBA AI in guest sessions before marking them functional.

### Base system and release engineering

- [ ] **TODO · P0** Define supported devices/CPU, RAM/storage minimums, boot firmware, graphics, Wi-Fi, audio, and display-resolution matrix.
- [ ] **TODO · P0** Complete repeatable VM checks for boot menu, wallpaper, panel/menu interaction, welcome application, file manager, browser, terminal, network, audio, shutdown, and reboot. ISO 0.2.1 proves desktop startup and visually confirms wallpaper and panel only.
- [ ] **TODO · P1** Choose a supported installer and safe partition/recovery workflow. The current ISO is live-only and has no installer.
- [ ] **TODO · P1** Define updates, persistence, account creation, recovery, backups, and rollback.
- [ ] **TODO · P1** Pin Ubuntu archive snapshots/build dependencies and produce checksums and a package manifest.
- [ ] **TODO · P2** Verify UEFI/BIOS behavior and test install/update/recovery on disposable virtual disks.

### Desktop and applications

- [ ] **IN_PROGRESS · P0** Verify the supplied wallpaper, menu, and SUAP/AVA launchers in the live session. Current UTM screenshot confirms wallpaper rendering, desktop shortcuts, and a single bottom panel; menu and launcher actions remain untested.
- [ ] **IN_PROGRESS · P1** Package the exact user-provided image as both desktop wallpaper and custom Plymouth artwork; verify boot-to-desktop transition and wallpaper persistence. The image bytes match the source, the splash appeared, and the current UTM screenshot shows it on the desktop; restart persistence and lower-resolution readability remain untested.
- [ ] **TODO · P1** Confirm the IFBA-icon Whisker menu opens by click and Super/Windows key; verify launchers at 1366×768 and 1920×1080, task switching, and keyboard-only access. The workspace pager is intentionally omitted while the default is one workspace.
- [ ] **TODO · P1** Inspect Thunar, terminal, Firefox, XFCE Settings Manager, notification dialogs, LightDM greeter, and system dialogs for theme consistency and functional controls.
- [ ] **TODO · P2** Evaluate XFWM4's built-in compositor on software-rendered and accelerated VM/physical hardware; keep a user-accessible off switch. Do not add Picom alongside XFWM4.
- [ ] **TODO · P2** Document unavailable effects (window open/minimize animations and background blur) unless a stable, accessible, low-resource solution is proven.
- [ ] **TODO · P1** Add genuine first-start onboarding and optional app checkboxes; communicate disk use, availability, and licensing.
- [ ] **TODO · P1** Implement shared system package installation once for all local users, with explicit confirmation, progress/errors, privilege separation, and rollback.
- [ ] **TODO · P2** Add localization, accessibility/screen-reader checks, settings, and user preference management.

### SUAP, AVA, and academic data

- [x] **DONE · P2** Open the public SUAP and AVA HTTPS destinations as ordinary links; no login automation, cookies, scraping, or private endpoints.
- [ ] **TODO · P1** Test external browser launching without signing in.
- [ ] **BLOCKED · P1** Read calendars, grades, coursework, or other academic information only after written IFBA/DGTI approval and documented authorized interfaces.

### Optional AI assistant

- [ ] **IN_PROGRESS · P1** Verify assistant chat, settings/data-management windows, service startup, Secret Service behavior, tools, and per-user paths inside the live ISO. The current desktop shows an IFBA AI launcher and the optional-setup notification, but its windows and service have not been opened or tested. The live account remains shared and passwordless; do not enter real student credentials.
- [x] **DONE · P1** Implement a Secret Service adapter and fail-closed behavior for missing/locked keyrings; no key is stored in plaintext.
- [x] **DONE · P1** Implement restrictive XDG directories, schema-versioned SQLite conversations/messages/memory, validated settings, and automated isolation/permission tests.
- [ ] **IN_PROGRESS · P1** Implement an NVIDIA NIM client and GTK conversation workflow, streaming, cancellation, bounded retries/context, endpoint-specific model/reasoning adapters, and network error handling. Mocked tests pass; API availability, key entitlement, payload compatibility, and visual guidance remain unverified without an authenticated request.
- [ ] **IN_PROGRESS · P1** Add selectable X11 windows, bounded AT-SPI context, explicit capture consent and preview, a documented image-capable NVIDIA route, strict structured-response validation, and a temporary click-through outline. Tests use mocks; desktop runtime is unverified.
- [ ] **IN_PROGRESS · P1** Add local conversation summaries, bounded context controls, opt-in editable learning memories, lexical retrieval, retention, export/deletion, and typed local tools requiring GTK initiation and one-shot file-creation confirmation. Automated tests pass; XFCE/D-Bus runtime is unverified.
- [ ] **TODO · P1** Watch focus/move/resize changes, offer selected-region capture, track tutorial state changes, and exercise the full guided workflow in Eclipse or a GTK test application.
- [ ] **TODO · P1** Define operation-specific consent, visible screen sharing, confirmation before system changes, model/provider errors, rate/cost controls, and privacy retention.
- [ ] **TODO · P2** Implement chat and educational walkthroughs only after the threat model and provider terms are reviewed. No AI is currently connected and no agent has unrestricted system control.

### Identity, legal, and project health

- [ ] **BLOCKED · P1** Use an official IFBA mark in a distributed build only when supplied with authorization. The generated mark currently in the prototype is provisional and must not be represented as official.
- [ ] **TODO · P1** Audit all package licenses, asset sources/permissions, attribution, and redistribution obligations.
- [ ] **TODO · P1** Review security boundaries, local data handling, update authenticity, and build-script privilege use.
- [ ] **TODO · P2** Add relevant automated checks, contribution guide, user documentation, changelog, issue templates, and support policy.
- [ ] **TODO · P2** Prepare signed/checksummed releases only after installer, legal, hardware, and security criteria pass.

## Earlier corrective slice — 2026-11-18

- Earlier ISO `08949f17d8ebd2f676c8b99db18826df048fa6eaa9828f93ce01ec24179f3b07`: UTM confirmed its path, rendered GRUB and custom splash, then reported inactive/black output. The cause is unresolved. Latest XFCE defaults are statically corrected and rebuilt as ISO `6d320c44992edd02f3fe645c7c2016517ab498d00afe7932ce84627195091580`; UTM access failed during that follow-up, so boot and desktop behavior are still unverified. The wallpaper rendering, Firefox profile, network, and assistant launch remain pending.
- The model UI contains the five requested families. Endpoint IDs/options are adapted to current NVIDIA references rather than sending identical unsupported parameters to every family. The UI streams answer text only and discards private `reasoning_content`. The model cannot arbitrarily operate the OS; typed local tools remain user-initiated and bounded.
- This is not completion of the broader Part 2 prompt. Installer, persistent individual student accounts, software installation, complete desktop feature set, live API call, and integrated secure system control remain open.

## Final audit slice — 2026-11-19

- See [`FINAL-AUDIT.md`](FINAL-AUDIT.md) for requirement-by-requirement status and acceptance tests. It explicitly distinguishes source and mock evidence from guest runtime evidence.
- Disabled the IFBA AI settings stack animation and added a regression test. No system-wide reduced-motion control exists yet.
- 55 tests pass; shell syntax, XML parsing, ISO hybrid boot metadata and expected boot files pass inspection. Extracted SquashFS contains the single-panel XFCE profile and the no-transition assistant source.
- Latest ISO hash is recorded above. UTM window access (`cgWindowNotFound`) and `utmctl` Automation denial (`OSStatus -1743`) prevent testing this exact image in the guest.
- The installer/multiuser login, system-wide animation settings, finished visual identity, global search, verified network/Firefox/AI runtime, accessibility, performance baselines and full application workflow remain incomplete or untested.

## Known limits

- The OS is a prototype live ISO based on Ubuntu 24.04 amd64, not a finished installable distribution.
- The app-selection catalogue does not install software. Shared installation across accounts is not implemented.
- SUAP and AVA open public HTTPS sites; academic data is not integrated.
- The native GTK assistant, per-user credential/data foundation, NVIDIA text streaming, consent-based visual guidance, educational memory controls, and safe user-initiated system tools are present in source. No authenticated live model request or visual desktop integration has been tested.
- The current live ISO's single passwordless `ubuntu` account is not suitable for multiple students; matrícula login and user isolation require a proper installer/provisioning policy.
- The IFBA-branded artwork is provisional, and institutional endorsement has not been established.
