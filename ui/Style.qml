pragma Singleton
import QtQuick 2.15

QtObject {
    // Color Palette (Professional Dark Theme)
    property color background: "#1E1E1E"    // VSCode-like dark background
    property color surface: "#252526"       // Slightly lighter surface
    property color surfaceLight: "#333333"  // Hover/Input fields
    property color surfaceHighlight: "#37373D" // Selection highlight
    
    property color textPrimary: "#CCCCCC"   // Softer white for main text
    property color textSecondary: "#969696" // Muted gray for subtitles
    property color textDisabled: "#5A5A5A"
    
    // Professional Accent (Muted Blue/Azure)
    property color accent: "#007ACC"        // Standard "Tech Blue"
    property color accentVariant: "#005F9E" // Darker shade
    property color accentSecondary: "#4EC9B0" // Teal for specific highlights
    
    property color error: "#F48771"         // Soft Red
    property color success: "#89D185"       // Soft Green
    property color warning: "#CCA700"       // Soft Yellow
    
    property color divider: "#3E3E42"

    // Layout
    property int sidebarWidth: 280
    property int headerHeight: 60
    property int cornerRadius: 4            // Sharper corners look more "tool-like"
    property int spacingSmall: 8
    property int spacingMedium: 16
    property int spacingLarge: 24
    
    // Typography
    property font headerFont: Qt.font({family: "Segoe UI", pointSize: 16, weight: Font.DemiBold})
    property font subHeaderFont: Qt.font({family: "Segoe UI", pointSize: 13, weight: Font.Medium})
    property font bodyFont: Qt.font({family: "Segoe UI", pointSize: 11})
    property font bodySmallFont: Qt.font({family: "Segoe UI", pointSize: 10})
    property font iconFont: Qt.font({family: "Segoe UI Emoji", pointSize: 14}) 
    
    // Animation
    property int animDurationShort: 100
    property int animDurationNormal: 200
}
