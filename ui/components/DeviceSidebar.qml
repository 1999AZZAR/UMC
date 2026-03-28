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

        // App Header
        Rectangle {
            Layout.fillWidth: true; height: Style.headerHeight; color: Style.background
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: Style.spacingMedium; anchors.rightMargin: Style.spacingMedium; spacing: 12
                Rectangle {
                    width: 24; height: 24; radius: 4; color: Style.accent
                    Text { anchors.centerIn: parent; text: "U"; color: "white"; font.bold: true; font.pixelSize: 14 }
                }
                Text { text: "UMC Manager"; font: Style.headerFont; color: Style.textPrimary }
                Item { Layout.fillWidth: true }
            }
        }
        
        Rectangle { Layout.fillWidth: true; height: 1; color: Style.divider }

        // Wireless Connection Section
        Rectangle {
            id: connectSection
            Layout.fillWidth: true; Layout.margins: Style.spacingSmall
            height: connectExpanded ? 180 : 36
            radius: 4; color: Style.surfaceLight
            z: connectExpanded ? 100 : 1 // Bring to front when expanded
            property bool connectExpanded: false
            Behavior on height { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }
            
            MouseArea {
                anchors.fill: parent; anchors.topMargin: 0; height: 36
                cursorShape: Qt.PointingHandCursor
                onClicked: connectSection.connectExpanded = !connectSection.connectExpanded
            }
            
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 8; spacing: 8
                RowLayout {
                    Layout.fillWidth: true; spacing: 8
                    Icon { name: "wifi"; size: 14; color: Style.accent }
                    Text { text: "Connect Device"; font.pixelSize: 11; font.weight: Font.Medium; color: Style.textPrimary; Layout.fillWidth: true }
                    Icon { name: "expand_more"; size: 14; color: Style.textSecondary; rotation: connectSection.connectExpanded ? 180 : 0 }
                }
                
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 6
                    visible: connectSection.connectExpanded
                    opacity: connectSection.connectExpanded ? 1 : 0
                    Behavior on opacity { NumberAnimation { duration: 150 } }
                    
                    RowLayout {
                        Layout.fillWidth: true; spacing: 4
                        TextField {
                            id: ipAddressField; Layout.fillWidth: true; placeholderText: "IP:port"; font.pixelSize: 10; height: 28
                            background: Rectangle { color: Style.surface; radius: 2; border.color: activeFocus ? Style.accent : Style.divider }
                            onAccepted: if (text && bridge) bridge.connect_wireless_device(text)
                        }
                        Rectangle {
                            width: 28; height: 28; radius: 2; color: Style.surface; border.color: Style.divider; border.width: 1
                            Icon { anchors.centerIn: parent; name: "link"; size: 12; color: Style.textSecondary }
                            MouseArea {
                                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                onClicked: if (ipAddressField.text && bridge) bridge.connect_wireless_device(ipAddressField.text)
                            }
                        }
                    }
                    
                    Rectangle { Layout.fillWidth: true; height: 1; color: Style.divider }
                    Text { text: "Android 11+ Pairing"; font.pixelSize: 9; color: Style.textSecondary }
                    RowLayout {
                        Layout.fillWidth: true; spacing: 4
                        TextField {
                            id: pairAddressField; Layout.fillWidth: true; placeholderText: "IP:port"; font.pixelSize: 10; height: 26
                            background: Rectangle { color: Style.surface; radius: 2; border.color: activeFocus ? Style.accent : Style.divider }
                        }
                        TextField {
                            id: pairingCodeField; Layout.preferredWidth: 60; placeholderText: "Code"; font.pixelSize: 10; height: 26
                            background: Rectangle { color: Style.surface; radius: 2; border.color: activeFocus ? Style.accent : Style.divider }
                        }
                        Rectangle {
                            width: 26; height: 26; radius: 2; color: Style.surface; border.color: Style.divider; border.width: 1
                            Text { anchors.centerIn: parent; text: "P"; font.pixelSize: 10; font.weight: Font.Bold; color: Style.textSecondary }
                            MouseArea {
                                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                onClicked: if (pairAddressField.text && pairingCodeField.text && bridge) bridge.pair_wireless_device(pairAddressField.text, pairingCodeField.text)
                            }
                        }
                    }
                    
                    Rectangle { Layout.fillWidth: true; height: 1; color: Style.divider }
                    Button {
                        text: "Enable TCP/IP (USB)"; Layout.fillWidth: true; font.pixelSize: 9
                        onClicked: if (bridge && bridge.currentDeviceSerial) bridge.enable_tcpip_mode(bridge.currentDeviceSerial, 5555)
                    }
                }
            }
        }

        // Section Title: Devices
        Item {
            Layout.fillWidth: true; height: 40
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: Style.spacingMedium; anchors.rightMargin: Style.spacingMedium
                Text { text: "CONNECTED DEVICES"; font.pixelSize: 10; font.weight: Font.DemiBold; color: Style.textSecondary; Layout.fillWidth: true }
                Icon { 
                    name: "refresh"; size: 14; color: Style.textSecondary 
                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: bridge.refresh_devices() }
                }
            }
        }

        // Device List
        ListView {
            id: deviceList
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            model: bridge ? bridge.devices : []
            boundsBehavior: Flickable.StopAtBounds
            
            delegate: Rectangle {
                id: deviceDelegate
                width: ListView.view.width; height: expanded ? 450 : 60
                color: (bridge && bridge.currentDeviceSerial === modelData.serial) ? Style.surfaceHighlight : "transparent"
                property bool expanded: false
                property var deviceStatus: modelData.status_data || {}
                
                // NO MORE INDIVIDUAL CONNECTIONS FOR STATUS!
                // We use modelData.status_data which is updated by the bridge.

                MouseArea {
                    anchors.fill: parent; anchors.rightMargin: 100
                    hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                    onClicked: bridge.select_device(modelData.serial)
                    onDoubleClicked: deviceDelegate.expanded = !deviceDelegate.expanded
                }

                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 12; spacing: 8
                    
                    RowLayout {
                        Layout.fillWidth: true; spacing: 12
                        Icon { name: "device_phone"; size: 16; color: (bridge && bridge.currentDeviceSerial === modelData.serial) ? Style.accent : Style.textSecondary }
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 2
                            Text { text: modelData.custom_name || modelData.model; color: Style.textPrimary; font.pixelSize: 12; font.weight: Font.Medium; elide: Text.ElideRight; Layout.fillWidth: true }
                            Text { text: modelData.serial; color: Style.textDisabled; font.pixelSize: 10; elide: Text.ElideRight; Layout.fillWidth: true }
                        }
                        
                        // Status Bar
                        RowLayout {
                            visible: !deviceDelegate.expanded && deviceStatus.battery_level !== undefined
                            spacing: 8
                            Rectangle {
                                width: 30; height: 10; color: Style.surfaceLight; radius: 2
                                Rectangle {
                                    width: parent.width * (deviceStatus.battery_level || 0) / 100
                                    height: parent.height; color: (deviceStatus.battery_level > 20) ? "#4CAF50" : "#F44336"; radius: 2
                                }
                            }
                            Text { text: deviceStatus.network_type === "wifi" ? "WiFi" : "USB"; font.pixelSize: 8; color: Style.textSecondary }
                        }

                        // Expand/Power/Mirror Row
                        RowLayout {
                            spacing: 4
                            Rectangle {
                                width: 24; height: 24; radius: 4; color: "transparent"
                                Icon { anchors.centerIn: parent; name: "open_in_new"; size: 14; color: Style.textSecondary }
                                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: openMenu.open() }
                                Menu {
                                    id: openMenu; y: 24; width: 180
                                    background: Rectangle { color: Style.surface; border.color: Style.divider; radius: 4 }
                                    MenuItem { text: "Mirror (Default)"; onTriggered: bridge.mirror_device(modelData.serial) }
                                    MenuItem { text: "New Phone Screen"; onTriggered: bridge.open_display(modelData.serial, "Phone") }
                                    MenuItem { text: "New Tablet Screen"; onTriggered: bridge.open_display(modelData.serial, "Tablet") }
                                    MenuItem { text: "New Desktop Screen"; onTriggered: bridge.open_display(modelData.serial, "Desktop") }
                                }
                            }
                            Rectangle {
                                width: 24; height: 24; radius: 4; color: "transparent"
                                Icon { anchors.centerIn: parent; name: "power"; size: 14; color: Style.textSecondary }
                                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: bridge.toggle_screen(modelData.serial) }
                            }
                            Rectangle {
                                width: 24; height: 24; radius: 4; color: "transparent"
                                Icon { anchors.centerIn: parent; name: "expand_more"; size: 14; rotation: deviceDelegate.expanded ? 180 : 0 }
                                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: deviceDelegate.expanded = !deviceDelegate.expanded }
                            }
                        }
                    }

                    // --- Expanded Controls ---
                    ColumnLayout {
                        Layout.fillWidth: true; visible: deviceDelegate.expanded; spacing: 12
                        
                        Rectangle { Layout.fillWidth: true; height: 1; color: Style.divider }

                        // Stats Grid
                        GridLayout {
                            columns: 2; Layout.fillWidth: true
                            Text { text: "Battery:"; font.pixelSize: 10; color: Style.textSecondary }
                            Text { text: (deviceStatus.battery_level || 0) + "% (" + (deviceStatus.battery_status || "N/A") + ")"; font.pixelSize: 10; color: Style.textPrimary; Layout.alignment: Qt.AlignRight }
                            Text { text: "Storage:"; font.pixelSize: 10; color: Style.textSecondary }
                            Text { text: deviceStatus.storage ? (Math.round(deviceStatus.storage.used/1024) + "GB / " + Math.round(deviceStatus.storage.total/1024) + "GB") : "N/A"; font.pixelSize: 10; color: Style.textPrimary; Layout.alignment: Qt.AlignRight }
                            Text { text: "Temp:"; font.pixelSize: 10; color: Style.textSecondary }
                            Text { text: (deviceStatus.temperature || 0) + "°C"; font.pixelSize: 10; color: Style.textPrimary; Layout.alignment: Qt.AlignRight }
                        }

                        // Volume
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 4
                            Text { text: "Volume (Media): " + Math.round(volSlider.value); font.pixelSize: 9; color: Style.textSecondary }
                            Slider {
                                id: volSlider; Layout.fillWidth: true; from: 0; to: 15
                                value: deviceStatus.volume_music || 0
                                onMoved: bridge.set_volume(modelData.serial, "music", Math.round(value))
                            }
                        }

                        // Brightness
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 4
                            Text { text: "Brightness: " + Math.round(brightSlider.value); font.pixelSize: 9; color: Style.textSecondary }
                            Slider {
                                id: brightSlider; Layout.fillWidth: true; from: 0; to: 255
                                value: deviceStatus.brightness || 128
                                onMoved: bridge.set_brightness(modelData.serial, Math.round(value))
                            }
                        }

                        // Toggles
                        GridLayout {
                            columns: 2; Layout.fillWidth: true; rowSpacing: 10
                            
                            RowLayout {
                                Text { text: "Rotate Lock"; font.pixelSize: 10; color: Style.textSecondary; Layout.fillWidth: true }
                                Switch { 
                                    checked: deviceStatus.rotation_locked || false
                                    onClicked: bridge.set_rotation_lock(modelData.serial, checked)
                                }
                            }
                            RowLayout {
                                Text { text: "Clipboard Sync"; font.pixelSize: 10; color: Style.textSecondary; Layout.fillWidth: true }
                                Switch { 
                                    checked: bridge.get_clipboard_sync(modelData.serial)
                                    onClicked: bridge.set_clipboard_sync(modelData.serial, checked)
                                }
                            }
                            RowLayout {
                                Text { text: "WiFi"; font.pixelSize: 10; color: Style.textSecondary; Layout.fillWidth: true }
                                Switch { 
                                    checked: deviceStatus.wifi_enabled !== false
                                    onClicked: bridge.set_wifi_enabled(modelData.serial, checked)
                                }
                            }
                            RowLayout {
                                Text { text: "Airplane"; font.pixelSize: 10; color: Style.textSecondary; Layout.fillWidth: true }
                                Switch { 
                                    checked: deviceStatus.airplane_mode || false
                                    onClicked: bridge.set_airplane_mode(modelData.serial, checked)
                                }
                            }
                        }

                        // Action Buttons
                        RowLayout {
                            Layout.fillWidth: true; spacing: 8
                            Button { text: "Screenshot"; Layout.fillWidth: true; onClicked: bridge.capture_screenshot(modelData.serial) }
                            Button { text: "Files"; Layout.fillWidth: true; onClicked: bridge.request_file_selection(modelData.serial) }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 6
                            Text { text: "Quick Actions"; font.pixelSize: 10; font.weight: Font.DemiBold; color: Style.textSecondary }

                            GridLayout {
                                columns: 3
                                Layout.fillWidth: true
                                columnSpacing: 8
                                rowSpacing: 8

                                Button { text: "Home"; Layout.fillWidth: true; onClicked: bridge.send_keyevent(modelData.serial, 3) }
                                Button { text: "Back"; Layout.fillWidth: true; onClicked: bridge.send_keyevent(modelData.serial, 4) }
                                Button { text: "Recents"; Layout.fillWidth: true; onClicked: bridge.send_keyevent(modelData.serial, 187) }

                                Button { text: "Menu"; Layout.fillWidth: true; onClicked: bridge.send_keyevent(modelData.serial, 82) }
                                Button { text: "Notif"; Layout.fillWidth: true; onClicked: bridge.send_keyevent(modelData.serial, 83) }
                                Button { text: "Search"; Layout.fillWidth: true; onClicked: bridge.send_keyevent(modelData.serial, 84) }

                                Button { text: "Play/Pause"; Layout.fillWidth: true; onClicked: bridge.send_keyevent(modelData.serial, 85) }
                                Button { text: "Vol +"; Layout.fillWidth: true; onClicked: bridge.send_keyevent(modelData.serial, 24) }
                                Button { text: "Vol -"; Layout.fillWidth: true; onClicked: bridge.send_keyevent(modelData.serial, 25) }
                            }
                        }
                    }
                }
            }
        }
        
        Rectangle { Layout.fillWidth: true; height: 1; color: Style.divider }

        // Global Launch Settings
        ColumnLayout {
            Layout.fillWidth: true; Layout.margins: Style.spacingMedium; spacing: 12
            Text { text: "GLOBAL SETTINGS"; font.pixelSize: 10; font.weight: Font.DemiBold; color: Style.textSecondary }
            
            RowLayout {
                Layout.fillWidth: true; spacing: 0
                Repeater {
                    model: ["Tablet", "Phone", "Desktop"]
                    delegate: Rectangle {
                        Layout.fillWidth: true; height: 28; color: (bridge && bridge.launchMode === modelData) ? Style.accent : Style.surfaceLight
                        Text { anchors.centerIn: parent; text: modelData; color: "white"; font.pixelSize: 11; font.weight: Font.Medium; opacity: (bridge && bridge.launchMode === modelData) ? 1 : 0.5 }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: if (bridge) bridge.launchMode = modelData }
                    }
                }
            }
            
            CheckBox {
                text: "Launch with Screen Off"; checked: bridge ? bridge.launchWithScreenOff : false
                onCheckedChanged: if (bridge) bridge.launchWithScreenOff = checked
            }
            CheckBox {
                text: "Forward Audio"; checked: bridge ? bridge.audioForwarding : false
                onCheckedChanged: if (bridge) bridge.audioForwarding = checked
            }
            
            Text { text: "PERFORMANCE PROFILE"; font.pixelSize: 10; font.weight: Font.DemiBold; color: Style.textSecondary }
            ComboBox {
                Layout.fillWidth: true; model: bridge ? bridge.profiles : []
                onActivated: (index) => { if (bridge) bridge.currentProfile = textAt(index) }
                Component.onCompleted: if (bridge) currentIndex = find(bridge.currentProfile)
            }
        }
    }
}
