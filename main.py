import sys
import os
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl
from backend.bridge import BackendBridge

def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    # Create the bridge
    bridge = BackendBridge()
    
    # Expose bridge to QML context
    engine.rootContext().setContextProperty("bridge", bridge)

    # Load main QML file
    # When installed, UI files are in /usr/share/umc/ui/
    ui_dir = os.path.join(os.path.dirname(__file__), "../share/umc/ui")
    if not os.path.exists(ui_dir):
        # Fallback for development
        ui_dir = os.path.join(os.path.dirname(__file__), "ui")
    
    qml_file = os.path.join(ui_dir, "main.qml")
    engine.load(QUrl.fromLocalFile(qml_file))

    if not engine.rootObjects():
        sys.exit(-1)

    ret = app.exec()
    bridge.cleanup()
    sys.exit(ret)

if __name__ == "__main__":
    main()
