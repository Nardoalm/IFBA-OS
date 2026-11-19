# IFBA OS project roadmap

`DONE` means implementation has evidence in this repository or a recorded runtime check. A mock, screenshot, or package candidate alone does not prove a system feature is operational.

## Current implementation

- [ ] **IN_PROGRESS · P0** Ubuntu 24.04 amd64 live image with Casper, Linux kernel, XFCE, LightDM, Xorg, NetworkManager, Mozilla Firefox DEB, and an automatic live-session user. Corrective ISO `08949f17d8ebd2f676c8b99db18826df048fa6eaa9828f93ce01ec24179f3b07` is attached in UTM; GRUB renders and the custom splash appeared, then UTM reported inactive/black display output. Failure is after GRUB, but its cause is unresolved; no desktop or guest-agent response. Diagnose before marking usable.
- [x] **DONE · P1** Native XFCE desktop configuration for Yaru Dark, Yaru icons, Inter, restrained green GTK3 accent, Xfwm4 built-in compositing, top greeting/date panel, bottom launcher/task/tray panel, workspace pager, and Super-key menu/window controls.
- [ ] **IN_PROGRESS · P0** Native SUAP and AVA desktop links use public HTTPS URLs; the rebuilt ISO sets Firefox as default. Confirm link launching and HTTPS after the LightDM startup issue is resolved, without logging in.
- [ ] **IN_PROGRESS · P0** Verify the native desktop in UTM. The exact selected wallpaper is in the ISO's Xfdesktop and Plymouth paths, but the latest boot showed GRUB and the custom splash before UTM reported inactive/black display output. TTY and guest-agent diagnostics did not yield logs. Confirm boot, LightDM, desktop wallpaper/panels, Firefox, network/audio, and shutdown.
- [x] **DONE · P2** Keep the Electron welcome-screen prototype separate in `app/`; it is not included or auto-launched by the native XFCE ISO.
- [x] **DONE · P2** Maintain an educational package candidate list at `config/educational-apps.json`. It is not installed or connected to an installer.
- [x] **DONE · P2** Use user-supplied SUAP and EaD IFBA images for launcher tiles. This does not establish authorization for institutional endorsement.
- [ ] **IN_PROGRESS · P1** Native GTK assistant, per-user D-Bus service, private XDG/SQLite storage, Secret Service, NVIDIA SSE text streaming, bounded context, cancellation, visual guidance, schema-v2 educational memory controls, retention/export, and typed user-initiated tools are implemented in source. UI now has five model choices and Off/Low/Medium/High reasoning settings with endpoint-specific payload adapters. Raw `reasoning_content` is deliberately discarded; unrestricted model control is not implemented. GTK/keyring/API/VM runtime checks remain unverified.
- [ ] **IN_PROGRESS · P0** The top panel says `Olá, [nome]!` and falls back to `Olá, estudante!`; real matrícula login remains blocked by the shared passwordless live account and the lack of an installer or authorized account-provisioning service.

## What comes from Linux Educacional

- No code, packages, desktop configuration, or assets have been copied from Linux Educacional (including a UFPR-associated version) into IFBA OS.
- The only related project idea so far is a curated catalogue of optional educational applications. The current candidate list is maintained in this repository and is not evidence of imported LE content.
- [ ] **TODO · P1** Research and document exact LE/UFPR releases, provenance, package manifests, and licenses before adopting any specific component.

## Remaining checklist

### Base system and release engineering

- [ ] **TODO · P0** Define supported devices/CPU, RAM/storage minimums, boot firmware, graphics, Wi-Fi, audio, and display-resolution matrix.
- [ ] **TODO · P0** Complete repeatable VM checks for boot menu, desktop startup, wallpaper, panel, welcome application, app menu, file manager, browser, terminal, network, audio, shutdown, and reboot.
- [ ] **TODO · P1** Choose a supported installer and safe partition/recovery workflow. The current ISO is live-only and has no installer.
- [ ] **TODO · P1** Define updates, persistence, account creation, recovery, backups, and rollback.
- [ ] **TODO · P1** Pin Ubuntu archive snapshots/build dependencies and produce checksums and a package manifest.
- [ ] **TODO · P2** Verify UEFI/BIOS behavior and test install/update/recovery on disposable virtual disks.

### Desktop and applications

- [ ] **IN_PROGRESS · P0** Diagnose the post-GRUB inactive video output using guest logs, then boot the rebuilt image to XFCE and confirm the supplied wallpaper, native top greeting/date panel, bottom panel, and SUAP/AVA links render together without an Electron dashboard.
- [ ] **IN_PROGRESS · P1** Package the exact user-provided image as both desktop wallpaper and custom Plymouth artwork; rebuild initramfs and verify the boot-to-desktop transition in UTM. The ISO image bytes match the source, and the custom Plymouth splash appeared, but desktop display is blocked by LightDM not starting.
- [ ] **TODO · P1** Confirm the IFBA-icon Whisker menu opens by click and Super/Windows key; verify launchers at 1366×768 and 1920×1080, task switching, workspace pager, and keyboard-only access.
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

- [ ] **IN_PROGRESS · P1** Verify assistant chat, settings/data-management windows, service startup, Secret Service behavior, tools, and per-user paths inside a rebuilt live ISO. Current UTM boot did not reach XFCE. The live account remains shared and passwordless; do not enter real student credentials.
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

## Latest corrective slice — 2026-11-18

- Offline tests pass (48 total). UTM confirms the exact ISO path, renders GRUB, and displayed the custom splash, then reported inactive/black video output. A virtual-terminal switch did not provide readable logs; QEMU Guest Agent did not respond. Root cause is unresolved and the desktop, wallpaper rendering, Firefox profile, network, and assistant launch are not runtime-verified. See the follow-up observation in `docs/VM-TESTING.md`.
- The model UI contains the five requested families. Endpoint IDs/options are adapted to current NVIDIA references rather than sending identical unsupported parameters to every family. The UI streams answer text only and discards private `reasoning_content`. The model cannot arbitrarily operate the OS; typed local tools remain user-initiated and bounded.
- This is not completion of the broader Part 2 prompt. Installer, persistent individual student accounts, software installation, complete desktop feature set, live API call, and integrated secure system control remain open.

## Known limits

- The OS is a prototype live ISO based on Ubuntu 24.04 amd64, not a finished installable distribution.
- The app-selection catalogue does not install software. Shared installation across accounts is not implemented.
- SUAP and AVA open public HTTPS sites; academic data is not integrated.
- The native GTK assistant, per-user credential/data foundation, NVIDIA text streaming, consent-based visual guidance, educational memory controls, and safe user-initiated system tools are present in source. No authenticated live model request or visual desktop integration has been tested.
- The current live ISO's single passwordless `ubuntu` account is not suitable for multiple students; matrícula login and user isolation require a proper installer/provisioning policy.
- The IFBA-branded artwork is provisional, and institutional endorsement has not been established.
