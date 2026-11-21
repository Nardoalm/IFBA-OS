/*
    SPDX-FileCopyrightText: 2026 IFBA OS Project
    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import org.kde.kirigami as Kirigami
import org.kde.plasma.private.sessions
import org.kde.plasma.private.keyboardindicator as KeyboardIndicator
import org.kde.plasma.networkmanagement as PlasmaNM
import org.kde.plasma.private.volume as PlasmaVolume
import org.kde.breeze.components

Item {
    id: ui
    focus: true

    property bool authenticationVisible: false
    property bool passwordlessReady: false
    property string errorText: ""
    property date now: new Date()

    SessionManagement {
        id: sessionManagement
    }

    KeyboardIndicator.KeyState {
        id: capsLock
        key: Qt.Key_CapsLock
    }

    PlasmaNM.NetworkStatus {
        id: networkStatus
    }

    PlasmaNM.ConnectionIcon {
        id: connectionIcon
        connectivity: networkStatus.connectivity
    }

    Timer {
        interval: 1000
        repeat: true
        running: true
        onTriggered: ui.now = new Date()
    }

    Connections {
        target: authenticator

        function onPromptForSecretChanged() {
            ui.authenticationVisible = true
            passwordField.forceActiveFocus()
        }

        function onInfoMessageChanged() {
            if (authenticator.infoMessage.length > 0) {
                ui.errorText = authenticator.infoMessage
            }
        }

        function onErrorMessageChanged() {
            if (authenticator.errorMessage.length > 0) {
                ui.errorText = authenticator.errorMessage
            }
        }

        function onFailed(kind) {
            if (kind !== 0) {
                return
            }
            ui.errorText = authenticator.errorMessage.length > 0
                    ? authenticator.errorMessage
                    : qsTr("Senha incorreta. Tente novamente.")
            passwordField.text = ""
            passwordField.forceActiveFocus()
        }

        function onSucceeded() {
            if (authenticator.hadPrompt) {
                Qt.quit()
            } else {
                // Keep passwordless live sessions behind the native PAM result
                // and require an explicit confirmation, as Plasma does.
                ui.passwordlessReady = true
                ui.authenticationVisible = true
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        z: -1
        onClicked: ui.revealAuthentication()
    }

    function revealAuthentication() {
        if (authenticationVisible) {
            return
        }
        authenticationVisible = true
        errorText = ""
        authenticator.startAuthenticating()
        Qt.callLater(() => passwordField.forceActiveFocus())
    }

    Keys.onPressed: event => {
        if (!authenticationVisible) {
            revealAuthentication()
            event.accepted = true
        }
    }

    ColumnLayout {
        id: clockView
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: parent.height * 0.33
        spacing: 10
        visible: !ui.authenticationVisible

        Controls.Label {
            Layout.alignment: Qt.AlignHCenter
            text: Qt.formatTime(ui.now, "HH:mm")
            color: "#FFFFFF"
            font.family: "Inter"
            font.pixelSize: Math.min(ui.height * 0.108, 128)
            font.weight: Font.DemiBold
        }

        Controls.Label {
            Layout.alignment: Qt.AlignHCenter
            text: Qt.locale("pt_BR").toString(ui.now, "dddd, d 'de' MMMM 'de' yyyy")
            color: "#F4F8F5"
            font.family: "Inter"
            font.pixelSize: Math.min(ui.height * 0.027, 30)
        }

        Controls.Button {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: ui.height * 0.06
            implicitWidth: Math.min(ui.width * 0.72, 590)
            implicitHeight: 76
            focusPolicy: Qt.NoFocus
            onClicked: ui.revealAuthentication()

            background: Rectangle {
                radius: 24
                color: "#40243A31"
                border.width: 1
                border.color: "#60889A90"
            }

            contentItem: RowLayout {
                spacing: 16
                Kirigami.Icon {
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                    source: "object-locked"
                    color: "white"
                }
                Controls.Label {
                    Layout.fillWidth: true
                    text: qsTr("Pressione qualquer tecla para desbloquear")
                    color: "white"
                    font.family: "Inter"
                    font.pixelSize: Math.min(ui.width * 0.016, 23)
                    horizontalAlignment: Text.AlignHCenter
                }
                Item { Layout.preferredWidth: 24 }
            }
        }
    }

    ColumnLayout {
        id: authView
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.88, 430)
        spacing: 14
        visible: ui.authenticationVisible

        Item {
            id: avatar
            property int avatarSize: Math.min(ui.height * 0.14, 148)
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: avatarSize
            Layout.preferredHeight: avatarSize

            Rectangle {
                anchors.fill: parent
                radius: width / 2
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#59D969" }
                    GradientStop { position: 0.55; color: "#208D38" }
                    GradientStop { position: 1.0; color: "#135B2A" }
                }
            }

            Rectangle {
                anchors.fill: parent
                anchors.margins: 2
                radius: width / 2
                color: "#25231B"
            }

            Image {
                id: avatarImage
                anchors.fill: parent
                anchors.margins: 6
                source: kscreenlocker_userImage.length > 0
                        ? (kscreenlocker_userImage.startsWith("file:")
                           ? kscreenlocker_userImage
                           : "file://" + kscreenlocker_userImage)
                        : ""
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                cache: true
                visible: status === Image.Ready
                layer.enabled: true
                layer.effect: OpacityMask {
                    maskSource: Rectangle {
                        width: avatarImage.width
                        height: avatarImage.height
                        radius: width / 2
                    }
                }
            }

            Kirigami.Icon {
                anchors.centerIn: parent
                width: parent.width * 0.55
                height: width
                source: "user-identity"
                color: "#F3F7F4"
                visible: avatarImage.status !== Image.Ready
            }
        }

        Controls.Label {
            Layout.alignment: Qt.AlignHCenter
            text: kscreenlocker_userName
            color: "white"
            font.family: "Inter"
            font.pixelSize: Math.min(ui.height * 0.027, 30)
            font.weight: Font.DemiBold
        }

        Controls.TextField {
            id: passwordField
            Layout.fillWidth: true
            Layout.preferredHeight: 52
            placeholderText: qsTr("Digite sua senha")
            font.family: "Inter"
            font.pixelSize: 18
            color: "#FFFFFF"
            enabled: !authenticator.graceLocked && !ui.passwordlessReady
            echoMode: showPassword.checked ? TextInput.Normal : TextInput.Password
            selectByMouse: false
            focus: true
            onAccepted: submitPassword()

            background: Rectangle {
                radius: 16
                color: "#B3131C18"
                border.width: passwordField.activeFocus ? 2 : 1
                border.color: passwordField.activeFocus ? "#39D353" : "#708B9690"
            }

            leftPadding: 48
            rightPadding: 48

            Kirigami.Icon {
                anchors.left: parent.left
                anchors.leftMargin: 16
                anchors.verticalCenter: parent.verticalCenter
                width: 22
                height: 22
                source: "object-locked"
                color: "#F5F7F5"
            }

            Controls.ToolButton {
                id: showPassword
                anchors.right: parent.right
                anchors.rightMargin: 4
                anchors.verticalCenter: parent.verticalCenter
                width: 42
                height: 42
                checkable: true
                icon.name: checked ? "view-visible" : "view-hidden"
                display: Controls.AbstractButton.IconOnly
                Accessible.name: checked ? qsTr("Ocultar senha") : qsTr("Mostrar senha")
                background: Rectangle { color: "transparent" }
            }
        }

        Controls.Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            visible: capsLock.locked || ui.errorText.length > 0
            text: capsLock.locked && ui.errorText.length > 0
                  ? qsTr("Caps Lock ativado · %1").arg(ui.errorText)
                  : (capsLock.locked ? qsTr("Caps Lock ativado") : ui.errorText)
            color: ui.errorText.length > 0 ? "#FFB4AB" : "#F3F5F3"
            font.family: "Inter"
            font.pixelSize: 15
            wrapMode: Text.Wrap
        }

        Controls.Button {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 8
            implicitWidth: Math.min(parent.width * 0.58, 230)
            implicitHeight: 50
            enabled: ui.passwordlessReady || (!authenticator.graceLocked && passwordField.text.length > 0)
            text: ui.passwordlessReady ? qsTr("Desbloquear") : qsTr("Desbloquear  ›")
            onClicked: ui.passwordlessReady ? Qt.quit() : submitPassword()

            background: Rectangle {
                radius: 16
                color: parent.enabled ? (parent.hovered ? "#2BA647" : "#208D38") : "#6A756D"
            }
            contentItem: Controls.Label {
                text: parent.text
                color: "white"
                font.family: "Inter"
                font.pixelSize: 18
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    function submitPassword() {
        if (passwordlessReady || authenticator.graceLocked || passwordField.text.length === 0) {
            return
        }
        errorText = ""
        authenticator.respond(passwordField.text)
    }

    RowLayout {
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: 28
        spacing: 12

        Controls.ToolButton {
            visible: sessionManagement.canSwitchUser
            icon.name: "system-switch-user"
            Accessible.name: qsTr("Alternar usuário")
            onClicked: sessionManagement.switchUser()
            background: Rectangle { radius: width / 2; color: "#39283A32"; border.color: "#548B9690" }
        }
        Controls.ToolButton {
            visible: sessionManagement.canReboot
            icon.name: "system-reboot"
            Accessible.name: qsTr("Reiniciar")
            onClicked: sessionManagement.requestReboot()
            background: Rectangle { radius: width / 2; color: "#39283A32"; border.color: "#548B9690" }
        }
        Controls.ToolButton {
            visible: sessionManagement.canShutdown
            icon.name: "system-shutdown"
            Accessible.name: qsTr("Desligar")
            onClicked: sessionManagement.requestShutdown()
            background: Rectangle { radius: width / 2; color: "#39283A32"; border.color: "#548B9690" }
        }
    }

    RowLayout {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 28
        spacing: 18

        Kirigami.Icon {
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
            source: connectionIcon.connectionIcon.length > 0
                    ? connectionIcon.connectionIcon + "-symbolic" : ""
            visible: source.length > 0
            color: "white"
            Accessible.name: qsTr("Estado da conectividade")
        }

        Kirigami.Icon {
            readonly property var output: PlasmaVolume.PreferredDevice.sink
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
            source: output
                    ? PlasmaVolume.AudioIcon.forVolume(
                          Math.round(output.volume / PlasmaVolume.PulseAudio.NormalVolume * 100),
                          output.muted, "")
                    : ""
            visible: source.length > 0
            color: "white"
            Accessible.name: qsTr("Estado do volume")
        }

        Battery {}
    }

}
