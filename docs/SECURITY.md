# Security and privacy model

## Current live image warning

The current build is a live demo, not a multi-user installation: it auto-logs into a single passwordless `ubuntu` account. Files and keyrings in that session are not isolated between different people using the same live account and may be lost on reboot. Do not configure a personal NVIDIA key or real student data in that environment. A secure student-login experience requires a future installer or controlled local-account provisioning path.

The requested common first-login password `12345` must not be packaged: knowing a student's matrícula plus a shared public password would allow account takeover before password rotation. Do not represent a typed matrícula as verified identity without an authorized identity source.

## Credential handling

- Store the API key only in the current user's Secret Service collection, accessed through `secret-tool`.
- Send key input to `secret-tool` over stdin; it never appears in argv. The D-Bus service returns generic errors and does not include subprocess output in logs/UI.
- Never put credentials in JSON, SQLite, environment variables, command history, debug logs, source, test fixtures, or ISO build outputs.
- There is no plaintext fallback. Missing executable, locked keyring, service failure, or timeout makes credential operations fail closed.
- The API key entry is masked and cleared after save. The UI does not retrieve an existing key for display.

## User data isolation

- The daemon is a per-user systemd user service, not root or a shared privileged daemon.
- D-Bus calls use a per-user session bus.
- Data/config/cache directories are created with mode `0700`; the database and settings file use mode `0600`.
- SQLite uses foreign keys, parameterized queries, explicit schema versioning, and a private data path. Credentials do not belong in SQLite.
- Tests use fake keys and a mocked subprocess; no real key is part of the test suite.

## Data sent to NVIDIA

Text requests send an educational system instruction, selected learning level, model ID, output-token ceiling, and bounded recent text messages to NVIDIA NIM. Visual assistance requires selecting one local window, consenting to capture, reviewing the preview, and separately confirming upload. Only the documented `microsoft/phi-4-multimodal-instruct` endpoint accepts screenshot bytes. Images are limited to 140 KiB, kept in memory, and not written to disk or SQLite. Login/password windows are blocked when detected from title or AT-SPI2, and the preview remains the student's final privacy check. The model cannot provide coordinates; a target ID is matched against the accessible-control list and its bounds are queried again before the temporary click-through outline is displayed. The assistant never clicks or types.

HTTP requests are not logged; user-facing errors omit response bodies and credentials. No authenticated live request or real desktop capture has been tested. Window selection, capture, accessibility, and overlay need X11/AT-SPI runtime validation.

## Local service boundaries

- The D-Bus service exposes only typed configuration and conversation methods. It has no shell command, system package, user-management, or arbitrary file-operation method.
- The user service uses `NoNewPrivileges`, `ProtectSystem=strict`, `ProtectHome=read-only`, a restrictive umask, private tmp, restricted address families, and narrowly writable XDG app directories.
- Future system tools require explicit allowlists and confirmation before file modifications or privileged actions. Content from websites, documents, or screenshots is never authorization.
- Screen capture and AT-SPI access are not implemented in Stage 1.
