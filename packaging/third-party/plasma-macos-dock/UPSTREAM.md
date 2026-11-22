# IFBA Dock upstream

Matt Anis and KDE contributors; per-file copyright and SPDX headers preserved.
Source: https://github.com/Matt-Anis/plasma-macos-dock/tree/ba4f0551ac9c71e9a777451aa1c43db144a10156

QML/JS and config only. No Apple icons, screenshots, installer or C++ module included. Metadata uses a native KDE icon. IFBA changes: dark green default, moderate zoom/lift, and reduced-motion gates for magnification and bounce. Complete corresponding source is distributed in packaging/plasma/ifba-dock; original file hashes are in manifest.json. LGPL applies to the files carrying LGPL headers, GPL to the others.

Pure QML is CPU architecture independent; private Plasma APIs require guest validation on Plasma 6.6. Optional native blur plugin is not supplied; Plasma panel/KWin provide blur, with solid background available in the widget settings. Runtime and multiple-monitor behavior have not been validated by IFBA.
