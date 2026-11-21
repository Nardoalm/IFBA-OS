/* SPDX-License-Identifier: GPL-3.0-or-later */

import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCMUtils
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore

import org.kde.plasma.networkmanagement as NetworkManagement
import org.kde.bluezqt as BluezQt
import org.kde.plasma.private.volume
import org.kde.plasma.private.brightnesscontrolplugin
import org.kde.plasma.workspace.dbus as DBus
import org.kde.plasma.private.batterymonitor
import org.kde.plasma.private.battery
import plasma.applet.org.kde.plasma.notifications as Notifications
import org.kde.plasma.private.mpris as Mpris

PlasmoidItem {
    id: root

    readonly property bool bluetoothAvailable: BluezQt.Manager.operational && BluezQt.Manager.adapters.length > 0
    readonly property bool hasOutput: Context.state === Context.State.Ready
        && preferredDevice.sink !== null && preferredDevice.sink.name !== "auto_null"
    readonly property var currentPlayer: mprisModel.currentPlayer

    switchWidth: Kirigami.Units.gridUnit * 24
    switchHeight: Kirigami.Units.gridUnit * 27
    toolTipMainText: i18n("Central de controle")
    toolTipSubText: i18n("Rede, áudio, tela, sistema e reprodução")
    Plasmoid.title: i18n("Central de controle")
    Plasmoid.icon: "settings-configure"
    Plasmoid.status: PlasmaCore.Types.ActiveStatus

    compactRepresentation: PlasmaComponents3.ToolButton {
        id: controlButton
        icon.name: "settings-configure"
        text: i18n("Controle")
        display: PlasmaComponents3.AbstractButton.IconOnly
        Accessible.name: i18n("Abrir central de controle")
        Accessible.description: root.toolTipSubText
        onClicked: root.expanded = !root.expanded
    }

    fullRepresentation: PlasmaExtras.Representation {
        id: panel
        collapseMarginsHint: true
        Layout.minimumWidth: Kirigami.Units.gridUnit * 23
        Layout.maximumWidth: Kirigami.Units.gridUnit * 29
        Layout.minimumHeight: Kirigami.Units.gridUnit * 24
        Layout.maximumHeight: Kirigami.Units.gridUnit * 34
        focus: true
        Keys.onEscapePressed: root.expanded = false

        PlasmaComponents3.ScrollView {
            id: scroller
            anchors.fill: parent
            background: null
            PlasmaComponents3.ScrollBar.vertical: PlasmaComponents3.ScrollBar { }

            contentItem: ColumnLayout {
                id: controls
                width: scroller.availableWidth
                spacing: Kirigami.Units.smallSpacing

                PlasmaComponents3.Label {
                    Layout.fillWidth: true
                    text: i18n("Central de controle")
                    font: Kirigami.Theme.defaultFont
                    font.bold: true
                    font.pointSize: Kirigami.Theme.defaultFont.pointSize + 2
                    Accessible.role: Accessible.Heading
                }

                // A compact connection summary and Wi-Fi switch backed by NetworkManager.
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: networkLayout.implicitHeight + Kirigami.Units.largeSpacing * 2
                    radius: Kirigami.Units.largeSpacing
                    color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g,
                                   Kirigami.Theme.textColor.b, 0.06)
                    visible: networkDevices.wiredDeviceAvailable || networkDevices.wirelessDeviceAvailable
                    ColumnLayout {
                        id: networkLayout
                        anchors.fill: parent
                        anchors.margins: Kirigami.Units.largeSpacing
                        RowLayout {
                            Layout.fillWidth: true
                            Kirigami.Icon { source: "network-wired-activated"; implicitWidth: Kirigami.Units.iconSizes.medium; implicitHeight: implicitWidth }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 0
                                PlasmaComponents3.Label { text: i18n("Rede"); font.bold: true }
                                PlasmaComponents3.Label {
                                    Layout.fillWidth: true
                                    text: networkStatus.activeConnections || i18n("Sem conexão ativa")
                                    opacity: 0.75
                                    elide: Text.ElideRight
                                }
                            }
                            PlasmaComponents3.Switch {
                                visible: networkDevices.wirelessDeviceAvailable && networkState.wirelessHwEnabled
                                enabled: visible
                                checked: networkState.wirelessEnabled
                                text: i18n("Wi-Fi")
                                Accessible.name: i18n("Ativar Wi-Fi")
                                onToggled: networkHandler.enableWireless(checked)
                            }
                        }
                        PlasmaComponents3.Button {
                            Layout.alignment: Qt.AlignRight
                            text: i18n("Configurações de rede")
                            icon.name: "configure"
                            onClicked: KCMUtils.KCMLauncher.openSystemSettings("kcm_networkmanagement")
                        }
                    }
                }

                // BlueZ owns adapter state and the list of connected devices.
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: bluetoothLayout.implicitHeight + Kirigami.Units.largeSpacing * 2
                    radius: Kirigami.Units.largeSpacing
                    color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g,
                                   Kirigami.Theme.textColor.b, 0.06)
                    visible: root.bluetoothAvailable
                    ColumnLayout {
                        id: bluetoothLayout
                        anchors.fill: parent
                        anchors.margins: Kirigami.Units.largeSpacing
                        RowLayout {
                            PlasmaComponents3.Label { Layout.fillWidth: true; text: i18n("Bluetooth"); font.bold: true }
                            PlasmaComponents3.Switch {
                                checked: BluezQt.Manager.bluetoothOperational
                                text: checked ? i18n("Ativado") : i18n("Desativado")
                                Accessible.name: i18n("Ativar Bluetooth")
                                onToggled: BluezQt.Manager.bluetoothBlocked = !checked
                            }
                        }
                        PlasmaComponents3.Label {
                            Layout.fillWidth: true
                            visible: BluezQt.Manager.bluetoothOperational && BluezQt.Manager.connectedDevices.length > 0
                            text: BluezQt.Manager.connectedDevices.map(device => device.name).join(", ")
                            wrapMode: Text.Wrap
                            opacity: 0.75
                        }
                        PlasmaComponents3.Label {
                            visible: BluezQt.Manager.bluetoothOperational && BluezQt.Manager.connectedDevices.length === 0
                            text: i18n("Nenhum dispositivo conectado")
                            opacity: 0.75
                        }
                        PlasmaComponents3.Button {
                            Layout.alignment: Qt.AlignRight
                            text: i18n("Configurações de Bluetooth")
                            icon.name: "configure"
                            onClicked: KCMUtils.KCMLauncher.openSystemSettings("kcm_bluetooth")
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: audioLayout.implicitHeight + Kirigami.Units.largeSpacing * 2
                    radius: Kirigami.Units.largeSpacing
                    color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g,
                                   Kirigami.Theme.textColor.b, 0.06)
                    visible: Context.state === Context.State.Ready && sinkFilterModel.count > 0
                    ColumnLayout {
                        id: audioLayout
                        anchors.fill: parent
                        anchors.margins: Kirigami.Units.largeSpacing
                        RowLayout {
                            PlasmaComponents3.Label { Layout.fillWidth: true; text: i18n("Áudio"); font.bold: true }
                            PlasmaComponents3.Label {
                                text: root.hasOutput ? Math.round(preferredDevice.sink.volume / PulseAudio.NormalVolume * 100) + "%" : ""
                                opacity: 0.75
                            }
                            PlasmaComponents3.ToolButton {
                                icon.name: preferredDevice.sink && preferredDevice.sink.muted ? "audio-volume-muted" : "audio-volume-high"
                                Accessible.name: preferredDevice.sink && preferredDevice.sink.muted ? i18n("Ativar som") : i18n("Silenciar")
                                enabled: root.hasOutput
                                onClicked: preferredDevice.sink.muted = !preferredDevice.sink.muted
                            }
                        }
                        PlasmaComponents3.Slider {
                            Layout.fillWidth: true
                            visible: root.hasOutput
                            from: 0
                            to: 150
                            value: root.hasOutput ? preferredDevice.sink.volume / PulseAudio.NormalVolume * 100 : 0
                            Accessible.name: i18n("Volume de saída")
                            onMoved: if (root.hasOutput) preferredDevice.sink.volume = value * PulseAudio.NormalVolume / 100
                        }
                        PlasmaComponents3.Label { visible: !root.hasOutput; text: i18n("Nenhuma saída de áudio disponível") }
                        PlasmaComponents3.Label { visible: sinkFilterModel.count > 1; text: i18n("Saída de áudio"); opacity: 0.75 }
                        Flow {
                            Layout.fillWidth: true
                            visible: sinkFilterModel.count > 1
                            spacing: Kirigami.Units.smallSpacing
                            Repeater {
                                model: sinkFilterModel
                                delegate: PlasmaComponents3.Button {
                                    required property var model
                                    text: model.Description
                                    checkable: true
                                    checked: model.PulseObject === preferredDevice.sink
                                    Accessible.name: i18n("Usar saída de áudio %1", text)
                                    onClicked: model.PulseObject.default = true
                                }
                            }
                        }
                        PlasmaComponents3.Button {
                            Layout.alignment: Qt.AlignRight
                            text: i18n("Configurações de áudio")
                            icon.name: "configure"
                            onClicked: KCMUtils.KCMLauncher.openSystemSettings("kcm_pulseaudio")
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: displayLayout.implicitHeight + Kirigami.Units.largeSpacing * 2
                    radius: Kirigami.Units.largeSpacing
                    color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g,
                                   Kirigami.Theme.textColor.b, 0.06)
                    visible: brightness.isBrightnessAvailable || nightLight.available
                    ColumnLayout {
                        id: displayLayout
                        anchors.fill: parent
                        anchors.margins: Kirigami.Units.largeSpacing
                        PlasmaComponents3.Label { text: i18n("Tela"); font.bold: true }
                        Repeater {
                            model: brightness.displays
                            delegate: RowLayout {
                                required property string displayName
                                required property string label
                                required property int brightness
                                required property int maxBrightness
                                visible: maxBrightness > 0
                                PlasmaComponents3.Label { text: label; Layout.preferredWidth: Kirigami.Units.gridUnit * 5; elide: Text.ElideRight }
                                PlasmaComponents3.Slider {
                                    Layout.fillWidth: true
                                    from: 0
                                    to: maxBrightness
                                    value: brightness
                                    Accessible.name: i18n("Brilho de %1", label)
                                    onMoved: root.setDisplayBrightness(displayName, value)
                                }
                            }
                        }
                        PlasmaComponents3.Label {
                            visible: !brightness.isBrightnessAvailable
                            text: i18n("Controle de brilho indisponível neste dispositivo")
                            opacity: 0.75
                        }
                        PlasmaComponents3.Switch {
                            visible: nightLight.available && nightLight.enabled
                            enabled: nightLight.togglable
                            checked: nightLight.inhibited
                            text: i18n("Suspender luz noturna")
                            Accessible.name: i18n("Suspender ou retomar a luz noturna")
                            onToggled: NightLightInhibitor.toggleInhibition()
                        }
                        PlasmaComponents3.Button {
                            Layout.alignment: Qt.AlignRight
                            text: i18n("Configurações de tela")
                            icon.name: "configure"
                            onClicked: KCMUtils.KCMLauncher.openSystemSettings("kcm_kscreen")
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: systemLayout.implicitHeight + Kirigami.Units.largeSpacing * 2
                    radius: Kirigami.Units.largeSpacing
                    color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g,
                                   Kirigami.Theme.textColor.b, 0.06)
                    visible: battery.hasBatteries || powerProfiles.profiles.length > 0 || notificationsReady
                    ColumnLayout {
                        id: systemLayout
                        anchors.fill: parent
                        anchors.margins: Kirigami.Units.largeSpacing
                        PlasmaComponents3.Label { text: i18n("Sistema"); font.bold: true }
                        PlasmaComponents3.Label {
                            visible: battery.hasBatteries
                            text: batteryStatusText
                            Accessible.name: i18n("Estado da bateria")
                        }
                        PlasmaComponents3.Label { visible: powerProfiles.profiles.length > 0; text: i18n("Perfil de energia") }
                        RowLayout {
                            visible: powerProfiles.profiles.length > 0
                            Repeater {
                                model: [
                                    { id: "power-saver", label: i18n("Economia") },
                                    { id: "balanced", label: i18n("Equilibrado") },
                                    { id: "performance", label: i18n("Desempenho") }
                                ]
                                delegate: PlasmaComponents3.Button {
                                    required property var modelData
                                    visible: powerProfiles.profiles.includes(modelData.id)
                                    text: modelData.label
                                    checkable: true
                                    checked: powerProfiles.activeProfile === modelData.id
                                    enabled: modelData.id !== "performance" || !powerProfiles.inhibitionReason
                                    Accessible.name: i18n("Perfil de energia %1", text)
                                    onClicked: powerProfiles.setProfile(modelData.id)
                                }
                            }
                        }
                        PlasmaComponents3.Switch {
                            visible: notificationsReady
                            checked: Notifications.Globals.inhibited
                            text: i18n("Não perturbe")
                            Accessible.name: i18n("Ativar não perturbe")
                            onToggled: Notifications.Globals.toggleDoNotDisturbMode()
                        }
                        PlasmaComponents3.Button {
                            Layout.alignment: Qt.AlignRight
                            text: i18n("Informações do sistema")
                            icon.name: "configure"
                            onClicked: KCMUtils.KCMLauncher.openSystemSettings("kcm_about-distro")
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: mediaLayout.implicitHeight + Kirigami.Units.largeSpacing * 2
                    radius: Kirigami.Units.largeSpacing
                    color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g,
                                   Kirigami.Theme.textColor.b, 0.06)
                    visible: !!root.currentPlayer
                    ColumnLayout {
                        id: mediaLayout
                        anchors.fill: parent
                        anchors.margins: Kirigami.Units.largeSpacing
                        PlasmaComponents3.Label { text: i18n("Multimídia"); font.bold: true }
                        PlasmaComponents3.Label {
                            Layout.fillWidth: true
                            text: root.currentPlayer ? root.currentPlayer.track : ""
                            font.bold: true
                            elide: Text.ElideRight
                        }
                        PlasmaComponents3.Label {
                            Layout.fillWidth: true
                            text: root.currentPlayer ? [root.currentPlayer.artist, root.currentPlayer.identity].filter(Boolean).join(" · ") : ""
                            opacity: 0.75
                            elide: Text.ElideRight
                        }
                        RowLayout {
                            Layout.alignment: Qt.AlignHCenter
                            PlasmaComponents3.ToolButton {
                                icon.name: "media-skip-backward"
                                Accessible.name: i18n("Faixa anterior")
                                enabled: root.currentPlayer && root.currentPlayer.canGoPrevious
                                onClicked: root.currentPlayer.Previous()
                            }
                            PlasmaComponents3.ToolButton {
                                icon.name: root.currentPlayer && root.currentPlayer.playbackStatus === Mpris.PlaybackStatus.Playing
                                    ? "media-playback-pause" : "media-playback-start"
                                Accessible.name: root.currentPlayer && root.currentPlayer.playbackStatus === Mpris.PlaybackStatus.Playing
                                    ? i18n("Pausar") : i18n("Reproduzir")
                                enabled: root.currentPlayer && (root.currentPlayer.playbackStatus === Mpris.PlaybackStatus.Playing
                                    ? root.currentPlayer.canPause : root.currentPlayer.canPlay)
                                onClicked: root.currentPlayer.playbackStatus === Mpris.PlaybackStatus.Playing
                                    ? root.currentPlayer.Pause() : root.currentPlayer.Play()
                            }
                            PlasmaComponents3.ToolButton {
                                icon.name: "media-skip-forward"
                                Accessible.name: i18n("Próxima faixa")
                                enabled: root.currentPlayer && root.currentPlayer.canGoNext
                                onClicked: root.currentPlayer.Next()
                            }
                        }
                    }
                }
            }
        }
    }

    NetworkManagement.EnabledConnections { id: networkState }
    NetworkManagement.AvailableDevices { id: networkDevices }
    NetworkManagement.NetworkStatus { id: networkStatus }
    NetworkManagement.Handler { id: networkHandler }

    SinkModel { id: sinkModel }
    PulseObjectFilterModel {
        id: sinkFilterModel
        sourceModel: sinkModel
        filterOutInactiveDevices: true
        filterVirtualDevices: true
    }
    PreferredDevice { id: preferredDevice }

    ScreenBrightnessControl { id: brightness }
    NightLightInhibitor { id: nightLightInhibitor }

    DBus.Properties {
        id: nightLight
        busType: DBus.BusType.Session
        service: "org.kde.KWin.NightLight"
        path: "/org/kde/KWin/NightLight"
        iface: "org.kde.KWin.NightLight"
        readonly property bool available: Boolean(properties.available)
        readonly property bool enabled: Boolean(properties.enabled)
        readonly property bool togglable: !Boolean(properties.inhibited) || nightLightInhibitor.inhibited
        readonly property bool inhibited: Boolean(properties.inhibited)
    }

    PowerProfilesControl { id: powerProfiles }
    BatteryControlModel { id: battery }
    Mpris.Mpris2Model { id: mprisModel }

    readonly property bool notificationsReady: typeof Notifications.Globals !== "undefined"
    readonly property string batteryStatusText: {
        if (!battery.hasBatteries) return "";
        const percent = Math.round(battery.percent) + "%";
        if (battery.pluggedIn) return i18n("Bateria: %1 · conectado à energia", percent);
        return i18n("Bateria: %1", percent);
    }

    function setDisplayBrightness(displayName, value) {
        brightness.setBrightness(displayName, Math.round(value));
    }
}
