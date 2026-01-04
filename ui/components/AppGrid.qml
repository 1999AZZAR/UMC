import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import ".."

Item {
    id: root
    
    property var fullPackageList: bridge ? bridge.packages : []
    property var filteredList: []

    onFullPackageListChanged: updateFilter()

    // Fuzzy search function - calculates similarity score
    function fuzzyMatch(query, text) {
        if (!query || !text) return 0
        
        var queryLower = query.toLowerCase()
        var textLower = text.toLowerCase()
        
        // Exact match gets highest score
        if (textLower === queryLower) return 100
        if (textLower.indexOf(queryLower) === 0) return 90  // Starts with
        if (textLower.indexOf(queryLower) !== -1) return 70  // Contains
        
        // Fuzzy matching: check if all query characters appear in order
        var queryIndex = 0
        var score = 0
        var consecutiveMatches = 0
        var maxConsecutive = 0
        
        for (var i = 0; i < textLower.length && queryIndex < queryLower.length; i++) {
            if (textLower[i] === queryLower[queryIndex]) {
                score += 10
                consecutiveMatches++
                maxConsecutive = Math.max(maxConsecutive, consecutiveMatches)
                queryIndex++
            } else {
                consecutiveMatches = 0
            }
        }
        
        // Bonus for consecutive matches
        score += maxConsecutive * 5
        
        // If all query characters were found, add bonus
        if (queryIndex === queryLower.length) {
            score += 20
        } else {
            // Penalty for missing characters
            score -= (queryLower.length - queryIndex) * 15
        }
        
        return Math.max(0, Math.min(100, score))
    }

    function updateFilter() {
        var query = searchField.text.trim()
        if (query === "") {
            filteredList = fullPackageList
        } else {
            var queryLower = query.toLowerCase()
            var temp = []
            var scoredApps = []
            
            for (var i = 0; i < fullPackageList.length; i++) {
                var app = fullPackageList[i]
                var packageName = app.package || app
                var appName = app.name || app
                
                // Calculate match scores for both name and package
                var nameScore = fuzzyMatch(queryLower, appName)
                var packageScore = fuzzyMatch(queryLower, packageName)
                var maxScore = Math.max(nameScore, packageScore)
                
                // Only include if score is above threshold
                if (maxScore > 20) {
                    scoredApps.push({
                        app: app,
                        score: maxScore
                    })
                }
            }
            
            // Sort by score (descending)
            scoredApps.sort(function(a, b) {
                return b.score - a.score
            })
            
            // Extract apps in sorted order
            for (var j = 0; j < scoredApps.length; j++) {
                temp.push(scoredApps[j].app)
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
                            color: Style.surfaceLight
                            border.color: Style.surfaceHighlight
                            border.width: 1
                            clip: true

                            // App Icon Image
                            Image {
                                id: appIconImage
                                anchors.fill: parent
                                anchors.margins: 2
                                property string iconSource: modelData.icon ? "file://" + modelData.icon : ""
                                source: iconSource
                                fillMode: Image.PreserveAspectFit
                                visible: iconSource !== "" && status === Image.Ready
                                smooth: true
                                antialiasing: true
                                asynchronous: true
                                
                                // Request icon fetch if not available and item is visible
                                Component.onCompleted: {
                                    if (!modelData.icon && bridge) {
                                        // Request icon fetch in background
                                        bridge.fetch_icon_for_package(modelData.package || modelData)
                                    }
                                }
                            }
                            
                            // Listen for icon updates
                            Connections {
                                target: bridge
                                function onIconReady(pkg, iconPath) {
                                    var currentPackage = modelData.package || modelData
                                    if (currentPackage === pkg) {
                                        // Update image source
                                        appIconImage.iconSource = "file://" + iconPath
                                    }
                                }
                            }

                            // Fallback: First letter if no icon
                            Text {
                                anchors.centerIn: parent
                                text: (modelData.name || modelData.package || modelData).substring(0, 1).toUpperCase()
                                color: Style.accent
                                font.bold: true
                                font.pixelSize: 24
                                font.family: Style.headerFont.family
                                visible: !appIconImage.visible || appIconImage.status !== Image.Ready
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
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        
                        onPressAndHold: {
                            if (mouse.button === Qt.RightButton) {
                                batchMenu.open()
                            }
                        }
                    }
                    
                    // Batch launch menu
                    Menu {
                        id: batchMenu
                        y: parent.height
                        
                        background: Rectangle {
                            color: Style.surface
                            border.color: Style.divider
                            radius: 4
                        }
                        
                        MenuItem {
                            text: "Launch on Selected Device"
                            font: Style.bodySmallFont
                            onTriggered: bridge.launch_app(modelData.package || modelData)
                            
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: parent.highlighted ? Style.accent : Style.textPrimary
                            }
                            background: Rectangle {
                                color: parent.highlighted ? Style.surfaceLight : "transparent"
                            }
                        }
                        
                        MenuSeparator {
                            contentItem: Rectangle {
                                width: parent.width
                                height: 1
                                color: Style.divider
                            }
                        }
                        
                        MenuItem {
                            text: "Launch on All Devices"
                            font: Style.bodySmallFont
                            onTriggered: {
                                if (bridge) {
                                    var devices = bridge.devices || []
                                    var serials = []
                                    for (var i = 0; i < devices.length; i++) {
                                        if (devices[i].serial) {
                                            serials.push(devices[i].serial)
                                        }
                                    }
                                    bridge.launch_app_on_multiple_devices(modelData.package || modelData, serials)
                                }
                            }
                            
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: parent.highlighted ? Style.accent : Style.textPrimary
                            }
                            background: Rectangle {
                                color: parent.highlighted ? Style.surfaceLight : "transparent"
                            }
                        }
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
