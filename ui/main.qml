import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components"
import "."

ApplicationWindow {
    id: window
    visible: true
    width: 1280
    height: 850
    title: "Unified Mobile Controller"
    color: Style.background

    RowLayout {
        anchors.fill: parent
        spacing: 0

        DeviceSidebar {
            Layout.fillHeight: true
            Layout.preferredWidth: Style.sidebarWidth
        }

        // Main Content Area
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // Header
            Rectangle {
                Layout.fillWidth: true
                height: Style.headerHeight
                color: Style.background
                
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: Style.spacingLarge
                    anchors.rightMargin: Style.spacingLarge
                    
                    Text {
                        text: "Applications"
                        font: Style.headerFont
                        color: Style.textPrimary
                    }
                    
                    Item { Layout.fillWidth: true } // Spacer
                    
                    // Status Badge
                    Rectangle {
                        visible: statusText.text !== ""
                        height: 32
                        implicitWidth: statusText.implicitWidth + 30
                        width: implicitWidth
                        radius: 16
                        color: Style.surfaceLight
                        
                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 8
                            
                            Rectangle {
                                width: 8
                                height: 8
                                radius: 4
                                color: Style.accent
                            }
                            
                            Text {
                                id: statusText
                                color: Style.textPrimary
                                font: Style.bodySmallFont
                            }
                        }
                    }
                }
            }
            
            // Bottom divider for header (Moved out to ColumnLayout)
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Style.surfaceLight
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
