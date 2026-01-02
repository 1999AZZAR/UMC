import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."

Rectangle {
    id: sidebar
    width: Style.sidebarWidth
    height: parent.height
    color: Qt.rgba(Style.surface.r, Style.surface.g, Style.surface.b, 0.85) // Translucent
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        Text {
            text: "UMC"
            font: Style.headerFont
            color: Style.accent
            Layout.alignment: Qt.AlignHCenter
        }
        
        Rectangle {
            height: 1
            Layout.fillWidth: true
            color: Style.surfaceLight
        }

        ListView {
            id: deviceList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: bridge ? bridge.devices : []
            
            delegate: ItemDelegate {
                width: parent.width
                
                contentItem: Column {
                    Text {
                        text: modelData.model
                        color: Style.textPrimary
                        font.bold: true
                    }
                    Text {
                        text: modelData.serial
                        color: Style.textSecondary
                        font.pixelSize: 12
                    }
                }
                
                background: Rectangle {
                    color: parent.highlighted || parent.hovered ? Style.surfaceLight : "transparent"
                    radius: 8
                }
                
                onClicked: {
                    bridge.select_device(modelData.serial)
                }
            }
        }
        
        Button {
            text: "Refresh"
            Layout.fillWidth: true
            onClicked: bridge.refresh_devices()
            
            background: Rectangle {
                color: Style.surfaceLight
                radius: 8
            }
            contentItem: Text {
                text: parent.text
                color: Style.textPrimary
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        Rectangle {
            height: 1
            Layout.fillWidth: true
            color: Style.surfaceLight
        }

        Text {
            text: "Launch Mode"
            color: Style.textSecondary
            font.pixelSize: 12
            font.bold: true
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            
            Repeater {
                model: ["Tablet", "Phone"]
                delegate: Rectangle {
                    Layout.fillWidth: true
                    height: 35
                    radius: 6
                    color: bridge && bridge.launchMode === modelData ? Style.accent : Style.surfaceLight
                    
                    Text {
                        anchors.centerIn: parent
                        text: modelData
                        color: bridge && bridge.launchMode === modelData ? "white" : Style.textPrimary
                        font.pixelSize: 12
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        onClicked: if (bridge) bridge.launchMode = modelData
                    }
                }
            }
        }
    }
}
