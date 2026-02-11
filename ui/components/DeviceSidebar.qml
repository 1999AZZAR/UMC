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
        anchors.fill: parent; anchors.margins: 0; spacing: 0

        // App Header (M3 Style)
        Rectangle {
            Layout.fillWidth: true; height: Style.headerHeight; color: "transparent"
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 24; spacing: 16
                Rectangle {
                    width: 48; height: 48; radius: 16
                    color: Style.accentVariant
                    Icon { anchors.centerIn: parent; name: "bolt"; size: 24; color: Style.accent }
                }
                ColumnLayout {
                    spacing: 0
                    Text { text: "UMC Controller"; font: Style.headerFont; color: Style.textPrimary }
                    Text { text: "System Management"; font.pixelSize: 11; color: Style.textSecondary; opacity: 0.7 }
                }
            }
        }

        // Sidebar Scrollable Content
        ScrollView {
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            
            ColumnLayout {
                width: parent.width - 32; spacing: 16
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.topMargin: 8; anchors.bottomMargin: 24

                // 1. Connection Card
                Rectangle {
                    id: connectSection
                    Layout.fillWidth: true; height: connectExpanded ? 240 : 64
                    radius: 24; color: Style.surfaceLight
                    property bool connectExpanded: false
                    Behavior on height { NumberAnimation { duration: 300; easing.type: Easing.OutQuint } }
                    
                    MouseArea {
                        anchors.fill: parent; anchors.topMargin: 0; height: 64
                        cursorShape: Qt.PointingHandCursor
                        onClicked: connectSection.connectExpanded = !connectSection.connectExpanded
                    }
                    
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 20; spacing: 15
                        RowLayout {
                            Layout.fillWidth: true; spacing: 12
                            Icon { name: "wifi"; size: 20; color: Style.accent }
                            Text { text: "Connect Device"; font: Style.subHeaderFont; color: Style.textPrimary; Layout.fillWidth: true }
                            Icon { name: "expand_more"; size: 16; color: Style.textSecondary; rotation: connectSection.connectExpanded ? 180 : 0; Behavior on rotation { NumberAnimation { duration: 200 } } }
                        }
                        
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 12; visible: connectSection.connectExpanded
                            opacity: connectSection.connectExpanded ? 1 : 0
                            Behavior on opacity { NumberAnimation { duration: 200 } }

                            TextField {
                                id: ipAddressField; Layout.fillWidth: true; placeholderText: "IP:Port (e.g. 192.168.1.5)"; font: Style.bodySmallFont; height: 40; verticalAlignment: Text.AlignVCenter
                                color: Style.textPrimary
                                background: Rectangle { color: Style.surface; radius: 12; border.color: parent.activeFocus ? Style.accent : "transparent"; border.width: 2 }
                                onAccepted: if (text && bridge) bridge.connect_wireless_device(text)
                            }
                            
                            Button {
                                text: "Connect Link"; Layout.fillWidth: true; height: 44
                                contentItem: Text { text: parent.text; font.weight: Font.Bold; color: Style.background; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                                background: Rectangle { color: Style.accent; radius: 12 }
                                onClicked: if (ipAddressField.text) bridge.connect_wireless_device(ipAddressField.text)
                            }

                            Button {
                                text: "Enable TCP/IP (USB)"; Layout.fillWidth: true; height: 36; font.pixelSize: 10
                                contentItem: Text { text: parent.text; font.weight: Font.Medium; color: Style.textPrimary; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                                background: Rectangle { color: "transparent"; border.color: Style.surfaceHighlight; border.width: 1; radius: 12 }
                                onClicked: if (bridge && bridge.currentDeviceSerial) bridge.enable_tcpip_mode(bridge.currentDeviceSerial)
                            }
                        }
                    }
                }

                Text { text: "Devices"; font: Style.subHeaderFont; color: Style.textSecondary; opacity: 0.6; leftPadding: 12 }

                // 2. Device List
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 12
                    Repeater {
                        model: bridge ? bridge.devices : []
                        delegate: Rectangle {
                            id: deviceDelegate
                            Layout.fillWidth: true; height: expanded ? 500 : 80
                            radius: Style.cornerRadius; color: isSelected ? Style.surfaceHighlight : Style.surfaceLight
                            property bool isSelected: bridge && bridge.currentDeviceSerial === modelData.serial
                            property bool expanded: false
                            property var deviceStatus: modelData.status_data || {}
                            Behavior on height { NumberAnimation { duration: 300; easing.type: Easing.OutQuint } }

                            ColumnLayout {
                                anchors.fill: parent; anchors.margins: 16; spacing: 16
                                
                                // Header row
                                RowLayout {
                                    Layout.fillWidth: true; spacing: 16
                                    Rectangle {
                                        width: 44; height: 44; radius: 12; color: Style.surface
                                        Icon { anchors.centerIn: parent; name: "device_phone"; size: 20; color: deviceDelegate.isSelected ? Style.accent : Style.textSecondary }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true; spacing: 2
                                        Text { text: modelData.custom_name || modelData.model; color: Style.textPrimary; font.pixelSize: 14; font.weight: Font.Bold; elide: Text.ElideRight }
                                        Text { text: modelData.serial; color: Style.textDisabled; font: Style.bodySmallFont; elide: Text.ElideRight }
                                    }
                                    Icon { 
                                        name: "expand_more"; size: 16; color: Style.textSecondary; rotation: deviceDelegate.expanded ? 180 : 0
                                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: deviceDelegate.expanded = !deviceDelegate.expanded }
                                    }
                                }
                                
                                // Compact Status
                                RowLayout {
                                    visible: !deviceDelegate.expanded && deviceStatus.battery_level !== undefined
                                    spacing: 12
                                    Rectangle {
                                        width: 36; height: 8; color: Style.surface; radius: 4
                                        Rectangle {
                                            width: parent.width * (deviceStatus.battery_level || 0) / 100; height: parent.height
                                            color: (deviceStatus.battery_level > 20) ? Style.success : Style.error; radius: 4
                                        }
                                    }
                                    Text { text: (deviceStatus.battery_level || 0) + "%"; font: Style.bodySmallFont; color: Style.textSecondary }
                                    Item { Layout.fillWidth: true }
                                    Text { text: deviceStatus.network_type === "wifi" ? "WiFi" : "USB"; font: Style.bodySmallFont; color: Style.accent; font.weight: Font.Bold }
                                }

                                // Expanded Controls
                                ColumnLayout {
                                    Layout.fillWidth: true; visible: deviceDelegate.expanded; spacing: 20
                                    
                                    Rectangle { Layout.fillWidth: true; height: 1; color: Style.surfaceHighlight }

                                    // Quick Stats
                                    RowLayout {
                                        Layout.fillWidth: true; spacing: 10
                                        Rectangle {
                                            Layout.fillWidth: true; height: 60; radius: 16; color: Style.surface
                                            ColumnLayout { anchors.centerIn: parent; spacing: 2
                                                Text { text: "Battery"; font.pixelSize: 10; color: Style.textDisabled; Layout.alignment: Qt.AlignHCenter }
                                                Text { text: (deviceStatus.battery_level || 0) + "%"; font.weight: Font.Bold; color: Style.textPrimary; Layout.alignment: Qt.AlignHCenter }
                                            }
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true; height: 60; radius: 16; color: Style.surface
                                            ColumnLayout { anchors.centerIn: parent; spacing: 2
                                                Text { text: "Temp"; font.pixelSize: 10; color: Style.textDisabled; Layout.alignment: Qt.AlignHCenter }
                                                Text { text: (deviceStatus.temperature || 0) + "°C"; font.weight: Font.Bold; color: Style.textPrimary; Layout.alignment: Qt.AlignHCenter }
                                            }
                                        }
                                    }

                                    // Sliders
                                    ColumnLayout {
                                        Layout.fillWidth: true; spacing: 12
                                        Column { Layout.fillWidth: true; spacing: 6
                                            Text { text: "Volume"; font.pixelSize: 10; color: Style.textSecondary }
                                            Slider { Layout.fillWidth: true; from: 0; to: 15; value: deviceStatus.volume_music || 0; onMoved: bridge.set_volume(modelData.serial, "music", Math.round(value)) }
                                        }
                                        Column { Layout.fillWidth: true; spacing: 6
                                            Text { text: "Brightness"; font.pixelSize: 10; color: Style.textSecondary }
                                            Slider { Layout.fillWidth: true; from: 0; to: 255; value: deviceStatus.brightness || 128; onMoved: bridge.set_brightness(modelData.serial, Math.round(value)) }
                                        }
                                    }

                                    // Toggles
                                    ColumnLayout {
                                        Layout.fillWidth: true; spacing: 12
                                        SwitchDelegate {
                                            Layout.fillWidth: true; text: "Clipboard Sync"; font: Style.bodySmallFont; checked: bridge.get_clipboard_sync(modelData.serial)
                                            onToggled: bridge.set_clipboard_sync(modelData.serial, checked)
                                            background: Rectangle { color: "transparent" }
                                            contentItem: Text { text: parent.text; font: parent.font; color: Style.textPrimary; verticalAlignment: Text.AlignVCenter; leftPadding: 0 }
                                        }
                                        SwitchDelegate {
                                            Layout.fillWidth: true; text: "Rotate Locked"; font: Style.bodySmallFont; checked: deviceStatus.rotation_locked || false
                                            onToggled: bridge.set_rotation_lock(modelData.serial, checked)
                                            background: Rectangle { color: "transparent" }
                                            contentItem: Text { text: parent.text; font: parent.font; color: Style.textPrimary; verticalAlignment: Text.AlignVCenter; leftPadding: 0 }
                                        }
                                    }

                                    // Bottom Actions
                                    GridLayout {
                                        columns: 2; Layout.fillWidth: true; rowSpacing: 8; columnSpacing: 8
                                        Button { text: "Mirror Device"; Layout.fillWidth: true; onClicked: bridge.mirror_device(modelData.serial); background: Rectangle { radius: 12; color: Style.accentVariant } }
                                        Button { text: "Screenshot"; Layout.fillWidth: true; onClicked: bridge.capture_screenshot(modelData.serial); background: Rectangle { radius: 12; color: Style.surface } }
                                        Button { text: "Toggle Power"; Layout.fillWidth: true; onClicked: bridge.toggle_screen(modelData.serial); background: Rectangle { radius: 12; color: Style.surface } }
                                        Button { text: "Files"; Layout.fillWidth: true; onClicked: bridge.request_file_selection(modelData.serial); background: Rectangle { radius: 12; color: Style.surface } }
                                    }
                                }
                            }

                            MouseArea {
                                anchors.fill: parent; anchors.rightMargin: 80; visible: !deviceDelegate.expanded
                                onClicked: bridge.select_device(modelData.serial)
                            }
                        }
                    }
                }
                
                Item { height: 16; width: 1 }

                // 3. Settings Card
                Rectangle {
                    Layout.fillWidth: true; Layout.preferredHeight: 320
                    color: Style.surfaceLight; radius: 24
                    
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 20; spacing: 16
                        Text { text: "Launch Config"; font: Style.subHeaderFont; color: Style.textPrimary }
                        
                        RowLayout {
                            Layout.fillWidth: true; spacing: 8
                            Repeater {
                                model: ["Tablet", "Phone", "Desktop"]
                                delegate: Button {
                                    Layout.fillWidth: true; height: 40
                                    text: modelData
                                    property bool isActive: bridge && bridge.launchMode === (modelData.charAt(0) + modelData.slice(1).toLowerCase())
                                    contentItem: Text { text: parent.text; font.weight: Font.Bold; font.pixelSize: 10; color: parent.isActive ? Style.background : Style.textPrimary; horizontalAlignment: Text.AlignHCenter }
                                    background: Rectangle { color: parent.isActive ? Style.accent : Style.surface; radius: 10 }
                                    onClicked: if (bridge) bridge.launchMode = (modelData.charAt(0) + modelData.slice(1).toLowerCase())
                                }
                            }
                        }
                        
                        ColumnLayout {
                            spacing: 8
                            CheckBox {
                                text: "Screen Off"; checked: bridge ? bridge.launchWithScreenOff : false
                                contentItem: Text { text: parent.text; color: Style.textSecondary; font: Style.bodySmallFont; leftPadding: 32 }
                                onCheckedChanged: if (bridge) bridge.launchWithScreenOff = checked
                            }
                            CheckBox {
                                text: "Forward Audio"; checked: bridge ? bridge.audioForwarding : false
                                contentItem: Text { text: parent.text; color: Style.textSecondary; font: Style.bodySmallFont; leftPadding: 32 }
                                onCheckedChanged: if (bridge) bridge.audioForwarding = checked
                            }
                        }
                        
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 4
                            Text { text: "Performance Profile"; font.pixelSize: 10; color: Style.textDisabled; leftPadding: 4 }
                            ComboBox {
                                Layout.fillWidth: true; height: 40; model: bridge ? bridge.profiles : []
                                onActivated: (index) => { if (bridge) bridge.currentProfile = textAt(index) }
                                Component.onCompleted: if (bridge) currentIndex = find(bridge.currentProfile)
                                background: Rectangle { color: Style.surface; radius: 10 }
                                contentItem: Text { text: parent.displayText; color: Style.textPrimary; font.weight: Font.Medium; font.pixelSize: 12; leftPadding: 12; verticalAlignment: Text.AlignVCenter }
                            }
                        }
                    }
                }
            }
        }
    }
}
