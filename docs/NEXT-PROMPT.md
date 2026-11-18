# Next implementation prompt

Continue IFBA OS on the `development` branch. Use English Conventional Commits with a concise subject and a detailed body. Read `AGENTS.md`, this file's linked project docs, and inspect Git status before editing. Preserve unrelated local changes. Commit and push only to `origin/development` when safe.

## Prompt

> Validate the latest Ubuntu 24.04 amd64 live ISO in the existing disposable UTM VM. Use 4 GB RAM, 2 CPUs, a 30 GB virtual disk, NAT, and no shared host folders or credentials. The previous ISO reached tty2 instead of XFCE because its root filesystem lacked `/etc/systemd/system/default.target`; the latest build now links that target to `graphical.target`. Confirm the latest ISO checksum before booting. Check whether LightDM starts and the XFCE desktop appears, then verify the supplied wallpaper, both panels, Whisker menu and Super key, app launchers, task switching, workspaces, Thunar, Terminal, NetSurf, settings, dialogs, notifications, network/audio controls, and shutdown/reboot. Do not log in to SUAP/AVA or configure AI. If boot still fails, collect the visible error and inspect the guest journal before changing the build. Update `docs/VM-TESTING.md`, `docs/DEVELOPMENT-LOOP.md`, and `docs/PROJECT-ROADMAP.md` with only observed results. Rebuild only when source changes, keep the ISO out of Git, run relevant static checks, stage and review the focused diff, commit in English, and push only to `origin/development` if safe.

## Deferred project work

- Verify desktop visuals and behavior at 1366×768 and 1920×1080.
- Review GTK/Xfwm appearance across applications, dialogs, LightDM, and notifications.
- Implement a real, permission-aware educational app installer with explicit confirmation and rollback.
- Decide a supported installer, persistence, updates, recovery, and hardware support policy.
- Integrate SUAP/AVA only through interfaces documented and authorized by IFBA/DGTI.
- Design optional AI with per-user secure key storage, visible screen sharing, scoped actions, and explicit confirmation.
- Review accessibility, licenses, security, and provisional IFBA branding before distribution.
