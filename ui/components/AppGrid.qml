import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."

Item {
    id: root
    
    // Model is now handled in Python (bridge.packagesModel)
    // We use bridge.packagesModel.filterText for searching

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Style.spacingLarge
        spacing: Style.spacingMedium

        // Search Bar Area
        Item {
            Layout.fillWidth: true
            height: 50
            
            Rectangle {
                anchors.centerIn: parent
                width: Math.min(parent.width, 600)
                height: 44
                radius: 22
                color: Style.surfaceLight
                border.color: searchField.activeFocus ? Style.accent : "transparent"
                border.width: 1
                
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 15
                    anchors.rightMargin: 15
                    spacing: 10
                    
                    Icon {
                        name: "search"
                        size: 14
                        color: Style.textSecondary
                    }
                    
                    TextField {
                        id: searchField
                        Layout.fillWidth: true
                        placeholderText: "Search applications..."
                        color: Style.textPrimary
                        font: Style.bodyFont
                        background: null
                        selectByMouse: true
                        // FIX: Directly update the model's filter text
                        onTextChanged: {
                            if (bridge && bridge.packagesModel) {
                                bridge.packagesModel.filterText = text.trim()
                            }
                        }
                    }
                    
                    // Clear button
                    Item {
                        width: 16
                        height: 16
                        visible: searchField.text.length > 0
                        
                        Text {
                            anchors.centerIn: parent
                            text: "✕"
                            color: Style.textSecondary
                            font.pixelSize: 12
                        }
                        
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: searchField.text = ""
                        }
                    }
                }
            }
        }

        // Grid
        GridView {
            id: appGridView
            Layout.fillWidth: true
            Layout.fillHeight: true
            cellWidth: 140
            cellHeight: 160
            clip: true
            
            // Use the Python model directly
            model: bridge ? bridge.packagesModel : null
            
            delegate: Item {
                width: 140
                height: 160
                
                Rectangle {
                    id: cardBg
                    width: 120
                    height: 140
                    anchors.centerIn: parent
                    color: Style.surface
                    radius: Style.cornerRadius
                    border.color: mouseArea.containsMouse ? Style.accent : Style.surfaceLight
                    border.width: mouseArea.containsMouse ? 1 : 1
                    
                    scale: mouseArea.containsMouse ? 1.02 : 1.0
                    Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutQuad } }
                    Behavior on border.color { ColorAnimation { duration: 150 } }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8
                        
                        // Icon
                        Rectangle {
                            Layout.alignment: Qt.AlignHCenter
                            width: 56
                            height: 56
                            radius: 18
                            color: Style.surfaceLight
                            border.color: Style.surfaceHighlight
                            border.width: 1
                            clip: true

                            Image {
                                id: appIconImage
                                anchors.fill: parent
                                anchors.margins: 2
                                // Use the 'icon' role from the model
                                source: icon ? "file://" + icon : ""
                                fillMode: Image.PreserveAspectFit
                                visible: icon !== undefined && icon !== "" && status === Image.Ready
                                smooth: true
                                antialiasing: true
                                asynchronous: true
                                
                                Component.onCompleted: {
                                    if (!icon && bridge) {
                                        bridge.fetch_icon_for_package(package)
                                    }
                                }
                            }
                            
                            // NO MORE INDIVIDUAL CONNECTIONS HERE!
                            // The model update triggers dataChanged which updates the Image source automatically.

                            Text {
                                anchors.centerIn: parent
                                text: (name || package || "").substring(0, 1).toUpperCase()
                                color: Style.accent
                                font.bold: true
                                font.pixelSize: 24
                                font.family: Style.headerFont.family
                                visible: !appIconImage.visible || appIconImage.status !== Image.Ready
                            }
                        }
                        
                        Text {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            text: name || package || ""
                            color: Style.textPrimary
                            wrapMode: Text.Wrap
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignTop
                            elide: Text.ElideMiddle
                            maximumLineCount: 3
                            font: Style.bodySmallFont
                        }
                    }
                    
                    MouseArea {
                        id: mouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: bridge.launch_app(package)
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        
                        onPressAndHold: {
                            if (mouse.button === Qt.RightButton) {
                                batchMenu.open()
                            }
                        }
                    }
                    
                    // Batch launch menu
                    Menu {
                        id: batchMenu
                        y: parent.height
                        
                        background: Rectangle {
                            color: Style.surface
                            border.color: Style.divider
                            radius: 4
                        }
                        
                        MenuItem {
                            text: "Launch on Selected Device"
                            font: Style.bodySmallFont
                            onTriggered: bridge.launch_app(package)
                            
                            contentItem: Row {
                                spacing: 8
                                leftPadding: 8
                                Icon {
                                    name: "play_arrow"
                                    size: 14
                                    color: parent.parent.highlighted ? Style.accent : Style.textSecondary
                                }
                                Text {
                                    text: parent.parent.text
                                    font: parent.parent.font
                                    color: parent.parent.highlighted ? Style.accent : Style.textPrimary
                                }
                            }
                            background: Rectangle {
                                color: parent.highlighted ? Style.surfaceLight : "transparent"
                            }
                        }
                        
                        MenuSeparator {
                            contentItem: Rectangle {
                                width: parent.width
                                height: 1
                                color: Style.divider
                            }
                        }
                        
                        MenuItem {
                            text: "Launch on All Devices"
                            font: Style.bodySmallFont
                            onTriggered: {
                                if (bridge) {
                                    var devices = bridge.devices || []
                                    var serials = []
                                    for (var i = 0; i < devices.length; i++) {
                                        if (devices[i].serial) {
                                            serials.push(devices[i].serial)
                                        }
                                    }
                                    bridge.launch_app_on_multiple_devices(package, serials)
                                }
                            }
                            
                            contentItem: Row {
                                spacing: 8
                                leftPadding: 8
                                Icon {
                                    name: "devices"
                                    size: 14
                                    color: parent.parent.highlighted ? Style.accent : Style.textSecondary
                                }
                                Text {
                                    text: parent.parent.text
                                    font: parent.parent.font
                                    color: parent.parent.highlighted ? Style.accent : Style.textPrimary
                                }
                            }
                            background: Rectangle {
                                color: parent.highlighted ? Style.surfaceLight : "transparent"
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Empty State
    Item {
        anchors.centerIn: parent
        visible: bridge && bridge.packagesModel.rowCount() === 0 && searchField.text === ""
        width: 300
        height: 200
        
        ColumnLayout {
            anchors.centerIn: parent
            spacing: 20
            
            Icon {
                Layout.alignment: Qt.AlignHCenter
                name: "device_tablet"
                size: 64
                color: Style.surfaceHighlight
            }
            
            Text {
                text: "Select a device to view apps"
                color: Style.textSecondary
                font: Style.subHeaderFont
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }
}
