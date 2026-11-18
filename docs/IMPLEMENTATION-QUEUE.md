# IFBA OS implementation queue

This file preserves the user's requested order and the detailed AI-stage prompts. The full prompt text is archived in [`prompts/`](prompts/).

The user asked to finish the three active workstreams before starting Etapa 3: (1) native XFCE modernization, (2) student greeting/account login, and (3) Etapas 1–2 of the AI assistant. Workstream 1 is complete; 2 and 3 must finish before Etapa 3 begins.

## Order and status

1. **Native XFCE modernization — DONE.** Commit `5380c1f` is on `origin/development`. The latest ISO still needs a fresh graphical UTM boot; the prior VM run reached tty2, and the rebuilt image now selects `graphical.target`.
2. **Student greeting and local account onboarding — IN PROGRESS.** The top panel now says `Olá, [student name]!` (fall back to `Olá, estudante!`). The current live image only has a shared passwordless `ubuntu` account, so matrícula authentication cannot be implemented as a real isolated account without an installer or trusted provisioning authority. Do not use shared `12345`: it defeats account isolation. Original request: [`STUDENT-LOGIN-REQUEST.md`](prompts/STUDENT-LOGIN-REQUEST.md).
3. **AI foundation and NVIDIA chat — IN PROGRESS.** Stage 1 and text-chat portions of Stage 2 are implemented in source with 18 automated tests. The API has not been tested with a real key, and GTK/D-Bus/keyring runtime has not yet been validated in a rebuilt ISO. Prompts: [`AI-STAGE-1.md`](prompts/AI-STAGE-1.md), [`AI-STAGE-2.md`](prompts/AI-STAGE-2.md).
4. **Screen understanding and visual guidance — QUEUED.** Start after tasks 2 and 3 are complete. Do not implement it before window context, accessible controls, authorized screenshot sharing, and cancellation are designed. Full prompt: [`AI-STAGE-3.md`](prompts/AI-STAGE-3.md).
5. **Persistent educational memory and safe system tools — QUEUED.** Start after Etapa 3 is complete. Reuse the existing per-user store and service; do not add another daemon or database without evidence. Full prompt: [`AI-STAGE-4.md`](prompts/AI-STAGE-4.md).
6. **Final XFCE/Plymouth/ISO integration and security/performance review — QUEUED.** Execute last, after Etapas 1–4, then continue build/boot/observe/fix/rebuild cycles and report actual blockers. Full prompt: [`AI-STAGE-5.md`](prompts/AI-STAGE-5.md).

## Security invariants

- The live ISO currently autologs into a single `ubuntu` account and is not installable. It does not provide student-account isolation. Never present it as a multi-student secure deployment.
- Do not store a shared initial password in the ISO or repository. Use individually provisioned credentials and require a password change only when account provisioning exists.
- API keys belong only in each logged-in user's Secret Service keyring. If the keyring is unavailable or locked, report that and fail closed; never fall back to plaintext.
- Conversations and learning data remain under that user's XDG data directory, with restrictive file permissions.
- Never send private files, screenshots, SUAP/AVA data, or active-window context automatically. Ask for specific consent where required.
- The model never receives unrestricted shell, administrator, file, or account-management access.
