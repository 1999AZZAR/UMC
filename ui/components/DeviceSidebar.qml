import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."

Rectangle {
    id: sidebar
    width: Style.sidebarWidth
    height: parent.height
    color: Style.surface
    
    // Background Pattern (subtle dots like Prism)
    Canvas {
        anchors.fill: parent
        opacity: 0.1
        onPaint: {
            var ctx = getContext("2d");
            ctx.fillStyle = "#ffffff";
            for (var x = 0; x < width; x += 20) {
                for (var y = 0; y < height; y += 20) {
                    ctx.fillRect(x, y, 1, 1);
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent; anchors.margins: 0; spacing: 0

        // App Header (Wired Style)
        Rectangle {
            Layout.fillWidth: true; height: 80; color: "transparent"
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 24; spacing: 15
                Rectangle {
                    width: 32; height: 32; radius: 8; color: "#000"
                    border.color: Style.accent; border.width: 2
                    Text { anchors.centerIn: parent; text: "U"; color: Style.accent; font.bold: true; font.pixelSize: 18 }
                }
                Column {
                    Text { text: "UMC_CORE"; font.pixelSize: 14; font.weight: Font.Black; color: "#fff"; font.letterSpacing: -0.5 }
                    Text { text: "UNIFIED MOBILE CONTROLLER"; font.pixelSize: 8; font.weight: Font.Bold; color: Style.accent; opacity: 0.8 }
                }
            }
        }
        
        Rectangle { Layout.fillWidth: true; height: 3; color: "#000" }

        // Sidebar Content
        ScrollView {
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            ScrollBar.vertical.policy: ScrollBar.AlwaysOff
            
            ColumnLayout {
                width: parent.width; spacing: 20
                anchors.margins: 16

                // 1. Connect Section (Hybrid Style)
                Rectangle {
                    id: connectSection
                    Layout.fillWidth: true; height: connectExpanded ? 220 : 44
                    radius: 12; color: Style.surfaceLight; border.color: "#000"; border.width: 2
                    property bool connectExpanded: false
                    Behavior on height { NumberAnimation { duration: 250; easing.type: Easing.OutBack } }
                    
                    MouseArea {
                        anchors.fill: parent; anchors.topMargin: 0; height: 44
                        cursorShape: Qt.PointingHandCursor
                        onClicked: connectSection.connectExpanded = !connectSection.connectExpanded
                    }
                    
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 12; spacing: 10
                        RowLayout {
                            Layout.fillWidth: true; spacing: 10
                            Icon { name: "wifi"; size: 16; color: Style.accent }
                            Text { text: "CONNECT DEVICE"; font.pixelSize: 11; font.weight: Font.Black; color: "#fff"; Layout.fillWidth: true }
                            Icon { name: "expand_more"; size: 14; color: "#fff"; rotation: connectSection.connectExpanded ? 180 : 0 }
                        }
                        
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 8; visible: connectSection.connectExpanded
                            TextField {
                                id: ipAddressField; Layout.fillWidth: true; placeholderText: "IP:PORT"; font.pixelSize: 11; height: 32
                                color: "#fff"
                                background: Rectangle { color: "#000"; radius: 6; border.color: parent.activeFocus ? Style.accent : "#333"; border.width: 1 }
                                onAccepted: if (text && bridge) bridge.connect_wireless_device(text)
                            }
                            Button {
                                text: "ESTABLISH LINK"; Layout.fillWidth: true
                                contentItem: Text { text: parent.text; font.weight: Font.Black; color: "#000"; horizontalAlignment: Text.AlignHCenter }
                                background: Rectangle { color: Style.accent; radius: 6; border.color: "#000"; border.width: 2 }
                                onClicked: if (ipAddressField.text) bridge.connect_wireless_device(ipAddressField.text)
                            }
                        }
                    }
                }

                // 2. Devices List Header
                Text { text: "UPLINK_STATUS"; font.pixelSize: 10; font.weight: Font.Black; color: Style.textSecondary; opacity: 0.5 }

                // ListView inside ColumnLayout needs specific height or fillHeight
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 12
                    Repeater {
                        model: bridge ? bridge.devices : []
                        delegate: Rectangle {
                            id: deviceDelegate
                            Layout.fillWidth: true; height: expanded ? 480 : 70
                            radius: 16; border.width: 2; border.color: isSelected ? Style.accent : "#000"
                            color: isSelected ? Style.surfaceHighlight : Style.surfaceLight
                            property bool isSelected: bridge && bridge.currentDeviceSerial === modelData.serial
                            property bool expanded: false
                            property var deviceStatus: modelData.status_data || {}
                            Behavior on height { NumberAnimation { duration: 250; easing.type: Easing.OutQuad } }

                            ColumnLayout {
                                anchors.fill: parent; anchors.margins: 12; spacing: 12
                                
                                // Device Info Row
                                RowLayout {
                                    Layout.fillWidth: true; spacing: 12
                                    Rectangle {
                                        width: 36; height: 36; radius: 8; color: "#000"; border.color: "#333"; border.width: 1
                                        Icon { anchors.centerIn: parent; name: "device_phone"; size: 18; color: deviceDelegate.isSelected ? Style.accent : "#fff" }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true; spacing: 0
                                        Text { text: (modelData.custom_name || modelData.model).toUpperCase(); color: "#fff"; font.pixelSize: 12; font.weight: Font.Black; elide: Text.ElideRight }
                                        Text { text: "ID: " + modelData.serial; color: Style.textSecondary; font.pixelSize: 9; font.family: "Monospace" }
                                    }
                                    Icon { 
                                        name: "expand_more"; size: 14; rotation: deviceDelegate.expanded ? 180 : 0; color: "#fff"
                                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: deviceDelegate.expanded = !deviceDelegate.expanded }
                                    }
                                }
                                
                                // Compact Status Bar
                                RowLayout {
                                    visible: !deviceDelegate.expanded && deviceStatus.battery_level !== undefined
                                    spacing: 10
                                    Rectangle {
                                        width: 40; height: 12; color: "#000"; radius: 4; border.color: "#333"; border.width: 1
                                        Rectangle {
                                            width: (parent.width - 2) * (deviceStatus.battery_level || 0) / 100; x: 1; y: 1
                                            height: parent.height - 2; color: (deviceStatus.battery_level > 20) ? "#4CAF50" : "#F44336"; radius: 2
                                        }
                                    }
                                    Text { text: (deviceStatus.battery_level || 0) + "%"; font.pixelSize: 9; font.weight: Font.Bold; color: "#fff" }
                                    Rectangle { width: 4; height: 4; radius: 2; color: "#333" }
                                    Text { text: deviceStatus.network_type === "wifi" ? "WIRELESS" : "USB_LINK"; font.pixelSize: 8; font.weight: Font.Bold; color: Style.accent }
                                }

                                // Expanded Controls (Wired/Brutal Style)
                                ColumnLayout {
                                    Layout.fillWidth: true; visible: deviceDelegate.expanded; spacing: 15
                                    
                                    Rectangle { Layout.fillWidth: true; height: 2; color: "#000" }

                                    // Matrix Stats
                                    GridLayout {
                                        columns: 2; Layout.fillWidth: true; rowSpacing: 8
                                        Text { text: "BATT_LEVEL"; font.pixelSize: 9; font.weight: Font.Bold; color: Style.textSecondary }
                                        Text { text: (deviceStatus.battery_level || 0) + "% [" + (deviceStatus.battery_status || "IDLE").toUpperCase() + "]"; font.pixelSize: 9; font.weight: Font.Black; color: "#fff"; Layout.alignment: Qt.AlignRight }
                                        Text { text: "STORAGE_USE"; font.pixelSize: 9; font.weight: Font.Bold; color: Style.textSecondary }
                                        Text { text: deviceStatus.storage ? (Math.round(deviceStatus.storage.used/1024) + " / " + Math.round(deviceStatus.storage.total/1024) + " GB") : "OFFLINE"; font.pixelSize: 9; font.weight: Font.Black; color: "#fff"; Layout.alignment: Qt.AlignRight }
                                        Text { text: "THERMAL_CPU"; font.pixelSize: 9; font.weight: Font.Bold; color: Style.textSecondary }
                                        Text { text: (deviceStatus.temperature || 0) + " °C"; font.pixelSize: 9; font.weight: Font.Black; color: "#fff"; Layout.alignment: Qt.AlignRight }
                                    }

                                    // Control Sliders
                                    ColumnLayout {
                                        Layout.fillWidth: true; spacing: 10
                                        Column { Layout.fillWidth: true; spacing: 2
                                            Text { text: "AUDIO_MAGNITUDE"; font.pixelSize: 8; font.weight: Font.Black; color: Style.accent }
                                            Slider { id: volSlider; Layout.fillWidth: true; from: 0; to: 15; value: deviceStatus.volume_music || 0; onMoved: bridge.set_volume(modelData.serial, "music", Math.round(value)) }
                                        }
                                        Column { Layout.fillWidth: true; spacing: 2
                                            Text { text: "PHOTON_INTENSITY"; font.pixelSize: 8; font.weight: Font.Black; color: Style.accent }
                                            Slider { id: brightSlider; Layout.fillWidth: true; from: 0; to: 255; value: deviceStatus.brightness || 128; onMoved: bridge.set_brightness(modelData.serial, Math.round(value)) }
                                        }
                                    }

                                    // Toggles Grid
                                    GridLayout {
                                        columns: 2; Layout.fillWidth: true; rowSpacing: 12; columnSpacing: 12
                                        
                                        // Custom Switch Component for Brutalism
                                        Repeater {
                                            model: [
                                                {label: "SYNC_CLIP", checked: bridge.get_clipboard_sync(modelData.serial), toggle: (c) => bridge.set_clipboard_sync(modelData.serial, c)},
                                                {label: "WIFI_RADIO", checked: deviceStatus.wifi_enabled !== false, toggle: (c) => bridge.set_wifi_enabled(modelData.serial, c)},
                                                {label: "FLIGHT_MODE", checked: deviceStatus.airplane_mode || false, toggle: (c) => bridge.set_airplane_mode(modelData.serial, c)},
                                                {label: "ROT_LOCK", checked: deviceStatus.rotation_locked || false, toggle: (c) => bridge.set_rotation_lock(modelData.serial, c)}
                                            ]
                                            delegate: RowLayout {
                                                Layout.fillWidth: true
                                                Text { text: modelData.label; font.pixelSize: 8; font.weight: Font.Black; color: "#fff"; Layout.fillWidth: true }
                                                Switch { 
                                                    checked: modelData.checked
                                                    onToggled: modelData.toggle(checked)
                                                }
                                            }
                                        }
                                    }

                                    // Action Buttons
                                    RowLayout {
                                        Layout.fillWidth: true; spacing: 8
                                        Button { 
                                            text: "SCR_SHOT"; Layout.fillWidth: true; 
                                            background: Rectangle { color: "#000"; border.color: parent.pressed ? Style.accent : "#444"; border.width: 2; radius: 8 }
                                            contentItem: Text { text: parent.text; color: "#fff"; font.weight: Font.Black; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter }
                                            onClicked: bridge.capture_screenshot(modelData.serial) 
                                        }
                                        Button { 
                                            text: "DRIVE_FS"; Layout.fillWidth: true; 
                                            background: Rectangle { color: "#000"; border.color: parent.pressed ? Style.accent : "#444"; border.width: 2; radius: 8 }
                                            contentItem: Text { text: parent.text; color: "#fff"; font.weight: Font.Black; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter }
                                            onClicked: bridge.request_file_selection(modelData.serial) 
                                        }
                                    }
                                    
                                    RowLayout {
                                        Layout.fillWidth: true; spacing: 8
                                        Button { 
                                            text: "MIRROR_LINK"; Layout.fillWidth: true; 
                                            background: Rectangle { color: "#000"; border.color: parent.pressed ? Style.accent : "#444"; border.width: 2; radius: 8 }
                                            contentItem: Text { text: parent.text; color: "#fff"; font.weight: Font.Black; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter }
                                            onClicked: bridge.mirror_device(modelData.serial) 
                                        }
                                        Button { 
                                            text: "POWER_SIG"; Layout.fillWidth: true; 
                                            background: Rectangle { color: "#000"; border.color: parent.pressed ? Style.accent : "#444"; border.width: 2; radius: 8 }
                                            contentItem: Text { text: parent.text; color: "#fff"; font.weight: Font.Black; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter }
                                            onClicked: bridge.toggle_screen(modelData.serial) 
                                        }
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
                
                Item { height: 20; width: 1 } // Spacer

                // 3. Global Settings (Brutal Minimalism)
                Rectangle {
                    Layout.fillWidth: true; Layout.preferredHeight: 280
                    color: "#000"; radius: 24; border.color: "#333"; border.width: 1
                    
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 20; spacing: 15
                        Text { text: "GLOBAL_SYSTEM_CONFIG"; font.pixelSize: 10; font.weight: Font.Black; color: Style.accent; font.letterSpacing: 1 }
                        
                        RowLayout {
                            Layout.fillWidth: true; spacing: 4
                            Repeater {
                                model: ["TABLET", "PHONE", "DESKTOP"]
                                delegate: Button {
                                    Layout.fillWidth: true; height: 36
                                    text: modelData
                                    property bool isActive: bridge && bridge.launchMode === (modelData.charAt(0) + modelData.slice(1).toLowerCase())
                                    contentItem: Text { text: parent.text; font.weight: Font.Black; font.pixelSize: 9; color: parent.isActive ? "#000" : "#fff"; horizontalAlignment: Text.AlignHCenter }
                                    background: Rectangle { color: parent.isActive ? Style.accent : "#111"; border.color: "#000"; border.width: 2; radius: 8 }
                                    onClicked: if (bridge) bridge.launchMode = (modelData.charAt(0) + modelData.slice(1).toLowerCase())
                                }
                            }
                        }
                        
                        ColumnLayout {
                            spacing: 12
                            CheckBox {
                                text: "STEALTH_LAUNCH (SCREEN OFF)"; checked: bridge ? bridge.launchWithScreenOff : false
                                contentItem: Text { text: parent.text; color: "#fff"; font.weight: Font.Bold; font.pixelSize: 9; leftPadding: 30 }
                                onCheckedChanged: if (bridge) bridge.launchWithScreenOff = checked
                            }
                            CheckBox {
                                text: "SONIC_FORWARDING (AUDIO)"; checked: bridge ? bridge.audioForwarding : false
                                contentItem: Text { text: parent.text; color: "#fff"; font.weight: Font.Bold; font.pixelSize: 9; leftPadding: 30 }
                                onCheckedChanged: if (bridge) bridge.audioForwarding = checked
                            }
                        }
                        
                        Column {
                            Layout.fillWidth: true; spacing: 5
                            Text { text: "ENGINE_PROFILE"; font.pixelSize: 8; font.weight: Font.Black; color: Style.textSecondary }
                            ComboBox {
                                width: parent.width; model: bridge ? bridge.profiles : []
                                onActivated: (index) => { if (bridge) bridge.currentProfile = textAt(index) }
                                Component.onCompleted: if (bridge) currentIndex = find(bridge.currentProfile)
                                background: Rectangle { color: "#111"; radius: 8; border.color: "#333"; border.width: 1 }
                                contentItem: Text { text: parent.displayText; color: "#fff"; font.weight: Font.Bold; font.pixelSize: 11; leftPadding: 10; verticalAlignment: Text.AlignVCenter }
                            }
                        }
                    }
                }
            }
        }
    }
}
