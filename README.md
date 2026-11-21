# IFBA OS

An independent Linux distribution prototype for academic use. The active live image uses Ubuntu 26.04 and KDE Plasma 6 for ARM64 and AMD64. IFBA Welcome is a native Qt 6 application that opens during the first desktop session; an older Electron screen remains in `app/` as a separate design prototype. This is not an official IFBA system and is not suitable for production deployment.

## Current direction

- Ubuntu 26.04 LTS with KDE Plasma 6 for ARM64 and AMD64; each architecture requires its own runtime validation.
- Mint-inspired usability and Linux Educacional-inspired educational app curation without reusing their branding.
- SUAP and AVA are opened as ordinary web links. No institutional login, scraping, or private API integration is implemented.
- The AI assistant is optional. Native GTK settings/chat and consent-based visual guidance, per-user credential/data storage, and NVIDIA text/image request paths are present in source; live API and rebuilt-ISO runtime validation remain pending.

## Prototype

The native session uses KDE Plasma 6, SDDM, Dolphin, Konsole, Mozilla Firefox, IFBA AI, and IFBA Welcome. Welcome links only to the project's existing public SUAP/AVA HTTPS destinations, local documentation, Discover updates, and installed educational applications. It does not integrate academic accounts or private APIs. The package catalogue is `config/educational-apps.json`; Welcome details are in [`docs/IFBA-WELCOME.md`](docs/IFBA-WELCOME.md). Visual assets are in `assets/`; generated IFBA marks are placeholders and must not be treated as official institutional artwork.

The assistant architecture and security constraints are documented in `docs/ARCHITECTURE.md`, `docs/AI-ASSISTANT.md`, and `docs/SECURITY.md`. The current live image still uses one passwordless demo account and is not suitable for configuring real student credentials.

## Build an ISO

The build script uses debootstrap, Casper, Plasma, and GRUB inside a Docker Linux container. Review `docs/BUILDING.md` first. On Apple Silicon, Docker runs the amd64 build under emulation and may take a while. The output is organized by product version and architecture under `output/`.

## VM testing

See `docs/VM-TESTING.md`. Use a disposable VM with no host folders or personal accounts mounted. This image is an experimental live image, not an installer or a supported release.

## License and identity

Code is currently offered under MIT; see `LICENSE`. Third-party packages retain their own licenses. Before public distribution, review all package and artwork licenses and obtain any required permission to use IFBA names or marks.
