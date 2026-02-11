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
            Layout.fillWidth: true; height: Style.headerHeight; color: "transparent"
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 24; spacing: 16
                Rectangle {
                    width: 44; height: 44; radius: 12; color: Style.accentVariant
                    Icon { anchors.centerIn: parent; name: "bolt"; size: 20; color: Style.accent }
                }
                ColumnLayout {
                    spacing: 0
                    Text { text: "UMC Controller"; color: Style.textPrimary; font.family: Style.headerFont.family; font.pointSize: Style.headerFont.pointSize; font.bold: true }
                    Text { text: "System Management"; font.pixelSize: 11; color: Style.textSecondary; opacity: 0.7 }
                }
            }
        }

        ScrollView {
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            ColumnLayout {
                width: parent.width - 32; spacing: 16; anchors.horizontalCenter: parent.horizontalCenter
                anchors.topMargin: 8; anchors.bottomMargin: 24

                Rectangle {
                    id: connectSection
                    Layout.fillWidth: true; height: connectExpanded ? 240 : 64
                    radius: 20; color: Style.surfaceLight
                    property bool connectExpanded: false
                    z: connectExpanded ? 100 : 1
                    Behavior on height { NumberAnimation { duration: 250; easing.type: Easing.OutQuint } }
                    
                    MouseArea {
                        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; height: 64
                        cursorShape: Qt.PointingHandCursor
                        onClicked: connectSection.connectExpanded = !connectSection.connectExpanded
                    }
                    
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 16; spacing: 12
                        RowLayout {
                            Layout.fillWidth: true; spacing: 12
                            Icon { name: "wifi"; size: 18; color: Style.accent }
                            Text { text: "Connect Device"; color: Style.textPrimary; font.family: Style.subHeaderFont.family; font.pointSize: Style.subHeaderFont.pointSize; font.weight: Font.Medium; Layout.fillWidth: true }
                            Icon { name: "expand_more"; size: 14; color: Style.textSecondary; rotation: connectSection.connectExpanded ? 180 : 0 }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 10; visible: connectSection.connectExpanded
                            TextField {
                                id: ipAddressField; Layout.fillWidth: true; placeholderText: "IP:Port"; height: 36
                                color: Style.textPrimary; font.pixelSize: 11
                                background: Rectangle { color: Style.surface; radius: 10; border.color: activeFocus ? Style.accent : "transparent"; border.width: 2 }
                            }
                            Button {
                                text: "Connect Link"; Layout.fillWidth: true; height: 40
                                contentItem: Text { text: parent.text; font.bold: true; color: Style.background; horizontalAlignment: Text.AlignHCenter }
                                background: Rectangle { color: Style.accent; radius: 10 }
                                onClicked: if (ipAddressField.text) bridge.connect_wireless_device(ipAddressField.text)
                            }
                        }
                    }
                }

                Text { text: "Devices"; color: Style.textSecondary; font.pixelSize: 11; font.weight: Font.Medium; opacity: 0.6; leftPadding: 12 }

                ColumnLayout {
                    Layout.fillWidth: true; spacing: 12
                    Repeater {
                        model: bridge ? bridge.devices : []
                        delegate: Rectangle {
                            id: deviceDelegate
                            Layout.fillWidth: true; height: expanded ? 450 : 70
                            radius: 20; color: isSelected ? Style.surfaceHighlight : Style.surfaceLight
                            property bool isSelected: bridge && bridge.currentDeviceSerial === modelData.serial
                            property bool expanded: false
                            property var deviceStatus: modelData.status_data || {}
                            Behavior on height { NumberAnimation { duration: 250 } }

                            ColumnLayout {
                                anchors.fill: parent; anchors.margins: 12; spacing: 12
                                RowLayout {
                                    Layout.fillWidth: true; spacing: 12
                                    Rectangle {
                                        width: 40; height: 40; radius: 10; color: Style.surface
                                        Icon { anchors.centerIn: parent; name: "device_phone"; size: 18; color: deviceDelegate.isSelected ? Style.accent : Style.textSecondary }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true; spacing: 1
                                        Text { text: modelData.custom_name || modelData.model; color: Style.textPrimary; font.pixelSize: 12; font.bold: true; elide: Text.ElideRight }
                                        Text { text: modelData.serial; color: Style.textDisabled; font.pixelSize: 10; elide: Text.ElideRight }
                                    }
                                    Icon { 
                                        name: "expand_more"; size: 14; color: Style.textSecondary; rotation: deviceDelegate.expanded ? 180 : 0
                                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: deviceDelegate.expanded = !deviceDelegate.expanded }
                                    }
                                }
                                
                                RowLayout {
                                    visible: !deviceDelegate.expanded && deviceStatus.battery_level !== undefined
                                    spacing: 8
                                    Rectangle {
                                        width: 32; height: 8; color: Style.surface; radius: 4
                                        Rectangle {
                                            width: parent.width * (deviceStatus.battery_level || 0) / 100; height: parent.height
                                            color: (deviceStatus.battery_level > 20) ? Style.success : Style.error; radius: 4
                                        }
                                    }
                                    Text { text: (deviceStatus.battery_level || 0) + "%"; color: Style.textSecondary; font.pixelSize: 9 }
                                    Item { Layout.fillWidth: true }
                                    Text { text: deviceStatus.network_type === "wifi" ? "WiFi" : "USB"; color: Style.accent; font.pixelSize: 9; font.bold: true }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true; visible: deviceDelegate.expanded; spacing: 16
                                    Rectangle { Layout.fillWidth: true; height: 1; color: Style.surfaceHighlight }
                                    GridLayout {
                                        columns: 2; Layout.fillWidth: true
                                        Text { text: "Battery:"; font.pixelSize: 10; color: Style.textSecondary }
                                        Text { text: (deviceStatus.battery_level || 0) + "% (" + (deviceStatus.battery_status || "N/A") + ")"; font.pixelSize: 10; color: Style.textPrimary; Layout.alignment: Qt.AlignRight }
                                        Text { text: "Temp:"; font.pixelSize: 10; color: Style.textSecondary }
                                        Text { text: (deviceStatus.temperature || 0) + "°C"; font.pixelSize: 10; color: Style.textPrimary; Layout.alignment: Qt.AlignRight }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true; spacing: 8
                                        Text { text: "Volume"; font.pixelSize: 9; color: Style.textSecondary }
                                        Slider { Layout.fillWidth: true; from: 0; to: 15; value: deviceStatus.volume_music || 0; onMoved: bridge.set_volume(modelData.serial, "music", Math.round(value)) }
                                        Text { text: "Brightness"; font.pixelSize: 9; color: Style.textSecondary }
                                        Slider { Layout.fillWidth: true; from: 0; to: 255; value: deviceStatus.brightness || 128; onMoved: bridge.set_brightness(modelData.serial, Math.round(value)) }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true; spacing: 10
                                        Button { text: "Mirror"; Layout.fillWidth: true; onClicked: bridge.mirror_device(modelData.serial) }
                                        Button { text: "Power"; Layout.fillWidth: true; onClicked: bridge.toggle_screen(modelData.serial) }
                                        Button { text: "Shot"; Layout.fillWidth: true; onClicked: bridge.capture_screenshot(modelData.serial) }
                                    }
                                }
                            }

                            MouseArea {
                                anchors.fill: parent; anchors.rightMargin: 60; visible: !deviceDelegate.expanded
                                onClicked: bridge.select_device(modelData.serial)
                            }
                        }
                    }
                }
                
                Rectangle {
                    Layout.fillWidth: true; Layout.preferredHeight: 180; color: Style.surfaceLight; radius: 20
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 16; spacing: 12
                        Text { text: "Launch Config"; color: Style.textPrimary; font.pixelSize: 11; font.bold: true }
                        RowLayout {
                            Layout.fillWidth: true; spacing: 4
                            Repeater {
                                model: ["Tablet", "Phone", "Desktop"]
                                Button {
                                    Layout.fillWidth: true; text: modelData
                                    property bool isActive: bridge && bridge.launchMode === modelData
                                    contentItem: Text { text: parent.text; font.bold: true; font.pixelSize: 9; color: parent.isActive ? Style.background : Style.textPrimary; horizontalAlignment: Text.AlignHCenter }
                                    background: Rectangle { color: parent.isActive ? Style.accent : Style.surface; radius: 8 }
                                    onClicked: if (bridge) bridge.launchMode = modelData
                                }
                            }
                        }
                        CheckBox { 
                            text: "Screen Off"; checked: bridge ? bridge.launchWithScreenOff : false
                            contentItem: Text { text: parent.text; color: Style.textSecondary; font.pixelSize: 10; leftPadding: 30 }
                            onCheckedChanged: if (bridge) bridge.launchWithScreenOff = checked 
                        }
                    }
                }
            }
        }
    }
}
