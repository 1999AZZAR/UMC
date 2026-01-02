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
                var app = fullPackageList[i]
                var packageName = app.package || app
                var appName = app.name || app
                if (packageName.toLowerCase().indexOf(query) !== -1 ||
                    appName.toLowerCase().indexOf(query) !== -1) {
                    temp.push(app)
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
                    
                    Icon {
                        name: "search"
                        size: 14
                        color: Style.textSecondary
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
                    Item {
                        width: 16
                        height: 16
                        visible: searchField.text.length > 0
                        
                        // We can use a simple X text or draw it. 
                        // For consistency let's use a Text "X" but styled better or add to Icon.qml
                        // Since I didn't add "close/clear" to Icon.qml, I'll stick to a clean Text or simple Rectangle cross
                        Text {
                            anchors.centerIn: parent
                            text: "✕"
                            color: Style.textSecondary
                            font.pixelSize: 12
                        }
                        
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
                    border.width: mouseArea.containsMouse ? 1 : 1 // Professional thin border
                    
                    // Hover Animation
                    scale: mouseArea.containsMouse ? 1.02 : 1.0
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
                            color: Style.surfaceLight // Flat color instead of gradient
                            border.color: Style.surfaceHighlight
                            border.width: 1

                            Text {
                                anchors.centerIn: parent
                                text: (modelData.name || modelData.package || modelData).substring(0, 1).toUpperCase()
                                color: Style.accent
                                font.bold: true
                                font.pixelSize: 24
                                font.family: Style.headerFont.family
                            }
                        }
                        
                        Text {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            text: modelData.name || modelData.package || modelData
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
                        onClicked: bridge.launch_app(modelData.package || modelData)
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
            
            Icon {
                Layout.alignment: Qt.AlignHCenter
                name: "device_tablet"
                size: 64
                color: Style.surfaceHighlight
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
