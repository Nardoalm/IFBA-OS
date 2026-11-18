# IFBA OS

An early, independent Linux distribution prototype for academic use. The live image is being built around a native XFCE desktop, visual assets, package-selection data, and a custom Ubuntu image build. An Electron welcome-screen prototype remains in `app/` for design exploration and is not part of the native desktop session. This is not an official IFBA system and is not suitable for production deployment.

## Current direction

- Ubuntu 24.04 LTS base for the first x86_64 live-image prototype.
- XFCE desktop for a modest-resource starting point; desktop choice remains subject to hardware testing.
- Mint-inspired usability and Linux Educacional-inspired educational app curation without reusing their branding.
- SUAP and AVA are opened as ordinary web links. No institutional login, scraping, or private API integration is implemented.
- The AI assistant is optional and not connected in this prototype.

## Prototype

The native session uses XFCE panels, Xfwm4, Xfdesktop, GTK settings, Thunar, NetSurf, and LightDM. The Electron welcome-screen source is kept in `app/` as a separate design prototype and is not launched by the ISO. The package catalogue is `config/educational-apps.json`. Visual assets are in `assets/`; generated IFBA marks are placeholders and must not be treated as official institutional artwork.

## Build an ISO

The build script uses debootstrap, Casper, XFCE, and GRUB inside a Docker Linux container. Review `docs/BUILDING.md` first. On Apple Silicon, Docker runs the amd64 build under emulation and may take a while. The output is written to `output/ifba-os-ubuntu-24.04-amd64.iso`.

## VM testing

See `docs/VM-TESTING.md`. Use a disposable VM with no host folders or personal accounts mounted. This image is an experimental live image, not an installer or a supported release.

## License and identity

Code is currently offered under MIT; see `LICENSE`. Third-party packages retain their own licenses. Before public distribution, review all package and artwork licenses and obtain any required permission to use IFBA names or marks.
