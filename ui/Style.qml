pragma Singleton
import QtQuick 2.15

QtObject {
    property color background: "#121212"
    property color surface: "#1E1E1E"
    property color surfaceLight: "#2C2C2C"
    property color textPrimary: "#FFFFFF"
    property color textSecondary: "#AAAAAA"
    property color accent: "#BB86FC"  // Default purple accent
    property color accentVariant: "#3700B3"
    property color error: "#CF6679"
    
    property int sidebarWidth: 250
    property int headerHeight: 60
    
    property font headerFont: Qt.font({family: "Roboto", pointSize: 18, weight: Font.Bold})
    property font bodyFont: Qt.font({family: "Roboto", pointSize: 11})
}
