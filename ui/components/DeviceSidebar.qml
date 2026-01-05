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
                anchors.fill: parent
                anchors.leftMargin: Style.spacingMedium
                anchors.rightMargin: Style.spacingMedium
                spacing: 12
                
                Rectangle {
                    width: 24
                    height: 24
                    radius: 4
                    color: Style.accent
                    
                    Text {
                        anchors.centerIn: parent
                        text: "U"
                        color: "white"
                        font.bold: true
                        font.family: Style.headerFont.family
                        font.pixelSize: 14
                    }
                }
                
                Text {
                    text: "UMC Manager"
                    font: Style.headerFont
                    color: Style.textPrimary
                }
                
                Item { Layout.fillWidth: true }
            }
        }
        
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Style.divider
        }

        // Section Title: Devices
        Item {
            Layout.fillWidth: true
            height: 40
            
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Style.spacingMedium
                anchors.rightMargin: Style.spacingMedium
                
                Text {
                    text: "CONNECTED DEVICES"
                    font.family: Style.bodySmallFont.family
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                    color: Style.textSecondary
                    Layout.fillWidth: true
                }
                
                // Refresh Button
                Item {
                    width: 24
                    height: 24
                    
                    Icon {
                        anchors.centerIn: parent
                        name: "refresh"
                        size: 14
                        color: refreshArea.pressed ? Style.textPrimary : Style.textSecondary
                        rotation: refreshArea.pressed ? 180 : 0
                        Behavior on rotation { NumberAnimation { duration: 200 } }
                    }
                    
                    MouseArea {
                        id: refreshArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: bridge.refresh_devices()
                    }
                }
            }
        }

        // Device List
        ListView {
            id: deviceList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: bridge ? bridge.devices : []
            boundsBehavior: Flickable.StopAtBounds
            
            delegate: Rectangle {
                id: deviceDelegate
                width: ListView.view.width
                height: modelData.expanded ? 120 : 50
                color: {
                    if (bridge && bridge.currentDeviceSerial === modelData.serial) return Style.surfaceHighlight
                    return ma.containsMouse ? Style.surfaceLight : "transparent"
                }
                
                property bool isSelected: bridge && bridge.currentDeviceSerial === modelData.serial
                property bool expanded: false
                property var deviceStatus: ({})
                
                // Load device status
                Component.onCompleted: {
                    try {
                        if (bridge && modelData.serial) {
                            var status = bridge.get_device_status(modelData.serial)
                            if (status) {
                                deviceStatus = status
                            }
                        }
                    } catch (e) {
                        // Silently fail - device may not be ready
                    }
                }
                
                // Listen for status updates
                Connections {
                    target: bridge
                    function onDeviceStatusChanged(serial, status) {
                        if (serial === modelData.serial) {
                            deviceDelegate.deviceStatus = status
                        }
                    }
                }

                MouseArea {
                    id: ma
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        bridge.select_device(modelData.serial)
                    }
                    onDoubleClicked: {
                        deviceDelegate.expanded = !deviceDelegate.expanded
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: Style.spacingMedium
                    anchors.rightMargin: Style.spacingMedium
                    spacing: 12
                    
                    // Device Icon
                    Icon {
                        name: "device_phone"
                        size: 16
                        color: parent.parent.isSelected ? Style.accent : Style.textSecondary
                    }
                    
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        
                        Text {
                            text: modelData.custom_name || modelData.model
                            color: parent.parent.parent.isSelected ? Style.textPrimary : Style.textSecondary
                            font.family: Style.bodyFont.family
                            font.pixelSize: 12
                            font.weight: Font.Medium
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: modelData.serial
                            color: Style.textDisabled
                            font.pixelSize: 10
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        
                        // Status indicators row
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            visible: deviceDelegate.deviceStatus && Object.keys(deviceDelegate.deviceStatus).length > 0
                            
                            // Battery indicator
                            Item {
                                visible: deviceDelegate.deviceStatus && deviceDelegate.deviceStatus.battery_level !== undefined && deviceDelegate.deviceStatus.battery_level !== null
                                width: 40
                                height: 12
                                
                                Rectangle {
                                    anchors.fill: parent
                                    anchors.margins: 1
                                    color: Style.surfaceLight
                                    radius: 2
                                    
                                    Rectangle {
                                        width: parent.width * Math.min(deviceDelegate.deviceStatus.battery_level || 0, 100) / 100
                                        height: parent.height
                                        color: {
                                            var level = deviceDelegate.deviceStatus.battery_level || 0
                                            if (level > 50) return "#4CAF50"
                                            if (level > 20) return "#FF9800"
                                            return "#F44336"
                                        }
                                        radius: 2
                                    }
                                }
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: (deviceDelegate.deviceStatus && deviceDelegate.deviceStatus.battery_level !== undefined ? deviceDelegate.deviceStatus.battery_level : 0) + "%"
                                    font.pixelSize: 8
                                    color: Style.textPrimary
                                }
                            }
                            
                            // Network type indicator
                            Text {
                                visible: deviceDelegate.deviceStatus && deviceDelegate.deviceStatus.network_type !== undefined && deviceDelegate.deviceStatus.network_type !== ""
                                text: deviceDelegate.deviceStatus && deviceDelegate.deviceStatus.network_type === "wifi" ? "WiFi" : "USB"
                                font.pixelSize: 8
                                color: Style.textSecondary
                            }
                            
                            // Temperature indicator
                            Text {
                                visible: deviceDelegate.deviceStatus && deviceDelegate.deviceStatus.temperature !== undefined && deviceDelegate.deviceStatus.temperature !== null
                                text: Math.round((deviceDelegate.deviceStatus && deviceDelegate.deviceStatus.temperature) ? deviceDelegate.deviceStatus.temperature : 0) + "°C"
                                font.pixelSize: 8
                                color: {
                                    var temp = deviceDelegate.deviceStatus.temperature || 0
                                    if (temp > 45) return "#F44336"
                                    if (temp > 40) return "#FF9800"
                                    return Style.textSecondary
                                }
                            }
                            
                            Item { Layout.fillWidth: true }
                        }
                    }

                    // Expand/Collapse button
                    Rectangle {
                        width: 24
                        height: 24
                        radius: 4
                        color: expandBtnArea.containsMouse ? Style.background : "transparent"
                        visible: ma.containsMouse || parent.parent.isSelected
                        
                        Icon {
                            anchors.centerIn: parent
                            name: "expand_more"
                            size: 14
                            color: Style.textSecondary
                            rotation: deviceDelegate.expanded ? 180 : 0
                            Behavior on rotation { NumberAnimation { duration: 200 } }
                        }
                        
                        MouseArea {
                            id: expandBtnArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                deviceDelegate.expanded = !deviceDelegate.expanded
                            }
                        }
                    }
                    
                    // Actions Row
                    Row {
                        spacing: 4
                        visible: ma.containsMouse || parent.parent.isSelected
                        
                        // Open/Mirror Button
                        Rectangle {
                            width: 24
                            height: 24
                            radius: 4
                            color: openBtnArea.containsMouse ? Style.background : "transparent"
                            
                            Icon {
                                anchors.centerIn: parent
                                name: "open_in_new"
                                size: 14
                                color: openBtnArea.pressed ? Style.accent : Style.textSecondary
                            }
                            
                            MouseArea {
                                id: openBtnArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: (mouse) => {
                                    openMenu.open()
                                    mouse.accepted = true
                                }
                                ToolTip.visible: containsMouse
                                ToolTip.text: "Open Screen..."
                                ToolTip.delay: 500
                            }
                            
                            Menu {
                                id: openMenu
                                y: parent.height
                                width: 180
                                
                                background: Rectangle {
                                    implicitWidth: 180
                                    implicitHeight: 40
                                    color: Style.surface
                                    border.color: Style.divider
                                    radius: 4
                                }
                                
                                MenuItem {
                                    text: "Mirror (Default)"
                                    font: Style.bodySmallFont
                                    onTriggered: if(bridge) bridge.mirror_device(modelData.serial)
                                    
                                    contentItem: Text {
                                        text: parent.text
                                        font: parent.font
                                        color: parent.highlighted ? Style.accent : Style.textPrimary
                                        horizontalAlignment: Text.AlignLeft
                                        verticalAlignment: Text.AlignVCenter
                                        leftPadding: 12
                                    }
                                    background: Rectangle {
                                        color: parent.highlighted ? Style.surfaceLight : "transparent"
                                    }
                                }
                                
                                MenuSeparator {
                                    contentItem: Rectangle {
                                        width: 180
                                        height: 1
                                        color: Style.divider
                                    }
                                }
                                
                                MenuItem {
                                    text: "New Phone Screen"
                                    font: Style.bodySmallFont
                                    onTriggered: if(bridge) bridge.open_display(modelData.serial, "Phone")
                                    
                                    contentItem: Text {
                                        text: parent.text
                                        font: parent.font
                                        color: parent.highlighted ? Style.accent : Style.textPrimary
                                        horizontalAlignment: Text.AlignLeft
                                        verticalAlignment: Text.AlignVCenter
                                        leftPadding: 12
                                    }
                                    background: Rectangle {
                                        color: parent.highlighted ? Style.surfaceLight : "transparent"
                                    }
                                }
                                
                                MenuItem {
                                    text: "New Tablet Screen"
                                    font: Style.bodySmallFont
                                    onTriggered: if(bridge) bridge.open_display(modelData.serial, "Tablet")
                                    
                                    contentItem: Text {
                                        text: parent.text
                                        font: parent.font
                                        color: parent.highlighted ? Style.accent : Style.textPrimary
                                        horizontalAlignment: Text.AlignLeft
                                        verticalAlignment: Text.AlignVCenter
                                        leftPadding: 12
                                    }
                                    background: Rectangle {
                                        color: parent.highlighted ? Style.surfaceLight : "transparent"
                                    }
                                }
                                
                                MenuItem {
                                    text: "New Desktop Screen"
                                    font: Style.bodySmallFont
                                    onTriggered: if(bridge) bridge.open_display(modelData.serial, "Desktop")
                                    
                                    contentItem: Text {
                                        text: parent.text
                                        font: parent.font
                                        color: parent.highlighted ? Style.accent : Style.textPrimary
                                        horizontalAlignment: Text.AlignLeft
                                        verticalAlignment: Text.AlignVCenter
                                        leftPadding: 12
                                    }
                                    background: Rectangle {
                                        color: parent.highlighted ? Style.surfaceLight : "transparent"
                                    }
                                }
                            }
                        }

                        // Power Button
                        Rectangle {
                            width: 24
                            height: 24
                            radius: 4
                            color: powerBtnArea.containsMouse ? Style.background : "transparent"
                            
                            Icon {
                                anchors.centerIn: parent
                                name: "power"
                                size: 14
                                color: powerBtnArea.pressed ? Style.error : Style.textSecondary
                            }
                            
                            MouseArea {
                                id: powerBtnArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: (mouse) => {
                                    if (bridge) {
                                        bridge.toggle_screen(modelData.serial)
                                        // Prevent selecting the row when clicking the button
                                        mouse.accepted = true
                                    }
                                }
                                ToolTip.visible: containsMouse
                                ToolTip.text: "Toggle Power (Device)"
                                ToolTip.delay: 500
                            }
                        }
                    }
                }
                
                // Expanded device details
                ColumnLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.topMargin: 50
                    anchors.margins: Style.spacingMedium
                    spacing: 8
                    visible: deviceDelegate.expanded
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Style.divider
                    }
                    
                    // Storage info
                    Item {
                        Layout.fillWidth: true
                        height: 20
                        visible: deviceDelegate.deviceStatus && deviceDelegate.deviceStatus.storage !== undefined && deviceDelegate.deviceStatus.storage !== null
                        
                        Text {
                            anchors.left: parent.left
                            text: "Storage:"
                            font.pixelSize: 10
                            color: Style.textSecondary
                        }
                        
                        Text {
                            anchors.right: parent.right
                            text: {
                                if (deviceDelegate.deviceStatus && deviceDelegate.deviceStatus.storage) {
                                    var s = deviceDelegate.deviceStatus.storage
                                    if (s && s.used !== undefined && s.total !== undefined) {
                                        var used = Math.round(s.used / 1024)
                                        var total = Math.round(s.total / 1024)
                                        return used + "GB / " + total + "GB"
                                    }
                                }
                                return ""
                            }
                            font.pixelSize: 10
                            color: Style.textPrimary
                        }
                    }
                    
                    // Battery status
                    Text {
                        Layout.fillWidth: true
                        visible: deviceDelegate.deviceStatus && deviceDelegate.deviceStatus.battery_status !== undefined && deviceDelegate.deviceStatus.battery_status !== ""
                        text: "Battery: " + (deviceDelegate.deviceStatus && deviceDelegate.deviceStatus.battery_status ? deviceDelegate.deviceStatus.battery_status : "")
                        font.pixelSize: 10
                        color: Style.textSecondary
                    }
                    
                    // Device name editor
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        
                        TextField {
                            id: deviceNameField
                            Layout.fillWidth: true
                            placeholderText: "Custom name..."
                            text: modelData.custom_name || ""
                            font.pixelSize: 10
                            height: 24
                            
                            background: Rectangle {
                                color: Style.surfaceLight
                                radius: 2
                                border.color: deviceNameField.activeFocus ? Style.accent : "transparent"
                                border.width: 1
                            }
                            
                            onAccepted: {
                                if (bridge) {
                                    bridge.set_device_name(modelData.serial, text)
                                }
                            }
                        }
                        
                        Rectangle {
                            width: 24
                            height: 24
                            radius: 4
                            color: saveNameBtnArea.containsMouse ? Style.background : "transparent"
                            
                            Icon {
                                anchors.centerIn: parent
                                name: "check"
                                size: 12
                                color: Style.accent
                            }
                            
                            MouseArea {
                                id: saveNameBtnArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (bridge) {
                                        bridge.set_device_name(modelData.serial, deviceNameField.text)
                                    }
                                }
                            }
                        }
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Style.divider
                    }
                    
                    // Clipboard sync toggle
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        
                        Text {
                            text: "Clipboard Sync:"
                            font.pixelSize: 10
                            color: Style.textSecondary
                        }
                        
                        Item { Layout.fillWidth: true }
                        
                        Rectangle {
                            id: clipboardToggle
                            width: 36
                            height: 20
                            radius: 10
                            color: clipboardToggle.enabled ? Style.accent : Style.surfaceLight
                            
                            property bool enabled: false
                            
                            Component.onCompleted: {
                                if (bridge) {
                                    enabled = bridge.get_clipboard_sync(modelData.serial)
                                }
                            }
                            
                            Rectangle {
                                anchors.verticalCenter: parent.verticalCenter
                                x: clipboardToggle.enabled ? parent.width - width - 2 : 2
                                width: 16
                                height: 16
                                radius: 8
                                color: "white"
                                
                                Behavior on x { NumberAnimation { duration: 200 } }
                            }
                            
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (bridge) {
                                        var newState = !clipboardToggle.enabled
                                        bridge.set_clipboard_sync(modelData.serial, newState)
                                        clipboardToggle.enabled = newState
                                    }
                                }
                            }
                        }
                    }
                    
                    // File transfer area
                    Rectangle {
                        Layout.fillWidth: true
                        height: 70
                        color: Style.surfaceLight
                        radius: 4
                        border.color: Style.divider
                        border.width: 1
                        
                        property int transferProgress: 0
                        property string currentOperation: ""
                        
                        // Listen for transfer progress
                        Connections {
                            target: bridge
                            function onFileTransferProgress(serial, operation, progress) {
                                if (serial === modelData.serial) {
                                    parent.transferProgress = progress
                                    parent.currentOperation = operation
                                }
                            }
                            function onFileTransferComplete(serial, operation, success) {
                                if (serial === modelData.serial) {
                                    parent.transferProgress = 0
                                    parent.currentOperation = ""
                                }
                            }
                        }
                        
                        // Drag and drop area
                        DropArea {
                            id: dropArea
                            anchors.fill: parent
                            
                            onDropped: function(drop) {
                                if (drop.hasUrls && bridge && modelData.serial) {
                                    var urls = drop.urls
                                    for (var i = 0; i < urls.length; i++) {
                                        var filePath = urls[i].toString().replace("file://", "")
                                        if (filePath && modelData.serial) {
                                            bridge.push_file_to_device(modelData.serial, filePath)
                                        }
                                    }
                                }
                            }
                            
                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: 4
                                color: Style.accent
                                radius: 2
                                opacity: dropArea.containsDrag ? 0.2 : 0
                                
                                Behavior on opacity { NumberAnimation { duration: 150 } }
                            }
                            
                            ColumnLayout {
                                anchors.centerIn: parent
                                spacing: 4
                                
                                Icon {
                                    Layout.alignment: Qt.AlignHCenter
                                    name: "file_upload"
                                    size: 20
                                    color: Style.textSecondary
                                }
                                
                                Text {
                                    Layout.alignment: Qt.AlignHCenter
                                    text: parent.parent.parent.transferProgress > 0 ? 
                                          (parent.parent.parent.currentOperation === "push" ? "Uploading..." : "Downloading...") : 
                                          "Drop files here"
                                    font.pixelSize: 9
                                    color: Style.textSecondary
                                }
                            }
                            
                            // Progress bar
                            Rectangle {
                                anchors.bottom: parent.bottom
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.margins: 4
                                height: 4
                                radius: 2
                                color: Style.surface
                                visible: parent.parent.transferProgress > 0
                                
                                Rectangle {
                                    width: parent.width * (parent.parent.transferProgress / 100)
                                    height: parent.height
                                    color: Style.accent
                                    radius: 2
                                    
                                    Behavior on width { NumberAnimation { duration: 100 } }
                                }
                            }
                        }
                        
                        // File transfer button
                        Rectangle {
                            anchors.right: parent.right
                            anchors.rightMargin: 4
                            anchors.top: parent.top
                            anchors.topMargin: 4
                            width: 24
                            height: 24
                            radius: 4
                            color: fileBtnArea.containsMouse ? Style.background : "transparent"
                            
                            Icon {
                                anchors.centerIn: parent
                                name: "folder"
                                size: 12
                                color: Style.textSecondary
                            }
                            
                            MouseArea {
                                id: fileBtnArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    // Request file selection
                                    if (bridge) {
                                        bridge.request_file_selection(modelData.serial)
                                    }
                                }
                            }
                        }
                    }
                    
                    // File dialog - using native file picker via bridge
                    Connections {
                        target: bridge
                        function onFileSelected(filePath) {
                            if (filePath && modelData.serial) {
                                bridge.push_file_to_device(modelData.serial, filePath)
                            }
                        }
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Style.divider
                    }
                    
                    // Screenshot button
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        
                        Text {
                            text: "Screenshot:"
                            font.pixelSize: 10
                            color: Style.textSecondary
                        }
                        
                        Item { Layout.fillWidth: true }
                        
                        Rectangle {
                            width: 24
                            height: 24
                            radius: 4
                            color: screenshotBtnArea.containsMouse ? Style.background : "transparent"
                            
                            Icon {
                                anchors.centerIn: parent
                                name: "screenshot"
                                size: 14
                                color: Style.textSecondary
                            }
                            
                            MouseArea {
                                id: screenshotBtnArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (bridge) {
                                        bridge.capture_screenshot(modelData.serial)
                                    }
                                }
                                ToolTip.visible: containsMouse
                                ToolTip.text: "Capture Screenshot"
                                ToolTip.delay: 500
                            }
                        }
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Style.divider
                    }
                    
                    // Device Controls Section
                    Text {
                        Layout.fillWidth: true
                        text: "DEVICE CONTROLS"
                        font.pixelSize: 9
                        font.weight: Font.DemiBold
                        color: Style.textSecondary
                    }
                    
                    // Volume Control
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            
                            Icon {
                                name: "volume"
                                size: 12
                                color: Style.textSecondary
                            }
                            
                            Text {
                                text: "Volume (Media):"
                                font.pixelSize: 10
                                color: Style.textSecondary
                            }
                            
                            Item { Layout.fillWidth: true }
                            
                            Text {
                                id: volumeText
                                text: "0"
                                font.pixelSize: 10
                                color: Style.textPrimary
                                width: 20
                            }
                        }
                        
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            
                            Icon {
                                name: "volume_down"
                                size: 10
                                color: Style.textSecondary
                            }
                            
                            Slider {
                                id: volumeSlider
                                Layout.fillWidth: true
                                from: 0
                                to: 15
                                value: 0
                                
                                onValueChanged: {
                                    volumeText.text = Math.round(value)
                                    if (bridge && modelData.serial) {
                                        bridge.set_volume(modelData.serial, "music", Math.round(value))
                                    }
                                }
                                
                                Component.onCompleted: {
                                    try {
                                        if (bridge && modelData.serial) {
                                            var vol = bridge.get_volume(modelData.serial, "music")
                                            if (vol !== undefined && vol !== null) {
                                                value = vol
                                            }
                                        }
                                    } catch (e) {
                                        // Silently fail - device may not be ready
                                    }
                                }
                            }
                            
                            Icon {
                                name: "volume"
                                size: 10
                                color: Style.textSecondary
                            }
                        }
                    }
                    
                    // Brightness Control
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            
                            Icon {
                                name: "brightness"
                                size: 12
                                color: Style.textSecondary
                            }
                            
                            Text {
                                text: "Brightness:"
                                font.pixelSize: 10
                                color: Style.textSecondary
                            }
                            
                            Item { Layout.fillWidth: true }
                            
                            Text {
                                id: brightnessText
                                text: "128"
                                font.pixelSize: 10
                                color: Style.textPrimary
                                width: 30
                            }
                        }
                        
                        Slider {
                            id: brightnessSlider
                            Layout.fillWidth: true
                            from: 0
                            to: 255
                            value: 128
                            
                            onValueChanged: {
                                brightnessText.text = Math.round(value)
                                if (bridge && modelData.serial) {
                                    bridge.set_brightness(modelData.serial, Math.round(value))
                                }
                            }
                            
                            Component.onCompleted: {
                                try {
                                    if (bridge && modelData.serial) {
                                        var bright = bridge.get_brightness(modelData.serial)
                                        if (bright !== undefined && bright !== null) {
                                            value = bright
                                        }
                                    }
                                } catch (e) {
                                    // Silently fail - device may not be ready
                                }
                            }
                        }
                    }
                    
                    // Quick Toggles
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        rowSpacing: 8
                        columnSpacing: 8
                        
                        // Rotation Lock
                        RowLayout {
                            spacing: 4
                            
                            Icon {
                                name: "rotation"
                                size: 12
                                color: Style.textSecondary
                            }
                            
                            Text {
                                text: "Rotation Lock:"
                                font.pixelSize: 10
                                color: Style.textSecondary
                            }
                            
                            Item { Layout.fillWidth: true }
                            
                            Rectangle {
                                id: rotationToggle
                                width: 36
                                height: 20
                                radius: 10
                                color: rotationToggle.enabled ? Style.accent : Style.surfaceLight
                                
                                property bool enabled: false
                                
                                Component.onCompleted: {
                                    try {
                                        if (bridge && modelData.serial) {
                                            var locked = bridge.get_rotation_lock(modelData.serial)
                                            if (locked !== undefined && locked !== null) {
                                                enabled = locked
                                            }
                                        }
                                    } catch (e) {
                                        // Silently fail - device may not be ready
                                    }
                                }
                                
                                Rectangle {
                                    anchors.verticalCenter: parent.verticalCenter
                                    x: rotationToggle.enabled ? parent.width - width - 2 : 2
                                    width: 16
                                    height: 16
                                    radius: 8
                                    color: "white"
                                    
                                    Behavior on x { NumberAnimation { duration: 200 } }
                                }
                                
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (bridge && modelData.serial) {
                                            var newState = !rotationToggle.enabled
                                            bridge.set_rotation_lock(modelData.serial, newState)
                                            rotationToggle.enabled = newState
                                        }
                                    }
                                }
                            }
                        }
                        
                        // Airplane Mode
                        RowLayout {
                            spacing: 4
                            
                            Icon {
                                name: "airplane"
                                size: 12
                                color: Style.textSecondary
                            }
                            
                            Text {
                                text: "Airplane Mode:"
                                font.pixelSize: 10
                                color: Style.textSecondary
                            }
                            
                            Item { Layout.fillWidth: true }
                            
                            Rectangle {
                                id: airplaneToggle
                                width: 36
                                height: 20
                                radius: 10
                                color: airplaneToggle.enabled ? Style.accent : Style.surfaceLight
                                
                                property bool enabled: false
                                
                                Component.onCompleted: {
                                    try {
                                        if (bridge && modelData.serial) {
                                            var airplane = bridge.get_airplane_mode(modelData.serial)
                                            if (airplane !== undefined && airplane !== null) {
                                                enabled = airplane
                                            }
                                        }
                                    } catch (e) {
                                        // Silently fail - device may not be ready
                                    }
                                }
                                
                                Rectangle {
                                    anchors.verticalCenter: parent.verticalCenter
                                    x: airplaneToggle.enabled ? parent.width - width - 2 : 2
                                    width: 16
                                    height: 16
                                    radius: 8
                                    color: "white"
                                    
                                    Behavior on x { NumberAnimation { duration: 200 } }
                                }
                                
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (bridge && modelData.serial) {
                                            var newState = !airplaneToggle.enabled
                                            bridge.set_airplane_mode(modelData.serial, newState)
                                            airplaneToggle.enabled = newState
                                        }
                                    }
                                }
                            }
                        }
                        
                        // WiFi
                        RowLayout {
                            spacing: 4
                            
                            Icon {
                                name: "wifi"
                                size: 12
                                color: Style.textSecondary
                            }
                            
                            Text {
                                text: "WiFi:"
                                font.pixelSize: 10
                                color: Style.textSecondary
                            }
                            
                            Item { Layout.fillWidth: true }
                            
                            Rectangle {
                                id: wifiToggle
                                width: 36
                                height: 20
                                radius: 10
                                color: wifiToggle.enabled ? Style.accent : Style.surfaceLight
                                
                                property bool enabled: true
                                
                                Component.onCompleted: {
                                    try {
                                        if (bridge && modelData.serial) {
                                            var wifi = bridge.get_wifi_enabled(modelData.serial)
                                            if (wifi !== undefined && wifi !== null) {
                                                enabled = wifi
                                            }
                                        }
                                    } catch (e) {
                                        // Silently fail - device may not be ready
                                    }
                                }
                                
                                Rectangle {
                                    anchors.verticalCenter: parent.verticalCenter
                                    x: wifiToggle.enabled ? parent.width - width - 2 : 2
                                    width: 16
                                    height: 16
                                    radius: 8
                                    color: "white"
                                    
                                    Behavior on x { NumberAnimation { duration: 200 } }
                                }
                                
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (bridge && modelData.serial) {
                                            var newState = !wifiToggle.enabled
                                            bridge.set_wifi_enabled(modelData.serial, newState)
                                            wifiToggle.enabled = newState
                                        }
                                    }
                                }
                            }
                        }
                        
                        // Bluetooth
                        RowLayout {
                            spacing: 4
                            
                            Icon {
                                name: "bluetooth"
                                size: 12
                                color: Style.textSecondary
                            }
                            
                            Text {
                                text: "Bluetooth:"
                                font.pixelSize: 10
                                color: Style.textSecondary
                            }
                            
                            Item { Layout.fillWidth: true }
                            
                            Rectangle {
                                id: bluetoothToggle
                                width: 36
                                height: 20
                                radius: 10
                                color: bluetoothToggle.enabled ? Style.accent : Style.surfaceLight
                                
                                property bool enabled: false
                                
                                Component.onCompleted: {
                                    try {
                                        if (bridge && modelData.serial) {
                                            var bluetooth = bridge.get_bluetooth_enabled(modelData.serial)
                                            if (bluetooth !== undefined && bluetooth !== null) {
                                                enabled = bluetooth
                                            }
                                        }
                                    } catch (e) {
                                        // Silently fail - device may not be ready
                                    }
                                }
                                
                                Rectangle {
                                    anchors.verticalCenter: parent.verticalCenter
                                    x: bluetoothToggle.enabled ? parent.width - width - 2 : 2
                                    width: 16
                                    height: 16
                                    radius: 8
                                    color: "white"
                                    
                                    Behavior on x { NumberAnimation { duration: 200 } }
                                }
                                
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (bridge && modelData.serial) {
                                            var newState = !bluetoothToggle.enabled
                                            bridge.set_bluetooth_enabled(modelData.serial, newState)
                                            bluetoothToggle.enabled = newState
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Style.divider
        }

        // Settings / Launch Mode Area
        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: Style.spacingMedium
            spacing: 12

            Text {
                text: "LAUNCH SETTINGS"
                font.family: Style.bodySmallFont.family
                font.pixelSize: 10
                font.weight: Font.DemiBold
                color: Style.textSecondary
            }

            // Mode Switcher
            RowLayout {
                Layout.fillWidth: true
                spacing: 0
                
                Repeater {
                    model: ["Tablet", "Phone", "Desktop"]
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        height: 28
                        color: (bridge && bridge.launchMode === modelData) ? Style.accent : Style.surfaceLight
                        
                        // First item radius left, last item radius right
                        radius: 2
                        
                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            color: (bridge && bridge.launchMode === modelData) ? "white" : Style.textSecondary
                            font.pixelSize: 11
                            font.weight: Font.Medium
                        }
                        
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: if (bridge) bridge.launchMode = modelData
                        }
                    }
                }
            }
            
            // Checkboxes
            ColumnLayout {
                spacing: 8
                
                CheckBox {
                    id: screenOffCheck
                    text: "Launch with Screen Off"
                    checked: bridge ? bridge.launchWithScreenOff : false
                    onCheckedChanged: if (bridge) bridge.launchWithScreenOff = checked
                    
                    contentItem: Text {
                        text: screenOffCheck.text
                        font: Style.bodySmallFont
                        color: Style.textPrimary
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: screenOffCheck.indicator.width + 8
                    }
                    
                    indicator: Rectangle {
                        implicitWidth: 16
                        implicitHeight: 16
                        x: 0
                        y: parent.height / 2 - height / 2
                        radius: 3
                        border.color: screenOffCheck.checked ? Style.accent : Style.textSecondary
                        color: screenOffCheck.checked ? Style.accent : "transparent"
                        
                        Icon {
                            anchors.centerIn: parent
                            name: "check" // We need to add check to Icon.qml or use simple rect
                            visible: screenOffCheck.checked
                            size: 10
                            color: "white"
                        }
                        // Fallback simple check indicator if icon missing
                        Rectangle {
                            anchors.centerIn: parent
                            width: 8; height: 8; radius: 1
                            color: "white"
                            visible: screenOffCheck.checked && true // Replace with Icon usage
                        }
                    }
                }
                
                CheckBox {
                    id: audioCheck
                    text: "Forward Audio"
                    checked: bridge ? bridge.audioForwarding : false
                    onCheckedChanged: if (bridge) bridge.audioForwarding = checked
                    
                    contentItem: Text {
                        text: audioCheck.text
                        font: Style.bodySmallFont
                        color: Style.textPrimary
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: audioCheck.indicator.width + 8
                    }
                    
                    indicator: Rectangle {
                        implicitWidth: 16
                        implicitHeight: 16
                        x: 0
                        y: parent.height / 2 - height / 2
                        radius: 3
                        border.color: audioCheck.checked ? Style.accent : Style.textSecondary
                        color: audioCheck.checked ? Style.accent : "transparent"
                        
                        Rectangle {
                            anchors.centerIn: parent
                            width: 8; height: 8; radius: 1
                            color: "white"
                            visible: audioCheck.checked
                        }
                    }
                }
                
                Item { height: 8; width: 1 } // Spacer
                
                Text {
                    text: "PERFORMANCE PROFILE"
                    font.family: Style.bodySmallFont.family
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                    color: Style.textSecondary
                }

                ComboBox {
                    id: profileCombo
                    Layout.fillWidth: true
                    height: 28
                    model: bridge ? bridge.profiles : []
                    
                    onActivated: (index) => {
                        if (bridge) bridge.currentProfile = textAt(index)
                    }
                    
                    Component.onCompleted: {
                        if (bridge) currentIndex = find(bridge.currentProfile)
                    }
                    
                    Connections {
                        target: bridge
                        function onCurrentProfileChanged(profile) {
                            if (profileCombo.find) {
                                var idx = profileCombo.find(profile)
                                if (idx !== -1) profileCombo.currentIndex = idx
                            }
                        }
                    }

                    delegate: ItemDelegate {
                        width: parent.width
                        contentItem: Text {
                            text: modelData
                            color: highlighted ? "white" : Style.textPrimary
                            font: Style.bodySmallFont
                            elide: Text.ElideRight
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            color: highlighted ? Style.accent : "transparent"
                        }
                    }

                    contentItem: Text {
                        leftPadding: 8
                        rightPadding: profileCombo.indicator.width + 8
                        text: profileCombo.displayText
                        font: Style.bodySmallFont
                        color: Style.textPrimary
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }

                    background: Rectangle {
                        color: Style.surfaceLight
                        radius: 2
                        border.color: "transparent"
                    }
                    
                    popup: Popup {
                        y: profileCombo.height - 1
                        width: profileCombo.width
                        implicitHeight: contentItem.implicitHeight
                        padding: 1

                        contentItem: ListView {
                            clip: true
                            implicitHeight: contentHeight
                            model: profileCombo.delegateModel
                            currentIndex: profileCombo.highlightedIndex
                            ScrollIndicator.vertical: ScrollIndicator { }
                        }

                        background: Rectangle {
                            color: Style.surface
                            border.color: Style.divider
                            radius: 2
                        }
                    }
                }
            }
        }
    }
}
