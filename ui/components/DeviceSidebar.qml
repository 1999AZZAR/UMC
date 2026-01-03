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
        anchors.margins: 0
        spacing: 0

        // App Header
        Rectangle {
            Layout.fillWidth: true
            height: Style.headerHeight
            color: Style.background
            
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Style.spacingMedium
                anchors.rightMargin: Style.spacingMedium
                spacing: 12
                
                Rectangle {
                    width: 24
                    height: 24
                    radius: 4
                    color: Style.accent
                    
                    Text {
                        anchors.centerIn: parent
                        text: "U"
                        color: "white"
                        font.bold: true
                        font.family: Style.headerFont.family
                        font.pixelSize: 14
                    }
                }
                
                Text {
                    text: "UMC Manager"
                    font: Style.headerFont
                    color: Style.textPrimary
                }
                
                Item { Layout.fillWidth: true }
            }
        }
        
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Style.divider
        }

        // Section Title: Devices
        Item {
            Layout.fillWidth: true
            height: 40
            
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Style.spacingMedium
                anchors.rightMargin: Style.spacingMedium
                
                Text {
                    text: "CONNECTED DEVICES"
                    font.family: Style.bodySmallFont.family
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                    color: Style.textSecondary
                    Layout.fillWidth: true
                }
                
                // Refresh Button
                Item {
                    width: 24
                    height: 24
                    
                    Icon {
                        anchors.centerIn: parent
                        name: "refresh"
                        size: 14
                        color: refreshArea.pressed ? Style.textPrimary : Style.textSecondary
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
        }

        // Device List
        ListView {
            id: deviceList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: bridge ? bridge.devices : []
            boundsBehavior: Flickable.StopAtBounds
            
            delegate: Rectangle {
                id: deviceDelegate
                width: ListView.view.width
                height: 50
                color: {
                    if (bridge && bridge.currentDeviceSerial === modelData.serial) return Style.surfaceHighlight
                    return ma.containsMouse ? Style.surfaceLight : "transparent"
                }
                
                property bool isSelected: bridge && bridge.currentDeviceSerial === modelData.serial

                MouseArea {
                    id: ma
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        bridge.select_device(modelData.serial)
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: Style.spacingMedium
                    anchors.rightMargin: Style.spacingMedium
                    spacing: 12
                    
                    // Device Icon
                    Icon {
                        name: "device_phone"
                        size: 16
                        color: parent.parent.isSelected ? Style.accent : Style.textSecondary
                    }
                    
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        
                        Text {
                            text: modelData.model
                            color: parent.parent.parent.isSelected ? Style.textPrimary : Style.textSecondary
                            font.family: Style.bodyFont.family
                            font.pixelSize: 12
                            font.weight: Font.Medium
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: modelData.serial
                            color: Style.textDisabled
                            font.pixelSize: 10
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }

                    // Actions Row
                    Row {
                        spacing: 4
                        visible: ma.containsMouse || parent.parent.isSelected
                        
                        // Screen Toggle
                        Rectangle {
                            width: 24
                            height: 24
                            radius: 4
                            color: screenBtnArea.containsMouse ? Style.background : "transparent"
                            
                            Icon {
                                anchors.centerIn: parent
                                name: "screen_off"
                                size: 14
                                color: screenBtnArea.pressed ? Style.accent : Style.textSecondary
                            }
                            
                            MouseArea {
                                id: screenBtnArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: (mouse) => {
                                    if (bridge) {
                                        bridge.toggle_scrcpy_display(modelData.serial)
                                        mouse.accepted = true
                                    }
                                }
                                ToolTip.visible: containsMouse
                                ToolTip.text: "Turn Screen Off (Scrcpy)"
                                ToolTip.delay: 500
                            }
                        }

                        // Power Button
                        Rectangle {
                            width: 24
                            height: 24
                            radius: 4
                            color: powerBtnArea.containsMouse ? Style.background : "transparent"
                            
                            Icon {
                                anchors.centerIn: parent
                                name: "power"
                                size: 14
                                color: powerBtnArea.pressed ? Style.error : Style.textSecondary
                            }
                            
                            MouseArea {
                                id: powerBtnArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: (mouse) => {
                                    if (bridge) {
                                        bridge.toggle_screen(modelData.serial)
                                        // Prevent selecting the row when clicking the button
                                        mouse.accepted = true
                                    }
                                }
                                ToolTip.visible: containsMouse
                            }
                        }
                    }
                }
            }
        }
        
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Style.divider
        }

        // Settings / Launch Mode Area
        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: Style.spacingMedium
            spacing: 12

            Text {
                text: "LAUNCH SETTINGS"
                font.family: Style.bodySmallFont.family
                font.pixelSize: 10
                font.weight: Font.DemiBold
                color: Style.textSecondary
            }

            // Mode Switcher
            RowLayout {
                Layout.fillWidth: true
                spacing: 0
                
                Repeater {
                    model: ["Tablet", "Phone", "Desktop"]
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        height: 28
                        color: (bridge && bridge.launchMode === modelData) ? Style.accent : Style.surfaceLight
                        
                        // First item radius left, last item radius right
                        radius: 2
                        
                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            color: (bridge && bridge.launchMode === modelData) ? "white" : Style.textSecondary
                            font.pixelSize: 11
                            font.weight: Font.Medium
                        }
                        
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: if (bridge) bridge.launchMode = modelData
                        }
                    }
                }
            }
            
            // Checkboxes
            ColumnLayout {
                spacing: 8
                
                CheckBox {
                    id: screenOffCheck
                    text: "Launch with Screen Off"
                    checked: bridge ? bridge.launchWithScreenOff : false
                    onCheckedChanged: if (bridge) bridge.launchWithScreenOff = checked
                    
                    contentItem: Text {
                        text: screenOffCheck.text
                        font: Style.bodySmallFont
                        color: Style.textPrimary
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: screenOffCheck.indicator.width + 8
                    }
                    
                    indicator: Rectangle {
                        implicitWidth: 16
                        implicitHeight: 16
                        x: 0
                        y: parent.height / 2 - height / 2
                        radius: 3
                        border.color: screenOffCheck.checked ? Style.accent : Style.textSecondary
                        color: screenOffCheck.checked ? Style.accent : "transparent"
                        
                        Icon {
                            anchors.centerIn: parent
                            name: "check" // We need to add check to Icon.qml or use simple rect
                            visible: screenOffCheck.checked
                            size: 10
                            color: "white"
                        }
                        // Fallback simple check indicator if icon missing
                        Rectangle {
                            anchors.centerIn: parent
                            width: 8; height: 8; radius: 1
                            color: "white"
                            visible: screenOffCheck.checked && true // Replace with Icon usage
                        }
                    }
                }
                
                CheckBox {
                    id: audioCheck
                    text: "Forward Audio"
                    checked: bridge ? bridge.audioForwarding : false
                    onCheckedChanged: if (bridge) bridge.audioForwarding = checked
                    
                    contentItem: Text {
                        text: audioCheck.text
                        font: Style.bodySmallFont
                        color: Style.textPrimary
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: audioCheck.indicator.width + 8
                    }
                    
                    indicator: Rectangle {
                        implicitWidth: 16
                        implicitHeight: 16
                        x: 0
                        y: parent.height / 2 - height / 2
                        radius: 3
                        border.color: audioCheck.checked ? Style.accent : Style.textSecondary
                        color: audioCheck.checked ? Style.accent : "transparent"
                        
                        Rectangle {
                            anchors.centerIn: parent
                            width: 8; height: 8; radius: 1
                            color: "white"
                            visible: audioCheck.checked
                        }
                    }
                }
                
                Item { height: 8; width: 1 } // Spacer
                
                Text {
                    text: "PERFORMANCE PROFILE"
                    font.family: Style.bodySmallFont.family
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                    color: Style.textSecondary
                }

                ComboBox {
                    id: profileCombo
                    Layout.fillWidth: true
                    height: 28
                    model: bridge ? bridge.profiles : []
                    
                    onActivated: (index) => {
                        if (bridge) bridge.currentProfile = textAt(index)
                    }
                    
                    Component.onCompleted: {
                        if (bridge) currentIndex = find(bridge.currentProfile)
                    }
                    
                    Connections {
                        target: bridge
                        function onCurrentProfileChanged(profile) {
                            if (profileCombo.find) {
                                var idx = profileCombo.find(profile)
                                if (idx !== -1) profileCombo.currentIndex = idx
                            }
                        }
                    }

                    delegate: ItemDelegate {
                        width: parent.width
                        contentItem: Text {
                            text: modelData
                            color: highlighted ? "white" : Style.textPrimary
                            font: Style.bodySmallFont
                            elide: Text.ElideRight
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            color: highlighted ? Style.accent : "transparent"
                        }
                    }

                    contentItem: Text {
                        leftPadding: 8
                        rightPadding: profileCombo.indicator.width + 8
                        text: profileCombo.displayText
                        font: Style.bodySmallFont
                        color: Style.textPrimary
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }

                    background: Rectangle {
                        color: Style.surfaceLight
                        radius: 2
                        border.color: "transparent"
                    }
                    
                    popup: Popup {
                        y: profileCombo.height - 1
                        width: profileCombo.width
                        implicitHeight: contentItem.implicitHeight
                        padding: 1

                        contentItem: ListView {
                            clip: true
                            implicitHeight: contentHeight
                            model: profileCombo.delegateModel
                            currentIndex: profileCombo.highlightedIndex
                            ScrollIndicator.vertical: ScrollIndicator { }
                        }

                        background: Rectangle {
                            color: Style.surface
                            border.color: Style.divider
                            radius: 2
                        }
                    }
                }
            }
        }
    }
}
