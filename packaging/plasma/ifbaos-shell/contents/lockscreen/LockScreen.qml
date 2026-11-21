/*
    SPDX-FileCopyrightText: 2026 IFBA OS Project
    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick

Item {
    id: root

    // KScreenLocker reads these properties and signals from the shell package.
    property bool debug: false
    property string notification
    property bool viewVisible: false
    property bool suspendToRamSupported: false
    property bool suspendToDiskSupported: false
    property bool locked: false

    signal clearPassword()
    signal notificationRepeated()
    signal unlockRequested()
    signal suspendToRam()
    signal suspendToDisk()

    implicitWidth: 800
    implicitHeight: 600

    LockScreenUi {
        anchors.fill: parent
    }
}
