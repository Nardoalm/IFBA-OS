# Initial technical decisions

- Ubuntu 24.04 LTS amd64 is the first prototype base because it has a long maintenance window and broad package support. This is a prototype choice, not a commitment to the eventual release base.
- XFCE is selected for the initial live image to limit desktop resource use. Compare it on target hardware before settling the experience.
- The first-run Electron screen is a UI prototype only. Application installation must later be implemented through a privileged, narrowly scoped system service; never let Electron renderer code execute arbitrary shell commands.
- Shared applications should be installed system-wide once; user documents, preferences, and API credentials remain per-user.
- The generated IFBA mark is an illustration placeholder. Replace it with authorized official artwork before distribution.
- No SUAP/AVA data integration exists. Future data access requires documented APIs and written institutional approval.
