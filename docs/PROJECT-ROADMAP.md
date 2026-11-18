# IFBA OS project roadmap

`DONE` means implementation has evidence in this repository or a recorded runtime check. A mock, screenshot, or package candidate alone does not prove a system feature is operational.

## Current implementation

- [x] **DONE · P1** Ubuntu 24.04 amd64 live image with Casper, Linux kernel, XFCE, LightDM, Xorg, NetworkManager, NetSurf, and an automatic live-session user.
- [x] **DONE · P1** Electron desktop home prototype with wallpaper, greeting/date, SUAP and AVA public HTTPS shortcuts, campus identity, truthful empty activities state, and an AI orb explaining that AI is not connected.
- [x] **DONE · P1** Electron security baseline: sandbox, context isolation, no Node integration in the renderer, blocked in-app navigation, and allowlisted SUAP/AVA external links.
- [ ] **IN_PROGRESS · P0** Deliver the Electron home, working default-browser path, panel/dock, and wallpaper together in the booted live desktop. See `docs/VM-TESTING.md`; current changes still require a fresh VM boot.
- [x] **DONE · P2** Maintain an educational package candidate list at `config/educational-apps.json`. It is not installed or connected to an installer.
- [x] **DONE · P2** Use user-supplied SUAP and EaD IFBA images for launcher tiles. This does not establish authorization for institutional endorsement.

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

- [ ] **TODO · P0** Boot the current build and confirm the Electron page, CSS, supplied portal logos, exact supplied wallpaper (with embedded 3D wordmark), and bottom panel render together.
- [ ] **TODO · P1** Confirm the IFBA-icon Whisker menu opens by click and Super/Windows key; verify dock launchers at 1280×720 and 1920×1080, task switching, and keyboard-only access.
- [ ] **TODO · P1** Add genuine first-start onboarding and optional app checkboxes; communicate disk use, availability, and licensing.
- [ ] **TODO · P1** Implement shared system package installation once for all local users, with explicit confirmation, progress/errors, privilege separation, and rollback.
- [ ] **TODO · P2** Add localization, accessibility/screen-reader checks, settings, and user preference management.

### SUAP, AVA, and academic data

- [x] **DONE · P2** Open the public SUAP and AVA HTTPS destinations as ordinary links; no login automation, cookies, scraping, or private endpoints.
- [ ] **TODO · P1** Test external browser launching without signing in.
- [ ] **BLOCKED · P1** Read calendars, grades, coursework, or other academic information only after written IFBA/DGTI approval and documented authorized interfaces.

### Optional AI assistant

- [ ] **TODO · P1** Build account/onboarding UI that lets the student configure an NVIDIA API key or skip AI entirely.
- [ ] **TODO · P1** Store credentials per user in the OS secure credential store; never embed keys in the ISO, package, or repository.
- [ ] **TODO · P1** Define consent, visible screen sharing, limited actions, confirmation before system changes, model/provider errors, rate/cost controls, and privacy retention.
- [ ] **TODO · P2** Implement chat and educational walkthroughs only after the threat model and provider terms are reviewed. No AI is currently connected and no agent has unrestricted system control.

### Identity, legal, and project health

- [ ] **BLOCKED · P1** Use an official IFBA mark in a distributed build only when supplied with authorization. The generated mark currently in the prototype is provisional and must not be represented as official.
- [ ] **TODO · P1** Audit all package licenses, asset sources/permissions, attribution, and redistribution obligations.
- [ ] **TODO · P1** Review security boundaries, local data handling, update authenticity, and build-script privilege use.
- [ ] **TODO · P2** Add relevant automated checks, contribution guide, user documentation, changelog, issue templates, and support policy.
- [ ] **TODO · P2** Prepare signed/checksummed releases only after installer, legal, hardware, and security criteria pass.

## Known limits

- The OS is a prototype live ISO based on Ubuntu 24.04 amd64, not a finished installable distribution.
- The app-selection catalogue does not install software. Shared installation across accounts is not implemented.
- SUAP and AVA open public HTTPS sites; academic data is not integrated.
- The AI orb is explanatory UI only; there is no API connection, account setup, key storage, or system-control agent.
- The IFBA-branded artwork is provisional, and institutional endorsement has not been established.
