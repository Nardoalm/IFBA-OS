# Security and privacy model

## Current live image warning

The current build is a live demo, not a multi-user installation: it auto-logs into a single passwordless `ubuntu` account. The Live root filesystem carries `/etc/ifba-os/live-demo`; while that marker exists, IFBA AI refuses API-key storage/deletion, settings changes, generation, visual capture, and conversation/memory persistence. It returns built-in settings defaults without reading or creating user configuration directories or the assistant SQLite database. Calamares removes the marker from the installed target; installed users are created through its account module with autologin disabled. These protections are source-level controls and still need guest validation.

Files outside IFBA AI remain accessible to anyone using the same unlocked Live account, and session files may be lost on reboot. The marker is an accidental-use safeguard, not a boundary against a user with the Live account's administrator privileges. Keep the Live image for disposable demonstrations only; do not put personal/student files or credentials into it. A multi-user Live experience requires a separate per-person authentication and home-provisioning design.

The requested common first-login password `12345` must not be packaged: knowing a student's matrícula plus a shared public password would allow account takeover before password rotation. Do not represent a typed matrícula as verified identity without an authorized identity source.

The latest compliance status is tracked in [`FINAL-AUDIT.md`](FINAL-AUDIT.md). A current user-session/AI security review could not be performed because the latest ISO has not been booted into an accessible UTM window; static checks do not establish runtime isolation or credential behavior.

## Credential handling

- Store the API key only in the current user's Secret Service collection, accessed through `secret-tool`.
- Send key input to `secret-tool` over stdin; it never appears in argv. The D-Bus service returns generic errors and does not include subprocess output in logs/UI.
- Never put credentials in JSON, SQLite, environment variables, command history, debug logs, source, test fixtures, or ISO build outputs.
- There is no plaintext fallback. Missing executable, locked keyring, service failure, or timeout makes credential operations fail closed.
- The API key entry is masked and cleared after save. The UI does not retrieve an existing key for display.

## User data isolation

- The daemon is a per-user systemd user service, not root or a shared privileged daemon.
- The daemon is not enabled at every login. Its D-Bus activation file starts the per-user systemd unit only when IFBA AI is requested, avoiding an idle background process in sessions that do not use the assistant.
- D-Bus calls use a per-user session bus.
- Data/config/cache directories are created with mode `0700`; the database and settings file use mode `0600`.
- SQLite uses foreign keys, parameterized queries, explicit schema versioning, and a private data path. Credentials do not belong in SQLite.
- Schema v2 makes bounded local extractive conversation summaries; fragments matching obvious sensitive terms are omitted. Summaries are sent as untrusted context, not instructions.
- Long-term memory is off by default and requires a student-initiated add/edit operation. The UI supports review, correction, deletion, export, clearing, and retention. Obvious password/API-key/token/CPF/RG/matrícula/contact strings are rejected; this heuristic cannot identify every sensitive fact.
- Tests use fake keys and a mocked subprocess; no real key is part of the test suite.

## Data sent to NVIDIA

Text requests send an educational system instruction, selected learning level, model ID, output-token ceiling, and bounded recent text messages to NVIDIA NIM. Visual assistance requires selecting one local window, consenting to capture, reviewing the preview, and separately confirming upload. Only the documented `microsoft/phi-4-multimodal-instruct` endpoint accepts screenshot bytes. Images are limited to 140 KiB, kept in memory, and not written to disk or SQLite. Login/password windows are blocked when detected from title or AT-SPI2, and the preview remains the student's final privacy check. The model cannot provide coordinates; a target ID is matched against the accessible-control list and its bounds are queried again before the temporary click-through outline is displayed. The assistant never clicks or types.

HTTP requests are not logged; user-facing errors omit response bodies and credentials. No authenticated live request or real desktop capture has been tested. Window selection, capture, accessibility, and overlay need X11/AT-SPI runtime validation.

## Local service boundaries

- The D-Bus service exposes only typed configuration and conversation methods. It has no shell command, system package, user-management, or arbitrary file-operation method.
- The user service uses `NoNewPrivileges`, `ProtectSystem=strict`, `ProtectHome=read-only`, a restrictive umask, private tmp, restricted address families, and narrowly writable XDG app directories.
- Current system tools are not callable by the model. They are invoked from GTK and run as the logged-in user. The daemon remains read-only with respect to home directories; file listing/search/create runs in the GTK client and a folder is granted only for that UI session. Listing/search does not follow symlinks and has result/depth limits. File creation targets a new immediate child, uses `O_EXCL`, `O_NOFOLLOW` where available, mode `0600`, and an expiring one-use token bound to the exact plan. No tool can run a shell, install packages, or perform privileged changes.
- X11 screen capture and AT-SPI inspection exist in source, with sensitive-window checks and explicit preview/upload confirmation. Runtime behavior remains unvalidated; both features are disabled while `/etc/ifba-os/live-demo` is present.

## Distribution audit — 2026-11-21

- The current build does not vendor the audited third-party KDE theme repositories or the rejected `plasma-liquid-glass` effect. Desktop packages are fetched through Ubuntu APT; package maintainer scripts may run as root inside the build chroot as normal package installation requires. Mozilla Firefox uses a separate HTTPS APT source. The downloaded key is rejected unless its fingerprint matches `35BAA0B33E9EB396F59CA838C0BA5CE6DC6315A3`; package metadata and packages remain authenticated by APT signatures. No remote shell installer is run.
- APT inputs are **not pinned to a snapshot**: the build runs `apt-get upgrade` and resolves current `resolute`, updates, security and Mozilla packages. This supports security fixes but means source commits alone do not reproduce byte-identical builds. The artifact manifest records its build identity and hash, not an immutable repository snapshot; deterministic package locking remains open.
- The repository's root `LICENSE` does not establish redistribution rights for every supplied institutional/portal image. The official IFBA symbol and third-party portal marks need a documented asset-by-asset authorization/license inventory before public distribution. Do not infer institutional endorsement from their appearance in the UI.
- The live image still auto-logs into one passwordless shared `ubuntu` account and grants the live installer/admin path. IFBA AI now fails closed for personal credentials, screenshots, conversations and memories while the Live marker exists, but the desktop account still shares ordinary files while unlocked; the image remains unsuitable for shared or personal-data use. Calamares removes the marker and configures a separate account with autologin disabled in source; post-install isolation remains unverified in a guest.
- IFBA AI uses a per-user D-Bus/systemd service with filesystem protections and no shell interface. It now starts only upon D-Bus activation. The model can request typed, allowlisted operations; file creation needs a one-use user confirmation. These are source-level controls, not proof against a compromised local session process running as the same user.
- The authenticated NVIDIA HTTP client now rejects redirects. Python's default `urllib` handler copies request headers to redirected requests; rejecting redirects keeps the bearer key bound to the fixed API origin. No request was made during this audit.
- NVIDIA SSE input now has per-line and aggregate byte ceilings, and the assistant service independently caps accumulated response bytes before emitting or persisting further content. Focused oversized-response regressions cover the network parser and service boundary.
- `qemu-guest-agent` is installed and explicitly enabled for VM diagnostics; its runtime cost and necessity on non-VM hardware have not been measured. Do not report RAM, CPU, GPU, boot-time or animation benchmarks without collecting them on target machines.
- Current audit checks did not execute install scripts, remote code, ISO builds, Calamares, NetworkManager hardware flows or authenticated provider calls. The corresponding runtime, vulnerability-database and signing checks remain pending.
