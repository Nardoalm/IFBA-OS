// Plasma evaluates this Look-and-Feel layout when there are no saved containments.
for (const desktop of desktops()) {
    desktop.wallpaperPlugin = "org.kde.image"
    desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"]
    desktop.writeConfig("Image", "file:///usr/share/backgrounds/ifba-os/campus-jacobina.jpg")
}

var topPanel = new Panel
topPanel.location = "top"
topPanel.height = 36
topPanel.lengthMode = "fill"
topPanel.alignment = "left"
topPanel.floating = false
topPanel.opacity = "translucent"
topPanel.hiding = "none"

// Keep the launcher visible even when no application exports a global menu.
var topLauncher = topPanel.addWidget("org.kde.plasma.kickoff")
topLauncher.currentConfigGroup = ["General"]
topLauncher.writeConfig("icon", "file:///usr/share/ifba-os/assets/icons/ifba-institutional-symbol.png")
topLauncher.writeConfig("menuLabel", "IFBA OS")
topLauncher.writeConfig("favorites", "applications:ifba-ai.desktop,applications:firefox.desktop,applications:org.kde.dolphin.desktop,applications:org.kde.konsole.desktop,applications:systemsettings.desktop,applications:suap-ifba.desktop,applications:ava-ifba.desktop")
topLauncher.writeConfig("systemApplications", "systemsettings.desktop,org.kde.kinfocenter.desktop,org.kde.discover.desktop")
topLauncher.writeConfig("systemFavorites", "suspend,logout,reboot,shutdown")
topLauncher.writeConfig("primaryActions", "3")
topLauncher.writeConfig("showActionButtonCaptions", "true")
topLauncher.writeConfig("favoritesDisplay", 0)
topLauncher.writeConfig("applicationsDisplay", 0)
topLauncher.writeConfig("appNameFormat", 0)
topLauncher.writeConfig("alphaSort", true)

// Plasma's appmenu exports menus only for applications that support the KDE
// global-menu protocol. Other applications simply have no menu here.
var globalMenu = topPanel.addWidget("org.kde.plasma.appmenu")
globalMenu.currentConfigGroup = ["Appearance"]
globalMenu.writeConfig("compactView", false)

var spacer = topPanel.addWidget("org.kde.plasma.panelspacer")
spacer.currentConfigGroup = ["General"]
spacer.writeConfig("expanding", true)

topPanel.addWidget("org.kde.milou")

var tray = topPanel.addWidget("org.kde.plasma.systemtray")
tray.currentConfigGroup = ["General"]
tray.writeConfig("extraItems", "org.kde.plasma.notifications,org.kde.plasma.networkmanagement,org.kde.plasma.volume,org.kde.plasma.battery,org.kde.plasma.bluetooth")
tray.writeConfig("shownItems", "org.kde.plasma.notifications,org.kde.plasma.networkmanagement,org.kde.plasma.volume,org.kde.plasma.battery,org.kde.plasma.bluetooth")
tray.writeConfig("scaleIconsToFit", "true")
tray.writeConfig("iconSpacing", "3")

var clock = topPanel.addWidget("org.kde.plasma.digitalclock")
clock.currentConfigGroup = ["Appearance"]
clock.writeConfig("showDate", true)
clock.writeConfig("dateFormat", "custom")
clock.writeConfig("customDateFormat", "ddd d 'de' MMM yyyy")
clock.writeConfig("use24hFormat", "2")
clock.writeConfig("dateDisplayFormat", "1")

var dock = new Panel
dock.location = "bottom"
dock.height = 68
dock.lengthMode = "fit"
dock.alignment = "center"
dock.floating = true
dock.opacity = "translucent"
dock.hiding = "none"

var dockLauncher = dock.addWidget("org.kde.plasma.kickoff")
dockLauncher.currentConfigGroup = ["General"]
dockLauncher.writeConfig("icon", "file:///usr/share/ifba-os/assets/icons/ifba-institutional-symbol.png")
dockLauncher.writeConfig("favorites", "applications:ifba-ai.desktop,applications:firefox.desktop,applications:org.kde.dolphin.desktop,applications:org.kde.konsole.desktop,applications:systemsettings.desktop,applications:suap-ifba.desktop,applications:ava-ifba.desktop")
dockLauncher.writeConfig("systemApplications", "systemsettings.desktop,org.kde.kinfocenter.desktop,org.kde.discover.desktop")
dockLauncher.writeConfig("systemFavorites", "suspend,logout,reboot,shutdown")
dockLauncher.writeConfig("primaryActions", "3")
dockLauncher.writeConfig("showActionButtonCaptions", "true")
dockLauncher.writeConfig("favoritesDisplay", 0)
dockLauncher.writeConfig("applicationsDisplay", 0)
dockLauncher.writeConfig("appNameFormat", 0)
dockLauncher.writeConfig("alphaSort", true)

var tasks = dock.addWidget("org.kde.plasma.icontasks")
tasks.currentConfigGroup = ["General"]
tasks.writeConfig("launchers", [
    "applications:org.kde.dolphin.desktop",
    "applications:systemsettings.desktop",
    "applications:ifba-ai.desktop",
    "applications:org.kde.konsole.desktop",
    "applications:com.visualstudio.CodeOSS.desktop",
    "applications:firefox.desktop",
    "applications:libreoffice-writer.desktop",
].join(","))
tasks.writeConfig("maxStripes", 1)
tasks.writeConfig("showOnlyCurrentScreen", true)
tasks.writeConfig("showToolTips", true)
tasks.writeConfig("groupingStrategy", 1)
tasks.writeConfig("sortingStrategy", 1)

dock.addWidget("org.kde.plasma.trash")
