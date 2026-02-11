import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."

Item {
    id: root
    
    // Explicit loading state from bridge
    readonly property bool loading: bridge && bridge.loading

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: Style.spacingLarge
        anchors.rightMargin: Style.spacingLarge
        anchors.topMargin: Style.spacingLarge
        anchors.bottomMargin: Style.spacingLarge
        spacing: Style.spacingMedium

        // Search Bar Area (Better alignment and wider for grid flow)
        Item {
            Layout.fillWidth: true
            height: 50
            
            Rectangle {
                anchors.centerIn: parent
                width: Math.min(parent.width - 40, 800) // Adaptive width
                height: 44
                radius: 12
                color: Style.surfaceLight
                border.color: searchField.activeFocus ? Style.accent : Style.divider
                border.width: 1
                
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 15
                    anchors.rightMargin: 15
                    spacing: 10
                    
                    Icon { name: "search"; size: 14; color: Style.textSecondary }
                    
                    TextField {
                        id: searchField
                        Layout.fillWidth: true
                        placeholderText: "Search applications..."
                        color: Style.textPrimary
                        font: Style.bodyFont
                        background: null
                        selectByMouse: true
                        onTextChanged: if (bridge) bridge.packagesModel.filterText = text.trim()
                    }
                    
                    Item {
                        width: 16; height: 16
                        visible: searchField.text.length > 0
                        Text { anchors.centerIn: parent; text: "✕"; color: Style.textSecondary; font.pixelSize: 12 }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: searchField.text = "" }
                    }
                }
            }
        }

        // Grid Section
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: root.loading ? 1 : 0

            // Grid View with adaptive cell layout
            GridView {
                id: appGridView
                cellWidth: width / Math.floor(width / 140) // Smart width adaptation
                cellHeight: 160
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                
                model: bridge ? bridge.packagesModel : null
                
                delegate: Item {
                    width: appGridView.cellWidth
                    height: appGridView.cellHeight
                    
                    Rectangle {
                        id: cardBg
                        width: 120; height: 140; anchors.centerIn: parent
                        color: mouseArea.containsMouse ? Style.surfaceHighlight : Style.surface
                        radius: 16 // M3-like rounder corners
                        border.color: mouseArea.containsMouse ? Style.accent : "transparent"
                        border.width: 1
                        
                        scale: mouseArea.containsMouse ? 1.05 : 1.0
                        Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutQuad } }
                        Behavior on color { ColorAnimation { duration: 150 } }

                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 12; spacing: 8
                            
                            // Icon Container
                            Rectangle {
                                Layout.alignment: Qt.AlignHCenter
                                width: 56; height: 56; radius: 14
                                color: Style.surfaceLight; clip: true
                                
                                Image {
                                    anchors.fill: parent; anchors.margins: 4
                                    source: icon ? "file://" + icon : ""
                                    fillMode: Image.PreserveAspectFit
                                    asynchronous: true
                                    Component.onCompleted: if (!icon && bridge) bridge.fetch_icon_for_package(packageId)
                                }
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: (name || "").substring(0, 1).toUpperCase()
                                    color: Style.accent; font.bold: true; font.pixelSize: 24
                                    visible: !icon
                                }
                            }
                            
                            // App Label
                            Text {
                                Layout.fillWidth: true
                                text: name || packageId || ""
                                color: Style.textPrimary
                                wrapMode: Text.Wrap
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideMiddle
                                maximumLineCount: 2
                                font: Style.bodySmallFont
                            }
                        }
                        
                        MouseArea {
                            id: mouseArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: bridge.launch_app(packageId)
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            onPressAndHold: if (mouse.button === Qt.RightButton) batchMenu.open()
                        }
                        
                        Menu {
                            id: batchMenu; y: parent.height
                            background: Rectangle { color: Style.surface; border.color: Style.divider; radius: 8; border.width: 1 }
                            MenuItem {
                                text: "Launch App"; font: Style.bodySmallFont
                                onTriggered: bridge.launch_app(packageId)
                            }
                            MenuItem {
                                text: "Launch on All"; font: Style.bodySmallFont
                                onTriggered: {
                                    var serials = [];
                                    for (var i = 0; i < bridge.devices.length; i++) serials.push(bridge.devices[i].serial);
                                    bridge.launch_app_on_multiple_devices(packageId, serials);
                                }
                            }
                        }
                    }
                }
            }

            // Loading State
            Item {
                ColumnLayout {
                    anchors.centerIn: parent; spacing: 20
                    BusyIndicator { Layout.alignment: Qt.AlignHCenter; running: root.loading }
                    Text { text: "SYCHRONIZING FEED"; color: Style.textSecondary; font.pixelSize: 10; font.weight: Font.Black; Layout.alignment: Qt.AlignHCenter }
                }
            }
        }
    }
    
    // Welcome State (No device selected)
    Item {
        anchors.centerIn: parent
        visible: bridge && bridge.currentDeviceSerial === ""
        ColumnLayout {
            anchors.centerIn: parent; spacing: 20
            Icon { Layout.alignment: Qt.AlignHCenter; name: "device_tablet"; size: 64; color: Style.surfaceHighlight }
            Text { text: "Select a device to begin control"; color: Style.textSecondary; font: Style.subHeaderFont }
        }
    }
}
