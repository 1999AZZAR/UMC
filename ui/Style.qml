pragma Singleton
import QtQuick 2.15

QtObject {
    // Color Palette (Dark Theme)
    property color background: "#121212"
    property color surface: "#1E1E1E"
    property color surfaceLight: "#2C2C2C"
    property color surfaceHighlight: "#383838"
    
    property color textPrimary: "#E0E0E0"
    property color textSecondary: "#A0A0A0"
    property color textDisabled: "#606060"
    
    property color accent: "#BB86FC"
    property color accentVariant: "#3700B3"
    property color accentSecondary: "#03DAC6"
    
    property color error: "#CF6679"
    property color success: "#00C853"
    
    property color divider: "#2C2C2C"

    // Layout
    property int sidebarWidth: 260
    property int headerHeight: 64
    property int cornerRadius: 12
    property int spacingSmall: 8
    property int spacingMedium: 16
    property int spacingLarge: 24
    
    // Typography
    property font headerFont: Qt.font({family: "Roboto", pointSize: 20, weight: Font.Bold})
    property font subHeaderFont: Qt.font({family: "Roboto", pointSize: 14, weight: Font.DemiBold})
    property font bodyFont: Qt.font({family: "Roboto", pointSize: 11})
    property font bodySmallFont: Qt.font({family: "Roboto", pointSize: 10})
    property font iconFont: Qt.font({family: "Font Awesome 5 Free", pointSize: 16}) // Placeholder for if we had an icon font
    
    // Animation
    property int animDurationShort: 100
    property int animDurationNormal: 250
}
