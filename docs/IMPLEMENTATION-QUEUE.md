# IFBA OS implementation queue

This file preserves the user's requested order and the detailed AI-stage prompts. The full prompt text is archived in [`prompts/`](prompts/).

The user asked to finish the three active workstreams before starting Etapa 3: (1) native XFCE modernization, (2) student greeting/account login, and (3) Etapas 1–2 of the AI assistant. Workstream 1 is complete; 2 and 3 must finish before Etapa 3 begins.

## Order and status

1. **Native XFCE modernization — DONE.** Commit `5380c1f` is on `origin/development`. The latest ISO still needs a fresh graphical UTM boot; the prior VM run reached tty2, and the rebuilt image now selects `graphical.target`.
2. **Student greeting and local account onboarding — IN PROGRESS.** The top panel now says `Olá, [student name]!` (fall back to `Olá, estudante!`). The current live image only has a shared passwordless `ubuntu` account, so matrícula authentication cannot be implemented as a real isolated account without an installer or trusted provisioning authority. Do not use shared `12345`: it defeats account isolation. Original request: [`STUDENT-LOGIN-REQUEST.md`](prompts/STUDENT-LOGIN-REQUEST.md).
3. **AI foundation and NVIDIA chat — IN PROGRESS.** Stage 1 and text-chat portions of Stage 2 are implemented in source; 25 automated tests pass, including image-route and context-validation tests. No real API request or rebuilt-ISO GTK/D-Bus/keyring runtime check has been made. Prompts: [`AI-STAGE-1.md`](prompts/AI-STAGE-1.md), [`AI-STAGE-2.md`](prompts/AI-STAGE-2.md).
4. **Screen understanding and visual guidance — SOURCE IMPLEMENTED; RUNTIME VALIDATION OPEN.** Source adds X11 window selection, bounded AT-SPI metadata, consent/preview/send screens, a documentation-verified multimodal model route, structured target validation, and a temporary click-through overlay. Real X11/AT-SPI/Eclipse integration remains unverified; focus-change monitoring, area selection, and step-state tracking remain open. Full prompt: [`AI-STAGE-3.md`](prompts/AI-STAGE-3.md).
5. **Persistent educational memory and safe system tools — SOURCE IMPLEMENTED; RUNTIME VALIDATION OPEN.** Schema v2 adds local summaries, bounded context, explicit/editable memory, lexical retrieval, retention, deletion/export, and GTK controls. Typed tools are limited to installed apps, safe HTTP(S) links, basic system information, user-selected folders, and confirmed non-overwriting file creation. No shell, package installation, or model-initiated tool calls are available. Automated tests pass. Full prompt: [`AI-STAGE-4.md`](prompts/AI-STAGE-4.md).
6. **Final XFCE/Plymouth/ISO integration and security/performance review — IN PROGRESS.** Source packages the user-selected artwork as both desktop wallpaper and Plymouth splash and bundles the assistant/memory/tools with the desktop. The ISO is rebuilt and its embedded images are checksum-verified. Latest UTM boot still waits on the NetworkManager start job, so the XFCE appearance, app launching, and remaining runtime checks are open. Full prompt: [`AI-STAGE-5.md`](prompts/AI-STAGE-5.md).

## Security invariants

- The live ISO currently autologs into a single `ubuntu` account and is not installable. It does not provide student-account isolation. Never present it as a multi-student secure deployment.
- Do not store a shared initial password in the ISO or repository. Use individually provisioned credentials and require a password change only when account provisioning exists.
- API keys belong only in each logged-in user's Secret Service keyring. If the keyring is unavailable or locked, report that and fail closed; never fall back to plaintext.
- Conversations and learning data remain under that user's XDG data directory, with restrictive file permissions.
- Never send private files, screenshots, SUAP/AVA data, or active-window context automatically. Ask for specific consent where required.
- The model never receives unrestricted shell, administrator, file, or account-management access.
- The model cannot call system tools. The student starts each supported local operation; file creation requires an exact, expiring, one-use confirmation token.
- Memory is disabled by default, explicitly written by the student, editable, searchable locally, and removable/exportable. Obvious credential and identifier strings are rejected from memory content.
