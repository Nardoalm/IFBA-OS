var panel = new Panel
panel.location = "bottom"
panel.height = 48
panel.lengthMode = "fill"
panel.alignment = "center"
panel.floating = true
panel.hiding = "none"

var launcher = panel.addWidget("org.kde.plasma.kickoff")
launcher.currentConfigGroup = ["General"]
launcher.writeConfig("favorites", "applications:ifba-ai.desktop,applications:firefox.desktop,applications:org.kde.dolphin.desktop,applications:org.kde.konsole.desktop,applications:systemsettings.desktop")

var tasks = panel.addWidget("org.kde.plasma.icontasks")
tasks.currentConfigGroup = ["General"]
tasks.writeConfig("launchers", "applications:ifba-ai.desktop,applications:firefox.desktop,applications:org.kde.dolphin.desktop,applications:org.kde.konsole.desktop")

panel.addWidget("org.kde.plasma.systemtray")
panel.addWidget("org.kde.plasma.digitalclock")
