# Initial technical decisions

- Ubuntu 24.04 LTS amd64 is the first prototype base because it has a long maintenance window and broad package support. This is a prototype choice, not a commitment to the eventual release base.
- XFCE is selected for the initial live image to limit desktop resource use. Compare it on target hardware before settling the experience.
- The first-run Electron screen is a UI prototype only. Application installation must later be implemented through a privileged, narrowly scoped system service; never let Electron renderer code execute arbitrary shell commands.
- Shared applications should be installed system-wide once; user documents, preferences, and API credentials remain per-user.
- The assistant daemon runs as a systemd user service and exposes a user-session D-Bus API. Its settings and SQLite database use per-user XDG directories; the NVIDIA key is stored only through Secret Service/libsecret.
- The live image's passwordless `ubuntu` autologin is a demo constraint, not the student-account design. Do not ship a common `12345` bootstrap password; defer student matrícula provisioning until a secure installer or authorized provisioning mechanism exists.
- The generated IFBA mark is an illustration placeholder. Replace it with authorized official artwork before distribution.
- No SUAP/AVA data integration exists. Future data access requires documented APIs and written institutional approval.
