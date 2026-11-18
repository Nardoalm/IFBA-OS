# IFBA OS project roadmap

Statuses describe evidence in this repository, not intent. `DONE` means the stated acceptance evidence exists; a UI mock or a file alone is not proof of an operational system feature.

## A. Foundation and architecture

- [x] **DONE · P1** Document the initial Ubuntu/XFCE direction and project boundaries. Acceptance: decisions and safety constraints are in `AGENTS.md` and `docs/DECISIONS.md`.
- [ ] **TODO · P1** Define release architecture and supported hardware. Depends on target-device research. Acceptance: documented CPU, boot, memory, and support matrix.
- [ ] **TODO · P2** Make ISO builds reproducible from a pinned Ubuntu snapshot. Acceptance: documented source snapshot and repeatable artifact verification.
- [ ] **TODO · P2** Add third-party license and attribution inventory. Acceptance: every shipped package and visual asset has a recorded license/source.

## B. Operating system and live environment

- [x] **DONE · P1** Assemble an amd64 Ubuntu 24.04 live ISO with Casper, XFCE, LightDM, NetworkManager, and kernel. Evidence: ISO exists and its SquashFS was inspected.
- [x] **DONE · P0** Reach the XFCE live desktop in UTM. Evidence: desktop panel, Home icon, and welcome-page shortcut appeared after explicitly including Xorg and `xinit`.
- [ ] **IN_PROGRESS · P0** Complete the live-session validation. The desktop boots, but the wallpaper appeared as a solid background and launcher/network/shutdown checks remain unverified; see `docs/VM-TESTING.md`.
- [ ] **TODO · P1** Verify networking, audio, display resizing, suspend, shutdown, and reboot. Depends on successful VM boot.
- [ ] **TODO · P2** Verify localization, keyboard layouts, accessibility and screen-reader basics.
- [ ] **TODO · P2** Define user creation, session security, and persistence policy.

## C. Visual identity

- [x] **DONE · P2** Include the generated graphite wallpaper in the image. Evidence: wallpaper paths exist in the SquashFS.
- [ ] **IN_PROGRESS · P2** Verify the wallpaper and welcome page in a VM. XFCE panel and desktop icons appeared; wallpaper did not render on the observed boot, and launcher interaction is pending.
- [ ] **BLOCKED · P2** Replace the provisional IFBA mark with official artwork. Blocker: no authorized official artwork has been supplied.
- [ ] **TODO · P3** Review typography, contrast, keyboard focus and responsive layouts.

## D. Applications and educational features

- [x] **DONE · P2** Add a reviewable educational application catalogue. Evidence: `config/educational-apps.json`.
- [ ] **IN_PROGRESS · P1** Save selected app preferences per user. Current evidence: welcome UI uses browser local storage; it does not install packages.
- [ ] **TODO · P0** Validate every package source, license, availability, disk cost and maintenance status.
- [ ] **TODO · P1** Implement package status and install/removal via a narrow privileged service. Requires threat model, explicit consent, progress/error handling and rollback.
- [ ] **TODO · P2** Add update and recovery workflows.

## E. IFBA OS application

- [ ] **IN_PROGRESS · P1** Make the welcome UI actions honest and usable. Current state: HTML/JS prototype; preferences can be saved locally, but no package backend exists.
- [ ] **TODO · P1** Decide whether Electron is the desktop shell or remains a separate prototype. Acceptance: documented runtime, packaging and support decision.
- [ ] **TODO · P1** Package a Linux amd64 Electron build reproducibly and add a menu launcher. Depends on the architecture decision.
- [ ] **TODO · P2** Add functional onboarding navigation, loading/error states, keyboard access, and localization.
- [ ] **TODO · P2** Add a settings page to review/clear local preferences.

## F. Institutional integrations

- [x] **DONE · P2** Link to public SUAP and AVA web destinations without automating access. Evidence: HTTPS anchors in `app/index.html`.
- [ ] **TODO · P1** Validate public URLs and behavior without signing in or handling private academic data.
- [ ] **BLOCKED · P1** Add data/API integration only after written IFBA/DGTI approval and documented interfaces.

## G. AI assistant

- [ ] **TODO · P2** Define use cases, provider abstraction and local-vs-remote tradeoffs.
- [ ] **TODO · P2** Build a visible, optional chat UI with mock-provider tests; label mock output as mock output.
- [ ] **TODO · P1** Design per-user credential storage, privacy controls, data minimization and explicit action consent.
- [ ] **TODO · P1** Add model access only after threat model, provider terms, budget controls, and user consent are addressed.

## H. Installation and distribution

- [ ] **TODO · P0** Select an installer and define recovery behavior. Current ISO has no installer.
- [ ] **TODO · P1** Test install to a disposable virtual disk, UEFI/BIOS boot, partitioning, updates and recovery.
- [ ] **TODO · P1** Test on supported physical hardware only after VM and safety review.
- [ ] **TODO · P2** Define ISO signing, checksums, release process and update channel.

## I. Quality and security

- [ ] **IN_PROGRESS · P1** Add repeatable validation for build scripts, HTML and renderer behavior. Current session validates shell syntax; automated UI tests are absent.
- [ ] **TODO · P1** Add unit/integration tests for app-selection persistence and error cases.
- [ ] **TODO · P1** Add ISO content manifest, checksum generation and package/license report.
- [ ] **TODO · P1** Review scripts for privilege scope, error handling and secret exposure.
- [ ] **TODO · P2** Add boot tests and diagnostics to CI when a suitable runner exists.

## J. Documentation and community

- [x] **DONE · P2** Document build and VM test procedures.
- [ ] **TODO · P2** Add contribution guide, changelog, code of conduct, user guide, issue templates and support policy.
- [ ] **TODO · P2** Prepare public releases only after identity, licenses, security, installer, and hardware support are reviewed.

## Current known limitations

- The XFCE desktop boots in the existing UTM VM, but wallpaper rendering, launcher behavior, network, and power actions have not all been verified.
- The Electron shell is not installed in the ISO; NetSurf opens the static page.
- App selections only persist in the current user's local browser storage. They do not install anything.
- The AI assistant is not connected and has no conversation or provider implementation.
- There is no installer, disk persistence, update workflow, or supported hardware matrix.
- Generated institutional branding is provisional, and institutional data integrations are absent.
