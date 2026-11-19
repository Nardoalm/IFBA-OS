# Next implementation prompt

Continue IFBA OS on the `development` branch. Use English Conventional Commits with a concise subject and a detailed body. Read `AGENTS.md`, this file's linked project docs, and inspect Git status before editing. Preserve unrelated local changes. Commit and push only to `origin/development` when safe.

## Prompt

> Diagnose why the rebuilt IFBA OS ISO reaches a text login instead of LightDM/XFCE. Current artifact SHA-256: `88901ac4237d49c94003acbafd1f17d3f925acaba2774c743d6563a7218190b1`. The UTM CD menu showed the matching basename but did not expose its backing path. Rootfs static checks show `default.target -> graphical.target` and `display-manager.service -> lightdm.service`; the Plymouth image appeared before the text console. Do not change boot services until guest journal or equivalent runtime evidence identifies the failure. The existing VM is QEMU x86_64, 4 GiB RAM, 2 CPUs, 64 GiB disk, Shared/NAT, e1000; it has no guest agent and is not a fresh 30 GiB disposable VM. Keep no host shares or credentials. Once XFCE starts, verify the selected wallpaper, panels, Whisker/Super menu, app launchers, Thunar, Terminal, Firefox, audio/network, shutdown and restart. Test guest IP, route, gateway, DNS and HTTPS separately. Do not visit SUAP/AVA or configure AI. UTM Shared networking uses the Mac's existing uplink and needs no Wi-Fi password. Update test/roadmap docs with observed evidence, run relevant checks, keep the ISO out of Git, and commit/push only to `origin/development` when safe.

## Deferred project work

- Verify desktop visuals and behavior at 1366×768 and 1920×1080.
- Review GTK/Xfwm appearance across applications, dialogs, LightDM, and notifications.
- Implement a real, permission-aware educational app installer with explicit confirmation and rollback.
- Decide a supported installer, persistence, updates, recovery, and hardware support policy.
- Integrate SUAP/AVA only through interfaces documented and authorized by IFBA/DGTI.
- Design optional AI with per-user secure key storage, visible screen sharing, scoped actions, and explicit confirmation.
- Review accessibility, licenses, security, and provisional IFBA branding before distribution.
