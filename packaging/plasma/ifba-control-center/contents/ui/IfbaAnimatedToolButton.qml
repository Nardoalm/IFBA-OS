/* SPDX-License-Identifier: GPL-3.0-or-later */

import QtQuick
import org.kde.plasma.components as PlasmaComponents3
import "."

PlasmaComponents3.ToolButton {
    id: control

    IfbaAnimationTokens { id: motion }

    scale: !enabled ? 1.0 : down ? 0.96 : hovered ? 1.04 : 1.0
    Behavior on scale {
        enabled: !motion.reducedMotion
        NumberAnimation { duration: motion.hoverMs; easing.type: motion.hoverCurve }
    }
}
