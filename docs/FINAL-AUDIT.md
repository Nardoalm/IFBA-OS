# IFBA OS final audit matrix

Audit date: 2026-11-19. Scope is the current source tree and `output/ifba-os-ubuntu-24.04-amd64.iso`. A source declaration or mocked test is not runtime evidence. UTM is listed as running by the host app inventory, but its window cannot be acquired (`cgWindowNotFound`) and `utmctl` is blocked from this SSH session (`OSStatus -1743`).

| Requirement | Expected | Observed evidence | Status | Priority / correction or acceptance test |
|---|---|---|---|---|
| Base and ISO | Ubuntu 24.04 amd64 live system boots to XFCE | ISO exists; 1.3 GiB, SHA-256 recorded in VM testing; GRUB/Casper contents previously inspected. Latest image has not been booted after the XFCE defaults change. | Blocked | P0: obtain UTM window/guest logs and cold boot this exact ISO. |
| Desktop wallpaper | Supplied grayscale IFBA OS image on Xfdesktop | Source asset is packaged and Xfconf default points to it; prior ISO image bytes were checked. Current desktop rendering is not confirmed. | Not tested | P0: inspect desktop after boot at 1366×768 and 1920×1080. |
| Panel | One lower XFCE panel, launchers, task list, tray, clock and session actions | Xfconf XML lists panel 1 only; a regression test checks location and pager absence; build copies the file to live user, XDG and `/etc/skel`. | Partially conforme | P0: verify real panel, each launcher, menu, network/audio indicators and reboot persistence. |
| Workspaces | One by default; user can add more | Xfwm4 default is one and is not locked; test checks both. | Partially conforme | P1: test Settings UI, user change and persistence in a booted session. |
| Panel repair | Repair only an identified duplicate panel; no recurring cleanup | Script checks non-root session, active panel 1 and bottom position; mock integration covers removing extras and pager. No real-session run. | Partially conforme | P1: run inside XFCE and validate failure paths with a backup profile. |
| Visual identity | Consistent IFBA OS design throughout desktop and applications | Yaru Dark/Yaru remain upstream themes; Inter, supplied wallpaper, panel CSS and GTK assistant styles add limited customization. GTK2/GTK4/libadwaita/non-GTK apps are not unified. | Não conforme | P1: develop and visually review a complete theme only after VM access; no official IFBA endorsement is implied. |
| Animations | Off by default; accessible interaction feedback remains | Assistant's settings stack previously cross-faded; now configured with no transition. No OS-wide animation preference or reduced-motion control exists. | Parcialmente conforme | P1: inspect XFWM/panel/GTK animation behavior and implement a truthful system-wide preference if supported. |
| Browser | Modern Firefox default, HTTPS and healthy profile | Mozilla Firefox DEB, locale package, helper, launchers and MIME handlers are configured; no current guest launch/profile/network result. NetSurf is removed from cached builds. | Not tested | P0: cold-launch Firefox, create profile, visit a public HTTPS test page, test URL dispatch and downloads. |
| Network | Accurate real state, DHCP/NAT, disconnect/reconnect | NetworkManager and a wired DHCP profile are configured; VM history showed disconnected tray state and a previous boot delayed at NetworkManager. No current IP/gateway/DNS/HTTPS evidence. | Bloqueado | P0: collect guest journal, link/IP/route/resolver state; test NAT loss and recovery. Never display fictitious Wi-Fi. |
| IFBA AI identity/UI | App/window shown as IFBA AI; controls work | Desktop entry, WM class, GTK window title and UI source are aligned. Mock tests cover HTTP/model/storage/tool paths; no GTK/D-Bus runtime or individual-button acceptance pass. | Parcialmente conforme | P1: run each listed control in XFCE, verify accessibility labels, focus and task switcher identity. |
| NVIDIA API | Authenticated supported model, streaming, errors, cancellation | Client, model registry and SSE/error paths exist; tests use mocked HTTP. No key or authenticated API request is available/authorized. | Not tested | P1: with an explicitly configured user key, test one request per entitled model; record sanitized status, never key/body. |
| Memory/privacy | Per-user isolated history and opt-in memory | SQLite schema, permissions, controls and isolation tests exist in source. Live ISO is one shared passwordless account. | Parcialmente conforme | P0: do not use real student data; implement installer/account model before multi-student use. |
| System actions | Only typed, bounded, student-started operations | No model tool-calling or arbitrary shell; file creation is bounded and confirmation-gated in source/tests. Runtime paths are untested. | Parcialmente conforme | P1: exercise open app/URL/folder/create and denial/expiry paths in a disposable profile. |
| Global search | Search apps/settings/files with keyboard and offline | Whisker menu and XFCE App Finder packages/configuration exist; there is no IFBA global search service or verified launcher shortcut. | Não conforme | P1: define scope and add keyboard-first app/settings search; keep file search local and permission-bounded. |
| Multitasking | Window switching, snap, resize and task indicators | XFWM keybinding XML configures Super+arrows and switching; actual windows were not tested. | Not tested | P1: open Firefox, Thunar, Terminal and IFBA AI; test focus, snap, minimize, maximize and close. |
| Settings/control center | Controls read/write actual system state | XFCE settings packages and panel controls are included; no unified IFBA Control Center exists. | Parcialmente conforme | P1: test each native dialog and document controls not present in VM hardware. |
| Files | Thunar common file operations | Thunar is installed by the build recipe; no live operation was validated. AI file access remains user-selected/limited in source. | Not tested | P1: create/copy/move/rename/delete/restore/open/drag files in a disposable home. |
| Installer and login | Installable OS and separate student accounts | ISO is live-only and auto-logs into shared passwordless `ubuntu`; no installer or trusted IFBA identity provisioner. | Não conforme | P0: decide installer and account provisioning; never ship shared `12345`. |
| Accessibility | Keyboard, contrast, scaling, screen-reader and reduced motion | Some native GTK focus/hover styles and keyboard bindings exist; no end-to-end AT-SPI, screen reader, contrast, scaling or reduced-motion audit. | Not tested | P1: run GTK/AT-SPI and keyboard passes at common VM sizes. |
| Performance | Measured boot, idle, launch and AI latency | No comparable timing/RAM/CPU dataset is present. | Not tested | P2: capture baseline only after reliable boot, with VM CPU/RAM configuration noted. |
| Plymouth/LightDM | Branded boot to graphical login/desktop | Artwork and config are packaged; previous UTM observations were inconsistent and latest image is unbooted. | Blocked | P0: verify exact ISO splash, LightDM and desktop handoff; collect system journal for stalls. |
| Legal/package integrity | Licensed assets/packages and authorized branding | Build uses Ubuntu/Mozilla repositories and supplied/generated assets; no complete SBOM/license or logo authorization record. | Parcialmente conforme | P1: add package manifest, asset provenance and redistribution review before distribution. |
| ISO reproducibility | Repeatable pinned build and verified output | Build script and Docker cache produce a bootable ISO, but apt archives are not snapshot-pinned; output hash changes over time. | Parcialmente conforme | P1: pin repository snapshots/package manifest and verify rebuilt artifacts against recorded inputs. |

