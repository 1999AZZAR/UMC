pragma Singleton
import QtQuick 2.15

QtObject {
    // M3 Tonal Palette (Dark Pastel Blue)
    property color background: "#1A1C1E"
    property color surface: "#111318"
    property color surfaceLight: "#3E4759"    // Secondary Container
    property color surfaceHighlight: "#43474E" // Surface Variant
    
    property color textPrimary: "#E2E2E6"
    property color textSecondary: "#D7E3F7"   // On Secondary Container
    property color textDisabled: "#8E9199"
    
    property color accent: "#D1E4FF"         // Primary
    property color accentVariant: "#00497D"  // Primary Container
    property color accentSecondary: "#F7D8FF" // Tertiary Pastel
    
    property color error: "#FFB4AB"
    property color success: "#B4F1B4"
    property color warning: "#EFDB72"
    
    property color divider: "transparent"

    // Layout
    property int sidebarWidth: 320           // Slightly wider for M3
    property int headerHeight: 80
    property int cornerRadius: 28            // Large rounded corners for M3
    property int spacingSmall: 8
    property int spacingMedium: 16
    property int spacingLarge: 24
    
    // Typography
    property font headerFont: Qt.font({family: "Plus Jakarta Sans", pointSize: 18, weight: Font.Bold})
    property font subHeaderFont: Qt.font({family: "Plus Jakarta Sans", pointSize: 13, weight: Font.Medium})
    property font bodyFont: Qt.font({family: "Plus Jakarta Sans", pointSize: 11})
    property font bodySmallFont: Qt.font({family: "Plus Jakarta Sans", pointSize: 10})
}
