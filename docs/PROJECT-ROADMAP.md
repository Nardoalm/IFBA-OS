# IFBA OS project roadmap

`DONE` means implementation has evidence in this repository or a recorded runtime check. A mock, screenshot, or package candidate alone does not prove a system feature is operational.

## Current implementation

- [ ] **IN_PROGRESS · P0** Final audit matrix is maintained in [`FINAL-AUDIT.md`](FINAL-AUDIT.md). The project channel was missing Ubuntu's Failsafe definition, a configuration defect consistent with the observed failsafe-session error; it is restored and the ISO rebuilt. The exact new ISO transitions from splash to the dark wallpaper, but no desktop controls appear, so session startup remains unresolved.

- [ ] **IN_PROGRESS · P0** Ubuntu 24.04 amd64 live image with Casper, Linux kernel, XFCE, LightDM, Xorg, NetworkManager, Mozilla Firefox DEB, and an automatic live-session user. Current ISO SHA-256 is `3022cef8989f8052dec5268c1c86b94f762e504e34ca0dd82726338be6e2a658`. Exact-image UTM evidence is in `VM-TESTING.md`: splash and wallpaper render but the panel/menu/greeter controls do not appear. The failsafe channel defect is fixed; full desktop boot remains unverified.
- [ ] **IN_PROGRESS · P0** XFCE defaults now declare one lower panel and one workspace, remove the pager, disable session auto-save, and seed the live user, XDG defaults, and `/etc/skel` from the same channels. Static regression checks pass; current-session behavior and persistence through an actual XFCE login/reboot still require a working VM boot.
- [ ] **IN_PROGRESS · P1** Native desktop uses Yaru Dark/Yaru icons, Inter, a GTK3 graphite panel with green interaction states, Xfwm4 compositing, bottom launchers/task/tray controls, and a searchable Whisker menu. It remains visually based on upstream Ubuntu Yaru; GTK2/GTK4/non-GTK consistency and actual app/window appearance have not been checked in the current ISO.
- [ ] **IN_PROGRESS · P0** Native SUAP and AVA desktop links use public HTTPS URLs; the rebuilt ISO sets Firefox as default. Confirm link launching and HTTPS after the LightDM startup issue is resolved, without logging in.
- [ ] **IN_PROGRESS · P0** Verify the native desktop in UTM. Exact wallpaper appears after Plymouth, but the VM has no usable panel/menu/greeter controls. The XFCE failsafe settings are restored in the latest ISO, but the cause of the missing controls is open. Obtain reliable serial/journal output or test another disposable VM display backend before changing boot/display settings. Then confirm panel/menu, Firefox, network/audio, and shutdown.
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

- [ ] **IN_PROGRESS · P0** Diagnose the post-GRUB inactive video output using guest logs, then boot the rebuilt image to XFCE and confirm the supplied wallpaper, single bottom panel, menu, and SUAP/AVA links render together without an Electron dashboard.
- [ ] **IN_PROGRESS · P1** Package the exact user-provided image as both desktop wallpaper and custom Plymouth artwork; rebuild initramfs and verify the boot-to-desktop transition in UTM. The ISO image bytes match the source, and the custom Plymouth splash appeared, but desktop display is blocked by LightDM not starting.
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
