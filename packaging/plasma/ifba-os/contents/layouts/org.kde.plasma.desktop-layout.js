// Plasma evaluates this Look-and-Feel layout when there are no saved containments.
for (const desktop of desktops()) {
    desktop.wallpaperPlugin = "org.kde.image"
    desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"]
    desktop.writeConfig("Image", "file:///usr/share/backgrounds/ifba-os/wallpaper.png")
}

var topPanel = new Panel
topPanel.location = "top"
topPanel.height = 36
topPanel.lengthMode = "fill"
topPanel.alignment = "left"
topPanel.floating = true
topPanel.hiding = "none"

// Keep the launcher visible even when no application exports a global menu.
var topLauncher = topPanel.addWidget("org.kde.plasma.kickoff")
topLauncher.currentConfigGroup = ["General"]
topLauncher.writeConfig("icon", "file:///usr/share/ifba-os/assets/icons/ifba-institutional-symbol.png")

// Plasma's appmenu exports menus only for applications that support the KDE
// global-menu protocol. Other applications simply have no menu here.
var globalMenu = topPanel.addWidget("org.kde.plasma.appmenu")
globalMenu.currentConfigGroup = ["Appearance"]
globalMenu.writeConfig("compactView", "true")

var spacer = topPanel.addWidget("org.kde.plasma.panelspacer")
spacer.currentConfigGroup = ["General"]
spacer.writeConfig("expanding", true)

var tray = topPanel.addWidget("org.kde.plasma.systemtray")
tray.currentConfigGroup = ["General"]
tray.writeConfig("extraItems", "org.kde.plasma.notifications,org.kde.plasma.networkmanagement,org.kde.plasma.volume,org.kde.plasma.battery,org.kde.plasma.bluetooth")
tray.writeConfig("shownItems", "org.kde.plasma.notifications,org.kde.plasma.networkmanagement,org.kde.plasma.volume,org.kde.plasma.battery,org.kde.plasma.bluetooth")
tray.writeConfig("scaleIconsToFit", "true")
tray.writeConfig("iconSpacing", "2")

var clock = topPanel.addWidget("org.kde.plasma.digitalclock")
clock.currentConfigGroup = ["Appearance"]
clock.writeConfig("showDate", true)
clock.writeConfig("dateFormat", "custom")
clock.writeConfig("customDateFormat", "ddd d 'de' MMM yyyy")
clock.writeConfig("use24hFormat", "2")
clock.writeConfig("dateDisplayFormat", "1")

var dock = new Panel
dock.location = "bottom"
dock.height = 72
dock.lengthMode = "fit"
dock.alignment = "center"
dock.floating = true
dock.hiding = "dodgewindows"

var appLauncher = dock.addWidget("org.kde.plasma.kickoff")
appLauncher.currentConfigGroup = ["General"]
appLauncher.writeConfig("icon", "file:///usr/share/ifba-os/assets/icons/ifba-institutional-symbol.png")
appLauncher.writeConfig("favorites", "applications:ifba-ai.desktop,applications:firefox.desktop,applications:org.kde.dolphin.desktop,applications:org.kde.konsole.desktop,applications:systemsettings.desktop,applications:suap-ifba.desktop,applications:ava-ifba.desktop")
appLauncher.writeConfig("systemApplications", "systemsettings.desktop,org.kde.kinfocenter.desktop,org.kde.discover.desktop")
appLauncher.writeConfig("systemFavorites", "suspend,logout,reboot,shutdown")
appLauncher.writeConfig("primaryActions", "3")
appLauncher.writeConfig("showActionButtonCaptions", "true")
appLauncher.writeConfig("favoritesDisplay", 0)
appLauncher.writeConfig("applicationsDisplay", 0)
appLauncher.writeConfig("appNameFormat", 0)
appLauncher.writeConfig("alphaSort", true)

var tasks = dock.addWidget("com.github.mattanis.macosdock")
tasks.currentConfigGroup = ["General"]
tasks.writeConfig("launchers", "applications:ifba-ai.desktop,applications:firefox.desktop,applications:org.kde.dolphin.desktop,applications:org.kde.konsole.desktop,applications:systemsettings.desktop")
tasks.writeConfig("maxStripes", 1)
tasks.writeConfig("showOnlyCurrentScreen", true)
tasks.writeConfig("showToolTips", true)
tasks.writeConfig("iconSpacing", 1)
tasks.writeConfig("groupingStrategy", 1)
tasks.writeConfig("groupedTaskVisualization", 0)
tasks.writeConfig("groupPopups", true)
tasks.writeConfig("sortingStrategy", 1)
tasks.writeConfig("separateLaunchers", true)
tasks.writeConfig("taskHoverEffect", true)
tasks.writeConfig("zoomMultiplier", 1.25)
tasks.writeConfig("zoomAnimationType", 1)
tasks.writeConfig("hoverElevation", 6)
tasks.writeConfig("iconSize", 44)
tasks.writeConfig("autoAdjustPanelThickness", false)
tasks.writeConfig("containerBackgroundColor", "#101A15")
tasks.writeConfig("containerBackgroundType", 3)
tasks.writeConfig("blurOpacity", 0.72)
