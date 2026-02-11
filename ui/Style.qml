pragma Singleton
import QtQuick 2.15

QtObject {
    // M3 Tonal Palette (Dark Pastel Blue - "Glass Hub" Edition)
    readonly property color background: "#0F1115"
    readonly property color surface: "#1A1C1E"
    readonly property color surfaceLight: "#2A2D35"    // Secondary Container
    readonly property color surfaceHighlight: "#343841" // Tonal Elevation
    
    readonly property color textPrimary: "#E2E2E6"
    readonly property color textSecondary: "#D7E3F7"
    readonly property color textDisabled: "#8E9199"
    
    readonly property color accent: "#D1E4FF"         // Primary Pastel
    readonly property color accentVariant: "#00497D"  // Deep Primary
    readonly property color accentTertiary: "#F7D8FF" // Tertiary Pastel (Pinkish)
    readonly property color accentSuccess: "#B4F1B4"
    
    readonly property color error: "#FFB4AB"
    readonly property color success: "#B4F1B4"
    readonly property color warning: "#EFDB72"
    
    readonly property color divider: "transparent"

    // Layout
    readonly property int sidebarWidth: 320
    readonly property int headerHeight: 80
    readonly property int cornerRadius: 28            // Large rounded corners (M3)
    readonly property int cornerRadiusSmall: 16
    
    // Typography (Plus Jakarta Sans)
    readonly property font headerFont: Qt.font({family: "Plus Jakarta Sans", pointSize: 18, weight: Font.Bold})
    readonly property font subHeaderFont: Qt.font({family: "Plus Jakarta Sans", pointSize: 13, weight: Font.DemiBold})
    readonly property font bodyFont: Qt.font({family: "Plus Jakarta Sans", pointSize: 11})
    readonly property font bodySmallFont: Qt.font({family: "Plus Jakarta Sans", pointSize: 10, weight: Font.Medium})
}
