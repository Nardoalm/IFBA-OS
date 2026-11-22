# WhiteSur KDE resources vendored by IFBA OS

- Upstream: https://github.com/vinceliuice/WhiteSur-kde
- Audited and pinned commit: `cf4df59ce91004f7ea39358b1b8ff917d5c329f7`
- Upstream license: GPL-3.0 (full text in `LICENSE`).
- Author attribution: Vince Liuice / contributors listed in `AUTHORS`.
- Upstream scripts were not executed or copied.

## Included upstream components

- `packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark/`: selected Plasma 6 desktop-theme SVG/SVGZ resources and metadata.
- `packaging/plasma/window-decoration/IFBA-Window/`: selected dark Aurorae decoration SVGs, scale variants and shared button SVGs.
- `packaging/kvantum/IFBA-Glass/` and `IFBA-Glass-Opaque/`: selected Kvantum SVG themes and configs.

These are modified derivatives: metadata/theme identifiers, palette/accent colors and Aurorae button placement have been adapted to IFBA OS. The canonical color source remains `packaging/design-system/tokens.json`; Plasma colors use the generated IFBA scheme.

## Excluded

No upstream installer/uninstaller, wallpapers, icons, fonts, SDDM theme, look-and-feel, plasmoid, network fetch, or privileged operation is included. The audit found conflicting wallpaper licensing and insufficient per-file provenance for icon resources. GTK uses Ubuntu's Breeze GTK theme with IFBA's existing stylesheet; menus and icons remain native KDE/Breeze.
