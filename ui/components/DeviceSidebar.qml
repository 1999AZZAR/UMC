import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."

Rectangle {
    id: sidebar
    width: Style.sidebarWidth
    height: parent.height
    color: Style.surface
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Style.spacingMedium
        spacing: Style.spacingMedium

        // App Title / Logo Area
        Item {
            Layout.fillWidth: true
            height: 40
            
            RowLayout {
                anchors.centerIn: parent
                spacing: 10
                
                Rectangle {
                    width: 32
                    height: 32
                    radius: 8
                    color: Style.accent
                    
                    Text {
                        anchors.centerIn: parent
                        text: "U"
                        color: "white"
                        font.bold: true
                        font.pixelSize: 18
                    }
                }
                
                Text {
                    text: "UMC"
                    font: Style.headerFont
                    color: Style.textPrimary
                }
            }
        }
        
        Rectangle {
            height: 1
            Layout.fillWidth: true
            color: Style.divider
        }

        // Devices Header
        RowLayout {
            Layout.fillWidth: true
            
            Text {
                text: "Connected Devices"
                font: Style.bodySmallFont
                color: Style.textSecondary
                Layout.fillWidth: true
            }
            
            // Refresh Button (Icon style)
            Rectangle {
                width: 28
                height: 28
                radius: 14
                color: refreshArea.containsMouse ? Style.surfaceLight : "transparent"
                
                Text {
                    anchors.centerIn: parent
                    text: "↻" // Simple unicode icon
                    color: Style.accent
                    font.bold: true
                    font.pixelSize: 16
                    rotation: refreshArea.pressed ? 180 : 0
                    Behavior on rotation { NumberAnimation { duration: 200 } }
                }
                
                MouseArea {
                    id: refreshArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: bridge.refresh_devices()
                }
            }
        }

        // Device List
        ListView {
            id: deviceList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: bridge ? bridge.devices : []
            spacing: 5
            
            delegate: Rectangle {
                id: deviceDelegate
                width: ListView.view.width
                height: 60
                radius: Style.cornerRadius
                color: {
                    if (bridge && bridge.currentDeviceSerial === modelData.serial) return Style.surfaceHighlight
                    return ma.containsMouse ? Style.surfaceLight : "transparent"
                }
                
                property bool isSelected: bridge && bridge.currentDeviceSerial === modelData.serial

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 12
                    
                    // Device Icon
                    Rectangle {
                        width: 36
                        height: 36
                        radius: 18
                        color: parent.parent.isSelected ? Style.accent : Style.surfaceLight
                        
                        Text {
                            anchors.centerIn: parent
                            text: "📱"
                            font.pixelSize: 18
                        }
                    }
                    
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        
                        Text {
                            text: modelData.model
                            color: Style.textPrimary
                            font.family: Style.bodyFont.family
                            font.pointSize: Style.bodyFont.pointSize
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: modelData.serial
                            color: Style.textSecondary
                            font.pixelSize: 10
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }
                }
                
                MouseArea {
                    id: ma
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        bridge.select_device(modelData.serial)
                    }
                }
            }
        }
        
        Rectangle {
            height: 1
            Layout.fillWidth: true
            color: Style.divider
        }

        // Launch Mode Section
        ColumnLayout {
            Layout.fillWidth: true
            spacing: Style.spacingSmall

            Text {
                text: "Launch Mode"
                color: Style.textSecondary
                font: Style.bodySmallFont
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                
                Repeater {
                    model: ["Tablet", "Phone"]
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        height: 40
                        radius: Style.cornerRadius
                        
                        property bool isActive: bridge && bridge.launchMode === modelData
                        
                        color: isActive ? Style.accentVariant : Style.surfaceLight
                        border.color: isActive ? Style.accent : "transparent"
                        border.width: 1
                        
                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            color: parent.isActive ? "white" : Style.textSecondary
                            font: Style.bodyFont
                        }
                        
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: if (bridge) bridge.launchMode = modelData
                        }
                    }
                }
            }
        }
    }
}
