import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."

Item {
    id: root
    
    // Model state
    readonly property bool isLoading: bridge && bridge.packagesModel.rowCount() === 0 && bridge.currentDeviceSerial !== ""

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

        // Grid Stack
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: root.isLoading ? 1 : 0

            // Grid View
            GridView {
                id: appGridView
                cellWidth: 140; cellHeight: 160; clip: true
                model: bridge ? bridge.packagesModel : null
                
                delegate: Item {
                    width: 140; height: 160
                    Rectangle {
                        width: 120; height: 140; anchors.centerIn: parent
                        color: Style.surface; radius: Style.cornerRadius
                        border.color: mouseArea.containsMouse ? Style.accent : Style.surfaceLight
                        border.width: 1
                        
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 12; spacing: 8
                            Rectangle {
                                Layout.alignment: Qt.AlignHCenter
                                width: 56; height: 56; radius: 18
                                color: Style.surfaceLight; clip: true
                                Image {
                                    anchors.fill: parent; anchors.margins: 2
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
                            Text {
                                Layout.fillWidth: true; text: name; color: Style.textPrimary
                                wrapMode: Text.Wrap; horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideMiddle; maximumLineCount: 2; font: Style.bodySmallFont
                            }
                        }
                        MouseArea {
                            id: mouseArea; anchors.fill: parent; hoverEnabled: true
                            onClicked: bridge.launch_app(packageId)
                        }
                    }
                }
            }

            // Loading State
            Item {
                ColumnLayout {
                    anchors.centerIn: parent; spacing: 20
                    BusyIndicator {
                        Layout.alignment: Qt.AlignHCenter
                        running: root.isLoading
                    }
                    Text {
                        text: "Decrypting Feed..."; color: Style.textSecondary
                        font: Style.subHeaderFont; Layout.alignment: Qt.AlignHCenter
                    }
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
            Text { text: "Select a device to begin"; color: Style.textSecondary; font: Style.subHeaderFont }
        }
    }
}
