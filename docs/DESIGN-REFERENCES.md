# Desktop design references

Research checked on 2026-11-18:

- Apple's latest macOS is macOS 27 Golden Gate 27.2.1. Apple describes its updated Liquid Glass treatment in terms of more consistent controls, clearer contrast, and refined window shapes. See [Apple's macOS page](https://www.apple.com/os/macos/) and [Apple security releases](https://support.apple.com/en-us/100100).
- Microsoft's current annual Windows 11 release is version 26H2. Microsoft documents a responsive Start menu with category/grid views, stronger app search, and taskbar customization. See [What's new in Windows 11 26H2](https://learn.microsoft.com/windows/whats-new/whats-new-windows-11-version-26h2) and [the 2026 Update announcement](https://blogs.windows.com/windowsexperience/2026/09/29/how-to-get-the-windows-11-2026-update/).
- Xfce 4.20 is the latest stable upstream release. Its X11 window manager includes a compositor for window/panel shadows and opacity; Xfce does not currently provide its own Wayland compositor. See [Xfce's download page](https://www.xfce.org/download/) and [4.20 tour](https://www.xfce.org/about/tour420).

## Adaptation in IFBA OS

- **macOS principles:** restrained dark surfaces, clear spacing, a compact bottom launcher with active-window list, consistent icons, focused typography, and subtle depth.
- **Windows principles:** a discoverable searchable Whisker application menu, familiar task switching, accessible tray controls, and a responsive full-width panel layout.
- **IFBA OS identity:** the supplied metallic wallpaper, the provisional IFBA OS menu mark, and a restrained green interaction accent.
- **Native components:** XFCE panel and plugins, Whisker, Xfwm4, Xfdesktop, GTK settings, Thunar, Mozilla Firefox, and LightDM. The Electron page is not launched or included in the live desktop image.

The ISO uses the upstream Ubuntu Yaru Dark GTK/Xfwm theme, Yaru icons, Inter, and Xfwm4's built-in compositor. Picom is deliberately not installed: Xfwm4 already owns compositing in this X11 session, and running two compositors risks rendering conflicts. The built-in compositor provides shadows and opacity, but XFWM4 does not provide polished open/minimize animations or background blur. The desktop keeps those effects off rather than adding an unverified compositor or sacrificing responsiveness.

The current default has one bottom panel with the IFBA menu, launchers, task list, tray, audio, clock, and session controls. The workspace pager was removed with the one-workspace default. The former top greeting/date panel was an actual second XFCE panel and caused the reported duplication; it is no longer part of the shipped layout. SUAP/AVA desktop links open their public HTTPS URLs in the configured browser. No academic activity data is fabricated. GTK4 and non-GTK applications may not follow GTK3 theme overrides exactly.

The system still uses the upstream Yaru Dark/Yaru theme and icons, so it can retain Ubuntu's visual character outside the custom wallpaper, panel, typography, and green focus/interaction treatment. This pass avoids replacing stable themes before the ISO reaches a usable XFCE session. The panel CSS has hover, checked, active, and focus states; animations remain disabled by default. Runtime visual review is pending.

This is a first native XFCE visual pass, not evidence that every dialog, notification, application, or login state has been visually reviewed. See `docs/VM-TESTING.md` for the runtime validation record.
