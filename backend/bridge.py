from PySide6.QtCore import QObject, Slot, Signal, Property, QTimer, QThread
from .worker import ADBWorker
from .scrcpy_handler import ScrcpyHandler

class BackendBridge(QObject):
    # Signals
    devicesChanged = Signal(list, arguments=['devices'])
    packagesChanged = Signal(list, arguments=['packages'])
    statusMessage = Signal(str, arguments=['message'])
    launchModeChanged = Signal(str, arguments=['mode'])
    
    # Internal Signals to trigger worker
    requestDevices = Signal()
    requestPackages = Signal(str)

    def __init__(self):
        super().__init__()
        self._scrcpy = ScrcpyHandler()
        self._current_device_serial = ""
        self._devices = []
        self._packages = []
        self._launch_mode = "Tablet" # Default
        
        # Setup Worker Thread
        self._thread = QThread()
        self._worker = ADBWorker()
        self._worker.moveToThread(self._thread)
        
        # Connect Signals
        self.requestDevices.connect(self._worker.fetch_devices)
        self.requestPackages.connect(self._worker.fetch_packages)
        
        self._worker.devicesReady.connect(self._on_devices_ready)
        self._worker.packagesReady.connect(self._on_packages_ready)
        self._worker.errorOccurred.connect(self._on_worker_error)
        
        self._thread.start()
        
        # Auto-refresh devices every 3 seconds
        self._timer = QTimer()
        self._timer.timeout.connect(self.requestDevices.emit)
        self._timer.start(3000)
        
        # Initial fetch
        self.requestDevices.emit()

    def get_devices(self):
        return self._devices

    def get_packages(self):
        return self._packages

    def get_launch_mode(self):
        return self._launch_mode

    def get_current_device_serial(self):
        return self._current_device_serial

    def set_launch_mode(self, mode):
        if self._launch_mode != mode:
            self._launch_mode = mode
            self.launchModeChanged.emit(mode)

    devices = Property(list, fget=get_devices, notify=devicesChanged)
    packages = Property(list, fget=get_packages, notify=packagesChanged)
    launchMode = Property(str, fget=get_launch_mode, fset=set_launch_mode, notify=launchModeChanged)
    currentDeviceSerial = Property(str, fget=get_current_device_serial, notify=statusMessage) # statusMessage is emitted when selected, good enough for now or I can add a dedicated signal.

    @Slot()
    def refresh_devices(self):
        # Manual refresh trigger
        self.requestDevices.emit()

    @Slot(list)
    def _on_devices_ready(self, devices):
        if devices != self._devices:
            self._devices = devices
            self.devicesChanged.emit(self._devices)

    @Slot(str, list)
    def _on_packages_ready(self, serial, packages):
        if serial == self._current_device_serial:
            self._packages = packages
            self.packagesChanged.emit(packages)

    @Slot(str)
    def _on_worker_error(self, message):
        self.statusMessage.emit(f"Error: {message}")

    @Slot(str)
    def select_device(self, serial):
        self._current_device_serial = serial
        self.statusMessage.emit(f"Selected: {serial}")
        # Clear packages immediately to indicate loading
        self._packages = []
        self.packagesChanged.emit([])
        self.requestPackages.emit(serial)

    @Slot(str)
    def launch_app(self, package_name):
        if not self._current_device_serial:
            self.statusMessage.emit("No device selected")
            return
            
        self.statusMessage.emit(f"Launching {package_name}...")
        
        # Use worker helper to get info (could be made async too, but fast enough usually)
        # Note: We are accessing worker method directly here. 
        # In strict thread safety, we should emit a signal or use QMetaObject.invokeMethod,
        # but since get_device_info is purely read-only/subprocess, it's generally safe 
        # provided it doesn't modify worker state.
        # Ideally: Refactor this to be fully async too.
        
        width, height, density = 1280, 800, 160 # Tablet Defaults

        if self._launch_mode == "Phone":
             # This is a synchronous call to the worker object living in another thread.
             # Python handles this, but it blocks the main thread slightly. 
             # For now, it's acceptable for the "Launch" action.
            w, h, d = self._worker.get_device_info(self._current_device_serial)
            width, height, density = w, h, d
        
        success = self._scrcpy.launch_app(
            self._current_device_serial, 
            package_name,
            width=width,
            height=height,
            dpi=density
        )
        
        if success:
            self.statusMessage.emit(f"Launched {package_name}")
        else:
            self.statusMessage.emit("Failed to launch scrcpy")
