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
        anchors.margins: 20
        spacing: 20

        // Search Bar
        TextField {
            id: searchField
            Layout.fillWidth: true
            Layout.maximumWidth: 400
            Layout.alignment: Qt.AlignHCenter
            placeholderText: "Search applications..."
            color: Style.textPrimary
            font: Style.bodyFont
            leftPadding: 15
            
            background: Rectangle {
                color: Style.surfaceLight
                radius: 20
                border.color: searchField.activeFocus ? Style.accent : "transparent"
                border.width: 1
            }

            onTextChanged: root.updateFilter()
        }

        // Grid
        GridView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            cellWidth: 160
            cellHeight: 140
            clip: true
            
            model: root.filteredList
            
            delegate: Rectangle {
                width: 140
                height: 120
                color: mouseArea.containsMouse ? Style.surfaceLight : Style.surface
                radius: 12
                border.color: Style.surfaceLight
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    
                    // Placeholder Icon
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        width: 48
                        height: 48
                        radius: 24
                        color: Style.accent
                        
                        Text {
                            anchors.centerIn: parent
                            text: modelData.substring(0, 1).toUpperCase()
                            color: "white"
                            font.bold: true
                        }
                    }
                    
                    Text {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        text: modelData
                        color: Style.textPrimary
                        wrapMode: Text.Wrap
                        horizontalAlignment: Text.AlignHCenter
                        elide: Text.ElideMiddle
                        font.pixelSize: 12
                    }
                }
                
                MouseArea {
                    id: mouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: bridge.launch_app(modelData)
                }
            }
        }
    }
    
    Text {
        anchors.centerIn: parent
        text: "Select a device to view apps"
        color: Style.textSecondary
        visible: bridge && bridge.packages.length === 0
        font.pixelSize: 16
    }
}
