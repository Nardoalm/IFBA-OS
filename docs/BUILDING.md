# Building the prototype ISO

The current build targets Ubuntu 24.04 LTS amd64 with Casper, XFCE, LightDM, Xorg, NetworkManager, NetSurf, and an Electron desktop home. It is a live-session prototype, not an installer or release build.

Requirements: Docker Desktop with at least 8 GB RAM, 30 GB free disk, and network access. From the repository root run `./scripts/build-iso.sh`. The host script invokes `scripts/build-iso-container.sh` and writes `output/ifba-os-ubuntu-24.04-amd64.iso`. Docker volume `ifba-os-build-cache` holds the Linux root filesystem because the macOS host filesystem is case-insensitive. On Apple Silicon, the build uses amd64 emulation. Removing that volume discards the cached root filesystem.

The image configures an automatic `ubuntu` live user, XFCE bottom panel with the Whisker application menu, its IFBA icon, Super/Windows-key shortcut, NetworkManager tray applet, NetSurf browser helper/default, desktop shortcuts, and an Electron home application launched at session start. The desktop background is the supplied full wallpaper with the 3D IFBA OS mark embedded in the image; the home page places portal shortcuts and activities around it without drawing a second central mark. Electron is installed into the guest from the pinned npm dependency and Linux amd64 package downloaded inside the Linux build container. SUAP and AVA links open only the allowlisted public HTTPS domains using the guest default browser.

The educational package catalogue is not installed by this image. The AI assistant is not connected. The current live image has no installer or disk persistence. The generated IFBA identity is provisional. Do not boot this image on real hardware or present it as an official IFBA release.

The build removes the container's systemd-resolved stub before SquashFS creation so the live guest can configure DNS itself. Never put credentials, API keys, cookies, student data, or personal files in the build context.