## Corrections in this audit slice

- Disabled the IFBA AI settings stack's cross-fade so the app respects the requested no-animation default for this transition. This does not disable animations across all XFCE applications.
- Added a regression check for the assistant transition setting.
- Existing XFCE panel/workspace repair and ISO changes are recorded in the preceding Iteration 9 and the project roadmap; they are not reclassified as runtime-verified here.

## Runtime boundary

No latest-image VM acceptance scenario was completed: UTM has no accessible window in the computer-use surface, while `utmctl` reports macOS Automation denial from the SSH execution context. The guest was not altered. Static package inspection, unit tests, and an ISO file check cannot validate desktop appearance, real networking, Firefox profile startup, GTK accessibility, or user-session persistence. See `VM-TESTING.md` for boot history and next concrete checks.

## Final artifact for this audit

- ISO: `output/ifba-os-ubuntu-24.04-amd64.iso`
- SHA-256: `9f6553df2575c710dac809c5a5d28aacdaa949056d2fb059927bc76ff4c9dffe`
- Size: 1,367,744,512 bytes.
- Artifact checks: bootable ISO9660 DOS/MBR structure, IFBA volume label, GRUB config, Casper kernel/initrd, and SquashFS entries.
- Automated evidence: 55 tests pass; shell syntax and packaged XML parsing pass.
- Guest evidence: none for this exact ISO; it is not VM-validated.
