import QtQuick 2.15

Item {
    id: root
    property string name: "circle"
    property color color: "white"
    property real size: 24

    width: size
    height: size

    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true
        
        onPaint: {
            var ctx = getContext("2d");
            ctx.reset();
            ctx.fillStyle = root.color;
            ctx.strokeStyle = root.color;
            ctx.lineWidth = 2;
            ctx.lineJoin = "round";
            ctx.lineCap = "round";

            var w = width;
            var h = height;
            var cx = w / 2;
            var cy = h / 2;
            var p = 4; // padding

            if (root.name === "refresh") {
                ctx.beginPath();
                ctx.arc(cx, cy, w/2 - p, 0, Math.PI * 1.5);
                ctx.stroke();
                // Arrow head
                ctx.beginPath();
                ctx.moveTo(cx, p);
                ctx.lineTo(cx + 4, p - 4);
                ctx.lineTo(cx + 4, p + 4);
                ctx.fill();
            }
            else if (root.name === "power") {
                // Circle
                ctx.beginPath();
                ctx.arc(cx, cy, w/2 - p, -Math.PI * 0.4, Math.PI * 1.4);
                ctx.stroke();
                // Line
                ctx.beginPath();
                ctx.moveTo(cx, p);
                ctx.lineTo(cx, cy);
                ctx.stroke();
            }
            else if (root.name === "screen_off") {
                // Monitor with slash or Moon
                // Simple Moon shape
                ctx.beginPath();
                ctx.arc(cx, cy, w/2 - p, 0, Math.PI * 2);
                ctx.stroke();
                // Fill half
                ctx.beginPath();
                ctx.arc(cx - 2, cy - 2, w/2 - p, 0, Math.PI * 2);
                ctx.globalCompositeOperation = "destination-out";
                ctx.fill();
                ctx.globalCompositeOperation = "source-over";
            }
            else if (root.name === "device_phone") {
                // Phone rect
                // roundRect replacement: roundedRect(x, y, w, h, r)
                var x = p, y = p, w_rect = w - 2*p, h_rect = h - 2*p, r = 2;
                ctx.beginPath();
                ctx.moveTo(x + r, y);
                ctx.lineTo(x + w_rect - r, y);
                ctx.arcTo(x + w_rect, y, x + w_rect, y + r, r);
                ctx.lineTo(x + w_rect, y + h_rect - r);
                ctx.arcTo(x + w_rect, y + h_rect, x + w_rect - r, y + h_rect, r);
                ctx.lineTo(x + r, y + h_rect);
                ctx.arcTo(x, y + h_rect, x, y + h_rect - r, r);
                ctx.lineTo(x, y + r);
                ctx.arcTo(x, y, x + r, y, r);
                ctx.closePath();
                ctx.stroke();
                
                // Home button line
                ctx.beginPath();
                ctx.moveTo(cx - 2, h - p - 3);
                ctx.lineTo(cx + 2, h - p - 3);
                ctx.stroke();
            }
            else if (root.name === "device_tablet") {
                // Tablet rect (landscape-ish)
                var x = 2, y = 6, w_rect = w - 4, h_rect = h - 12, r = 2;
                ctx.beginPath();
                ctx.moveTo(x + r, y);
                ctx.lineTo(x + w_rect - r, y);
                ctx.arcTo(x + w_rect, y, x + w_rect, y + r, r);
                ctx.lineTo(x + w_rect, y + h_rect - r);
                ctx.arcTo(x + w_rect, y + h_rect, x + w_rect - r, y + h_rect, r);
                ctx.lineTo(x + r, y + h_rect);
                ctx.arcTo(x, y + h_rect, x, y + h_rect - r, r);
                ctx.lineTo(x, y + r);
                ctx.arcTo(x, y, x + r, y, r);
                ctx.closePath();
                ctx.stroke();
            }
            else if (root.name === "search") {
                ctx.beginPath();
                ctx.arc(cx - 2, cy - 2, 6, 0, Math.PI * 2);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(cx + 3, cy + 3);
                ctx.lineTo(w - p, h - p);
                ctx.stroke();
            }
            else if (root.name === "menu") {
                ctx.beginPath();
                ctx.moveTo(p, cy - 4);
                ctx.lineTo(w - p, cy - 4);
                ctx.moveTo(p, cy);
                ctx.lineTo(w - p, cy);
                ctx.moveTo(p, cy + 4);
                ctx.lineTo(w - p, cy + 4);
                ctx.stroke();
            }
            else if (root.name === "save") {
                var x = p, y = p, rw = w - 2*p, rh = h - 2*p;
                ctx.beginPath();
                ctx.rect(x, y, rw, rh);
                ctx.stroke();
                ctx.fillStyle = root.color;
                ctx.fillRect(x + 2, y, rw - 4, 4);
                ctx.fillRect(x + 4, y + rh - 6, rw - 8, 6);
            }
            else if (root.name === "play") {
                ctx.beginPath();
                ctx.moveTo(p, p);
                ctx.lineTo(p, h - p);
                ctx.lineTo(w - p, h / 2);
                ctx.closePath();
                ctx.fill();
            }
            else if (root.name === "delete") {
                ctx.beginPath();
                ctx.moveTo(p, p);
                ctx.lineTo(w - p, h - p);
                ctx.moveTo(w - p, p);
                ctx.lineTo(p, h - p);
                ctx.stroke();
            }
            else if (root.name === "check") {
                ctx.beginPath();
                ctx.moveTo(p, cy);
                ctx.lineTo(cx, h - p);
                ctx.lineTo(w - p, p);
                ctx.stroke();
            }
            else if (root.name === "desktop") {
                // Monitor
                var x = p, y = p+2, rw = w - 2*p, rh = h - 2*p - 4;
                ctx.beginPath();
                ctx.rect(x, y, rw, rh);
                ctx.stroke();
                // Stand
                ctx.beginPath();
                ctx.moveTo(cx, y + rh);
                ctx.lineTo(cx, h - p);
                ctx.moveTo(cx - 4, h - p);
                ctx.lineTo(cx + 4, h - p);
                ctx.stroke();
            }
            else if (root.name === "open_in_new") {
                // Box
                var x = p, y = p+3, rw = w - 2*p - 3, rh = h - 2*p - 3;
                ctx.beginPath();
                ctx.moveTo(x + rw, y);
                ctx.lineTo(x, y);
                ctx.lineTo(x, y + rh);
                ctx.lineTo(x + rw, y + rh);
                ctx.lineTo(x + rw, y + rh/2); // Gap for arrow
                ctx.stroke();
                
                // Arrow
                ctx.beginPath();
                ctx.moveTo(cx + 2, cy - 2);
                ctx.lineTo(w - p + 1, p - 1); // Diagonal
                ctx.stroke();
                // Arrow head
                ctx.beginPath();
                ctx.moveTo(w - p + 1, p - 1);
                ctx.lineTo(w - p + 1 - 4, p - 1);
                ctx.moveTo(w - p + 1, p - 1);
                ctx.lineTo(w - p + 1, p - 1 + 4);
                ctx.stroke();
            }
        }
    }
    
    onNameChanged: canvas.requestPaint()
    onColorChanged: canvas.requestPaint()
}
