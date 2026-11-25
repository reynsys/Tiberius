import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.workspace.components as PW
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    readonly property color orange: "#f28c38"
    property string longName: ""

    preferredRepresentation: fullRepresentation
    toolTipMainText: longName
    toolTipSubText: "Click to switch the keyboard layout"
    Plasmoid.status: PlasmaCore.Types.ActiveStatus

    FontLoader { id: hudFont; source: "../fonts/Oxanium.ttf" }

    fullRepresentation: PW.KeyboardLayoutSwitcher {
        id: sw
        Layout.minimumWidth: 34
        Layout.preferredWidth: 34
        Layout.maximumWidth: 34
        Layout.minimumHeight: 24
        hoverEnabled: true
        Accessible.name: root.longName
        Accessible.role: Accessible.Button

        Binding { target: root; property: "longName"; value: sw.layoutNames.longName || "" }

        Text {
            anchors.centerIn: parent
            text: (sw.layoutNames.displayName || sw.layoutNames.shortName || "").toUpperCase()
            color: sw.containsMouse ? Qt.lighter(root.orange, 1.2) : root.orange
            font { family: hudFont.name; weight: Font.DemiBold; pixelSize: 16 }
        }
        // the same four corner ticks as the tray icons, in teal
        Item {
            anchors.centerIn: parent
            width: 32; height: 22
            Repeater {
                model: 4
                Item {
                    required property int index
                    readonly property bool r: index % 2 === 1
                    readonly property bool b: index > 1
                    x: r ? parent.width - 5 : 0
                    y: b ? parent.height - 5 : 0
                    width: 5; height: 5
                    Rectangle { width: 5; height: 1; y: parent.b ? 4 : 0; color: "#22d3c5" }
                    Rectangle { width: 1; height: 5; x: parent.r ? 4 : 0; color: "#22d3c5" }
                }
            }
        }
    }
}
