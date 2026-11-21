// Native Plasma panels only. Keep the applet identifiers available in the
// Ubuntu Plasma 6 package set; no third-party dock or global-menu applet.
var topPanel = new Panel
topPanel.location = "top"
topPanel.height = 34
topPanel.lengthMode = "fill"
topPanel.alignment = "left"
topPanel.floating = false
topPanel.hiding = "none"

var launcher = topPanel.addWidget("org.kde.plasma.kickoff")
launcher.currentConfigGroup = ["General"]
launcher.writeConfig("icon", "/usr/share/ifba-os/assets/icons/ifba-mark-placeholder.png")
launcher.writeConfig("favorites", "applications:firefox.desktop,applications:org.kde.dolphin.desktop,applications:org.kde.konsole.desktop,applications:ifba-ai.desktop,applications:systemsettings.desktop,applications:suap-ifba.desktop,applications:ava-ifba.desktop")

var spacer = topPanel.addWidget("org.kde.plasma.panelspacer")
spacer.currentConfigGroup = ["General"]
spacer.writeConfig("expanding", true)

var tray = topPanel.addWidget("org.kde.plasma.systemtray")
var clock = topPanel.addWidget("org.kde.plasma.digitalclock")
clock.currentConfigGroup = ["Appearance"]
clock.writeConfig("showDate", true)
clock.writeConfig("dateFormat", "shortDate")

var dock = new Panel
dock.location = "bottom"
dock.height = 58
dock.lengthMode = "fit"
dock.alignment = "center"
dock.floating = true
dock.hiding = "autohide"

var tasks = dock.addWidget("org.kde.plasma.icontasks")
tasks.currentConfigGroup = ["General"]
tasks.writeConfig("launchers", "applications:firefox.desktop,applications:org.kde.dolphin.desktop,applications:org.kde.konsole.desktop,applications:ifba-ai.desktop,applications:systemsettings.desktop")
tasks.writeConfig("maxStripes", 1)
tasks.writeConfig("showOnlyCurrentScreen", true)
