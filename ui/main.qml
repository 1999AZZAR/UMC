import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components"
import "."

ApplicationWindow {
    id: window
    visible: true
    width: 1280; height: 850
    title: "Unified Mobile Controller"
    color: Style.background

    RowLayout {
        anchors.fill: parent; spacing: 0

        DeviceSidebar {
            Layout.fillHeight: true; Layout.preferredWidth: Style.sidebarWidth
        }

        // Main Content Area
        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; spacing: 0

            // Header Section (Glass/Pastel Vibes)
            Rectangle {
                Layout.fillWidth: true; height: Style.headerHeight; color: "transparent"
                
                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: 32; anchors.rightMargin: 32
                    
                    ColumnLayout {
                        spacing: 2
                        Text { text: "Applications"; font: Style.headerFont; color: Style.textPrimary }
                        Text { text: bridge ? bridge.currentDeviceSerial : "No device"; font.pixelSize: 10; color: Style.textDisabled }
                    }
                    
                    Item { Layout.fillWidth: true }
                    
                    // Status Badge (Tonal Container)
                    Rectangle {
                        visible: statusText.text !== ""; height: 36; width: statusText.implicitWidth + 40; radius: 18
                        color: Style.accentVariant; border.color: Style.accent; border.width: 1
                        
                        RowLayout {
                            anchors.centerIn: parent; spacing: 10
                            Rectangle { width: 8; height: 8; radius: 4; color: Style.success }
                            Text { id: statusText; color: Style.accent; font: Style.bodySmallFont }
                        }
                    }
                }
            }
            
            Rectangle { Layout.fillWidth: true; height: 1; color: Style.surfaceHighlight; opacity: 0.5 }
            
            Connections {
                target: bridge
                function onStatusMessage(msg) {
                    statusText.text = msg
                    statusTimer.restart()
                }
            }
            
            Timer { id: statusTimer; interval: 3500; onTriggered: statusText.text = "" }

            AppGrid { Layout.fillWidth: true; Layout.fillHeight: true }
        }
    }
}
