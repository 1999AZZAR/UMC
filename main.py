import sys
import os
import signal
import logging

# Ensure the current directory is in sys.path for robust imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtCore import QUrl
    from backend.bridge import BackendBridge
except ImportError as e:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logger = logging.getLogger(__name__)
    logger.critical("Critical import error: %s", e)
    logger.critical("Python path: %s", sys.path)
    sys.exit(1)

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # Use QApplication instead of QGuiApplication for file dialogs
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    # Create the bridge
    bridge = BackendBridge()
    app.aboutToQuit.connect(bridge.cleanup)
    
    # Handle SIGINT (Ctrl+C) for quick shutdown
    def signal_handler(sig, frame):
        bridge.cleanup()
        app.quit()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Expose bridge to QML context
    engine.rootContext().setContextProperty("bridge", bridge)

    # Load main QML file
    # Fallback for development/installation paths
    ui_dir = os.path.join(current_dir, "ui")
    if not os.path.exists(ui_dir):
        ui_dir = os.path.join(current_dir, "../share/umc/ui")
    
    qml_file = os.path.join(ui_dir, "main.qml")
    if not os.path.exists(qml_file):
        logger.error("QML file not found at %s", qml_file)
        sys.exit(1)
        
    engine.load(QUrl.fromLocalFile(qml_file))

    if not engine.rootObjects():
        logger.error("Failed to load QML objects")
        sys.exit(-1)

    ret = app.exec()
    sys.exit(ret)

if __name__ == "__main__":
    main()
