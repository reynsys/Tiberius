import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PC
import org.kde.plasma.clock
import org.kde.plasma.workspace.calendar as PlasmaCalendar
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    readonly property color orange: "#f28c38"
    readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical
    readonly property string timeText: Qt.formatTime(clock.dateTime, Qt.locale().timeFormat(Locale.ShortFormat))
    readonly property string dateText: Qt.formatDate(clock.dateTime, vertical ? "dd/MM" : Qt.locale().dateFormat(Locale.ShortFormat))

    preferredRepresentation: compactRepresentation
    toolTipMainText: Qt.formatDate(clock.dateTime, Qt.locale().dateFormat(Locale.LongFormat))
    toolTipSubText: timeText

    Clock { id: clock }
    FontLoader { id: hudFont; source: "../fonts/Oxanium.ttf" }

    compactRepresentation: MouseArea {
        id: compact
        Layout.minimumWidth: root.vertical ? 0 : Math.ceil(column.implicitWidth) + Kirigami.Units.smallSpacing * 4
        Layout.preferredWidth: Layout.minimumWidth
        Layout.minimumHeight: root.vertical ? Math.ceil(column.implicitHeight) : 0
        hoverEnabled: true
        Accessible.name: root.timeText + " " + root.dateText
        Accessible.role: Accessible.Button
        property bool wasExpanded: false
        onPressed: wasExpanded = root.expanded
        onClicked: root.expanded = !wasExpanded

        Column {
            id: column
            anchors.centerIn: parent
            // the digits keep the same width, so the panel doesn't shift every minute
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.timeText
                color: compact.containsMouse ? Qt.lighter(root.orange, 1.2) : root.orange
                font { family: hudFont.name; weight: Font.DemiBold; pixelSize: Math.round(Math.min(compact.height * 0.5, 22)); features: { "tnum": 1 } }
                height: Math.ceil(font.pixelSize * 1.0)
                verticalAlignment: Text.AlignVCenter
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.dateText
                color: root.orange
                font { family: hudFont.name; weight: Font.DemiBold; pixelSize: Math.round(Math.min(compact.height * 0.4, 17)); features: { "tnum": 1 } }
                height: Math.ceil(font.pixelSize * 1.0)
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    fullRepresentation: ColumnLayout {
        Layout.minimumWidth: Kirigami.Units.gridUnit * 20
        Layout.minimumHeight: Kirigami.Units.gridUnit * 23
        Layout.preferredWidth: Layout.minimumWidth
        Layout.preferredHeight: Layout.minimumHeight
        spacing: Kirigami.Units.smallSpacing

        Text {
            Layout.leftMargin: Kirigami.Units.largeSpacing
            Layout.topMargin: Kirigami.Units.smallSpacing
            text: root.timeText
            color: root.orange
            font { family: hudFont.name; weight: Font.DemiBold; pixelSize: 40; features: { "tnum": 1 } }
        }
        PC.Label {
            Layout.leftMargin: Kirigami.Units.largeSpacing
            text: root.toolTipMainText
            color: "#5ae8dc"
            font.family: hudFont.name
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: "#22d3c5"
            opacity: 0.6
            Rectangle { width: 40; height: 3; color: root.orange }
        }
        PlasmaCalendar.MonthView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            today: clock.dateTime
            eventPluginsManager: PlasmaCalendar.EventPluginsManager {}
            firstDayOfWeek: Qt.locale().firstDayOfWeek
        }
    }
}
