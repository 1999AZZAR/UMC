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
                    TextField {
                        id: ipAddressField; Layout.fillWidth: true; placeholderText: "IP:port"; font.pixelSize: 10; height: 28
                        background: Rectangle { color: Style.surface; radius: 2; border.color: activeFocus ? Style.accent : Style.divider }
                        onAccepted: if (text && bridge) bridge.connect_wireless_device(text)
                    }
                    Button {
                        text: "Connect"; Layout.fillWidth: true
                        onClicked: if (ipAddressField.text) bridge.connect_wireless_device(ipAddressField.text)
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
                Icon { name: "refresh"; size: 14; color: Style.textSecondary; MouseArea { anchors.fill: parent; onClicked: bridge.refresh_devices() } }
            }
        }

        // Device List
        ListView {
            id: deviceList
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            model: bridge ? bridge.devices : []
            
            delegate: Rectangle {
                id: deviceDelegate
                width: ListView.view.width; height: expanded ? 160 : 60
                color: (bridge && bridge.currentDeviceSerial === modelData.serial) ? Style.surfaceHighlight : "transparent"
                property bool expanded: false
                // Use status_data from model instead of individual Connections
                property var deviceStatus: modelData.status_data || {}

                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 12; spacing: 8
                    RowLayout {
                        Layout.fillWidth: true; spacing: 12
                        Icon { name: "device_phone"; size: 16; color: Style.accent }
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 2
                            Text { text: modelData.custom_name || modelData.model; color: Style.textPrimary; font.pixelSize: 12; font.weight: Font.Medium }
                            Text { text: modelData.serial; color: Style.textDisabled; font.pixelSize: 10 }
                        }
                        Icon { 
                            name: "expand_more"; size: 14; rotation: deviceDelegate.expanded ? 180 : 0
                            MouseArea { anchors.fill: parent; onClicked: deviceDelegate.expanded = !deviceDelegate.expanded }
                        }
                    }

                    // Status Bar (Simplified)
                    RowLayout {
                        Layout.fillWidth: true; spacing: 10
                        visible: deviceStatus.battery_level !== undefined
                        Rectangle {
                            width: 40; height: 12; color: Style.surfaceLight; radius: 2
                            Rectangle {
                                width: parent.width * (deviceStatus.battery_level || 0) / 100
                                height: parent.height; color: (deviceStatus.battery_level > 20) ? "#4CAF50" : "#F44336"; radius: 2
                            }
                        }
                        Text { text: (deviceStatus.battery_level || 0) + "%"; font.pixelSize: 9; color: Style.textSecondary }
                        Text { text: deviceStatus.network_type === "wifi" ? "WiFi" : "USB"; font.pixelSize: 9; color: Style.textSecondary }
                    }

                    // Quick Actions (Expanded)
                    RowLayout {
                        Layout.fillWidth: true; visible: deviceDelegate.expanded; spacing: 10
                        Button { text: "Mirror"; onClicked: bridge.mirror_device(modelData.serial) }
                        Button { text: "Power"; onClicked: bridge.toggle_screen(modelData.serial) }
                        Button { text: "Shot"; onClicked: bridge.capture_screenshot(modelData.serial) }
                    }
                }

                MouseArea {
                    anchors.fill: parent; anchors.rightMargin: 40
                    onClicked: bridge.select_device(modelData.serial)
                }
            }
        }
    }
}
