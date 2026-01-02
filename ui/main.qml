import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components"
import "."

ApplicationWindow {
    id: window
    visible: true
    width: 1200
    height: 800
    title: "Unified Mobile Controller"
    color: Style.background

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Sidebar {
            Layout.fillHeight: true
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // Top Bar
            Rectangle {
                Layout.fillWidth: true
                height: 60
                color: "transparent"
                
                Text {
                    anchors.centerIn: parent
                    text: "Applications"
                    font: Style.headerFont
                    color: Style.textPrimary
                }
                
                Text {
                    id: statusText
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.rightMargin: 20
                    color: Style.accent
                    font.pixelSize: 12
                }
            }
            
            Connections {
                target: bridge
                function onStatusMessage(msg) {
                    statusText.text = msg
                    statusTimer.restart()
                }
            }
            
            Timer {
                id: statusTimer
                interval: 3000
                onTriggered: statusText.text = ""
            }

            // Main Content
            AppGrid {
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }
    }
}
