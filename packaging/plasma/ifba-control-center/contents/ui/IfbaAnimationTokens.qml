/* Generated from packaging/design-system/tokens.json. */
import QtQuick
import org.kde.kirigami as Kirigami

QtObject {
    // Kirigami.Units follows KDE's AnimationDurationFactor. KDE clamps the
    // resulting duration to 1 ms, so explicitly disable Behaviors at that floor.
    readonly property bool reducedMotion: Kirigami.Units.longDuration <= 1
    readonly property real kdeDurationScale: Kirigami.Units.longDuration / 240
    readonly property int hoverMs: reducedMotion ? 0 : Math.round(120 * kdeDurationScale)
    readonly property int controlMs: reducedMotion ? 0 : Math.round(180 * kdeDurationScale)
    readonly property int moduleMs: reducedMotion ? 0 : Math.round(180 * kdeDurationScale)
    readonly property int dockMs: reducedMotion ? 0 : Math.round(180 * kdeDurationScale)
    readonly property int windowOpenMs: reducedMotion ? 0 : Math.round(180 * kdeDurationScale)
    readonly property int minimizeMs: reducedMotion ? 0 : Math.round(240 * kdeDurationScale)
    readonly property int overviewMs: reducedMotion ? 0 : Math.round(240 * kdeDurationScale)
    readonly property int lockScreenMs: reducedMotion ? 0 : Math.round(180 * kdeDurationScale)

    readonly property int hoverCurve: Easing.OutCubic
    readonly property int enterCurve: Easing.OutQuint
    readonly property int standardCurve: Easing.InOutCubic
}
