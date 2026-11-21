// Native Plasma 6 panels only. Keep menus and actions tied to real applets.
// The session setup applies this layout once to a new profile; existing panel
// customizations are left untouched after first login.
var topPanel = new Panel
topPanel.location = "top"
topPanel.height = 36
topPanel.lengthMode = "fill"
topPanel.alignment = "left"
topPanel.floating = true
topPanel.hiding = "none"

// Plasma's appmenu exports menus only for applications that support the KDE
// global-menu protocol. Other applications simply have no menu here.
var globalMenu = topPanel.addWidget("org.kde.plasma.appmenu")
globalMenu.currentConfigGroup = ["Appearance"]
globalMenu.writeConfig("compactView", "true")

var spacer = topPanel.addWidget("org.kde.plasma.panelspacer")
spacer.currentConfigGroup = ["General"]
spacer.writeConfig("expanding", true)

topPanel.addWidget("org.ifbaos.controlcenter")

var tray = topPanel.addWidget("org.kde.plasma.systemtray")
tray.currentConfigGroup = ["General"]
tray.writeConfig("extraItems", "org.kde.plasma.notifications,org.kde.plasma.networkmanagement,org.kde.plasma.volume,org.kde.plasma.battery")
tray.writeConfig("shownItems", "org.kde.plasma.notifications,org.kde.plasma.networkmanagement,org.kde.plasma.volume,org.kde.plasma.battery")
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
dock.height = 70
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

var tasks = dock.addWidget("org.kde.plasma.icontasks")
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
