import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."

Item {
    id: root
    readonly property bool loading: bridge && bridge.loading

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24; spacing: 24

        // 🔍 M3 Search Bar
        Rectangle {
            Layout.fillWidth: true; Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: Math.min(parent.width - 40, 720)
            height: 56; radius: 28; color: Style.surfaceLight
            
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 12; spacing: 12
                Icon { name: "search"; size: 18; color: Style.textSecondary }
                TextField {
                    id: searchField; Layout.fillWidth: true; placeholderText: "Search apps on " + (bridge ? bridge.currentDeviceSerial : "device")
                    color: Style.textPrimary; font: Style.bodyFont; background: null; selectByMouse: true
                    onTextChanged: if (bridge) bridge.packagesModel.filterText = text.trim()
                }
                Rectangle {
                    width: 32; height: 32; radius: 16; color: Style.surface; visible: searchField.text.length > 0
                    Text { anchors.centerIn: parent; text: "✕"; color: Style.textSecondary; font.pixelSize: 10 }
                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: searchField.text = "" }
                }
            }
        }

        // 📱 Grid Section
        StackLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; currentIndex: root.loading ? 1 : 0

            GridView {
                id: appGridView; cellWidth: 160; cellHeight: 180; clip: true; boundsBehavior: Flickable.StopAtBounds
                model: bridge ? bridge.packagesModel : null
                
                delegate: Item {
                    width: appGridView.cellWidth; height: appGridView.cellHeight
                    
                    Rectangle {
                        id: cardBg; width: 140; height: 160; anchors.centerIn: parent
                        radius: 24; color: mouseArea.containsMouse ? Style.surfaceHighlight : "transparent"
                        
                        Behavior on color { ColorAnimation { duration: 150 } }

                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 16; spacing: 12
                            
                            // App Icon (M3 Tonal Container style)
                            Rectangle {
                                Layout.alignment: Qt.AlignHCenter
                                width: 72; height: 72; radius: 20
                                color: mouseArea.containsMouse ? Style.accentVariant : Style.surfaceLight
                                
                                Behavior on color { ColorAnimation { duration: 150 } }
                                
                                Image {
                                    anchors.fill: parent; anchors.margins: 12; fillMode: Image.PreserveAspectFit; asynchronous: true
                                    source: icon ? "file://" + icon : ""
                                    Component.onCompleted: if (!icon && bridge) bridge.fetch_icon_for_package(packageId)
                                }
                                
                                Text {
                                    anchors.centerIn: parent; visible: !icon
                                    text: (name || "?").substring(0, 1).toUpperCase()
                                    color: Style.accent; font.bold: true; font.pixelSize: 28
                                }
                            }
                            
                            Text {
                                Layout.fillWidth: true; text: name || packageId || ""; color: Style.textPrimary
                                font: Style.bodySmallFont; wrapMode: Text.Wrap; horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideRight; maximumLineCount: 2
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
                            MenuItem { text: "Launch App"; onTriggered: bridge.launch_app(packageId) }
                            MenuItem { text: "Force Stop"; onTriggered: bridge.force_stop_app(packageId) }
                            background: Rectangle { color: Style.surface; radius: 12; border.color: Style.surfaceHighlight; border.width: 1 }
                        }
                    }
                }
            }

            // 🔄 Loading State
            Item {
                ColumnLayout {
                    anchors.centerIn: parent; spacing: 24
                    BusyIndicator { Layout.alignment: Qt.AlignHCenter; running: root.loading; palette.dark: Style.accent }
                    Text { text: "SYNCING DATA..."; color: Style.textSecondary; font.pixelSize: 11; font.letterSpacing: 2; font.weight: Font.DemiBold; Layout.alignment: Qt.AlignHCenter }
                }
            }
        }
    }
    
    // 🏠 Empty/Welcome State
    Item {
        anchors.fill: parent; visible: bridge && bridge.currentDeviceSerial === ""
        ColumnLayout {
            anchors.centerIn: parent; spacing: 20
            Rectangle {
                width: 120; height: 120; radius: 60; color: Style.surfaceLight
                Icon { anchors.centerIn: parent; name: "device_phone"; size: 48; color: Style.textDisabled }
            }
            Text { text: "Select a device to begin control"; color: Style.textSecondary; font: Style.subHeaderFont; opacity: 0.7 }
        }
    }
}
