import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."

Item {
    id: root
    
    property var fullPackageList: bridge ? bridge.packages : []
    property var filteredList: []

    onFullPackageListChanged: updateFilter()

    function updateFilter() {
        var query = searchField.text.toLowerCase()
        if (query === "") {
            filteredList = fullPackageList
        } else {
            var temp = []
            for (var i = 0; i < fullPackageList.length; i++) {
                if (fullPackageList[i].toLowerCase().indexOf(query) !== -1) {
                    temp.push(fullPackageList[i])
                }
            }
            filteredList = temp
        }
    }

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
                    
                    Text {
                        text: "🔍"
                        color: Style.textSecondary
                        font.pixelSize: 14
                    }
                    
                    TextField {
                        id: searchField
                        Layout.fillWidth: true
                        placeholderText: "Search applications..."
                        color: Style.textPrimary
                        font: Style.bodyFont
                        background: null
                        selectByMouse: true
                        onTextChanged: root.updateFilter()
                    }
                    
                    // Clear button
                    Text {
                        text: "✕"
                        color: searchField.text.length > 0 ? Style.textSecondary : "transparent"
                        font.pixelSize: 14
                        visible: searchField.text.length > 0
                        
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
            Layout.fillWidth: true
            Layout.fillHeight: true
            cellWidth: 140
            cellHeight: 160
            clip: true
            
            model: root.filteredList
            
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
                    border.width: mouseArea.containsMouse ? 2 : 1
                    
                    // Hover Animation
                    scale: mouseArea.containsMouse ? 1.05 : 1.0
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
                            gradient: Gradient {
                                GradientStop { position: 0.0; color: Style.accent }
                                GradientStop { position: 1.0; color: Style.accentVariant }
                            }
                            
                            Text {
                                anchors.centerIn: parent
                                text: modelData.substring(0, 1).toUpperCase()
                                color: "white"
                                font.bold: true
                                font.pixelSize: 24
                            }
                        }
                        
                        Text {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            text: modelData
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
                        onClicked: bridge.launch_app(modelData)
                    }
                }
            }
        }
    }
    
    // Empty State
    Item {
        anchors.centerIn: parent
        visible: bridge && bridge.packages.length === 0
        width: 300
        height: 200
        
        ColumnLayout {
            anchors.centerIn: parent
            spacing: 20
            
            Text {
                text: "📱"
                font.pixelSize: 64
                Layout.alignment: Qt.AlignHCenter
                opacity: 0.5
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
