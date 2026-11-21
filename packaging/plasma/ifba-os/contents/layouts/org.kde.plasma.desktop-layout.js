// Native Plasma panels only. Keep the applet identifiers available in the
// Ubuntu Plasma 6 package set; no third-party dock or global-menu applet.
var topPanel = new Panel
topPanel.location = "top"
topPanel.height = 36
topPanel.lengthMode = "fill"
topPanel.alignment = "left"
topPanel.floating = true
topPanel.hiding = "none"

var systemMenu = topPanel.addWidget("org.kde.plasma.kickoff")
systemMenu.currentConfigGroup = ["General"]
systemMenu.writeConfig("icon", "file:///usr/share/ifba-os/assets/icons/ifba-mark-placeholder.png")
systemMenu.writeConfig("menuLabel", "IFBA OS")
systemMenu.writeConfig("favorites", "applications:org.kde.kinfocenter.desktop,applications:systemsettings.desktop,applications:firefox.desktop,applications:org.kde.dolphin.desktop,applications:org.kde.konsole.desktop,applications:ifba-ai.desktop,applications:suap-ifba.desktop,applications:ava-ifba.desktop")
systemMenu.writeConfig("systemApplications", "systemsettings.desktop,org.kde.kinfocenter.desktop,org.kde.discover.desktop")
systemMenu.writeConfig("systemFavorites", "lock-screen,reboot,shutdown")
systemMenu.writeConfig("primaryActions", "3")
systemMenu.writeConfig("showActionButtonCaptions", "true")

var applicationsMenu = topPanel.addWidget("org.kde.plasma.kicker")
applicationsMenu.currentConfigGroup = ["General"]
applicationsMenu.writeConfig("icon", "applications-all-symbolic")
applicationsMenu.writeConfig("showRecentApps", "false")
applicationsMenu.writeConfig("showRecentDocs", "false")

var globalMenu = topPanel.addWidget("org.kde.plasma.appmenu")
globalMenu.currentConfigGroup = ["Appearance"]
globalMenu.writeConfig("compactView", "false")

var spacer = topPanel.addWidget("org.kde.plasma.panelspacer")
spacer.currentConfigGroup = ["General"]
spacer.writeConfig("expanding", true)

var search = topPanel.addWidget("org.kde.milou")

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

var dockLauncher = dock.addWidget("org.kde.plasma.kickoff")
dockLauncher.currentConfigGroup = ["General"]
dockLauncher.writeConfig("icon", "file:///usr/share/ifba-os/assets/icons/ifba-mark-placeholder.png")

var tasks = dock.addWidget("org.kde.plasma.icontasks")
tasks.currentConfigGroup = ["General"]
tasks.writeConfig("launchers", "applications:firefox.desktop,applications:org.kde.dolphin.desktop,applications:org.kde.konsole.desktop,applications:ifba-ai.desktop,applications:org.thonny.Thonny.desktop,applications:org.kde.gcompris.desktop,applications:libreoffice-writer.desktop,applications:systemsettings.desktop")
tasks.writeConfig("maxStripes", 1)
tasks.writeConfig("showOnlyCurrentScreen", true)
tasks.writeConfig("showToolTips", true)
tasks.writeConfig("iconSpacing", 1)
tasks.writeConfig("groupingStrategy", 1)
tasks.writeConfig("groupedTaskVisualization", 0)
tasks.writeConfig("groupPopups", true)
tasks.writeConfig("sortingStrategy", 1)
tasks.writeConfig("separateLaunchers", true)
tasks.writeConfig("taskHoverEffect", false)

dock.addWidget("org.kde.plasma.trash")
