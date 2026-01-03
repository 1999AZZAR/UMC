from PySide6.QtCore import QObject, Slot, Signal, Property, QTimer, QThread
from .worker import ADBWorker
from .scrcpy_handler import ScrcpyHandler
from .profiles import get_profile_names, get_profile_flags

class BackendBridge(QObject):
    # Signals
    devicesChanged = Signal(list, arguments=['devices'])
    packagesChanged = Signal(list, arguments=['packages'])
    statusMessage = Signal(str, arguments=['message'])
    launchModeChanged = Signal(str, arguments=['mode'])
    launchWithScreenOffChanged = Signal(bool, arguments=['enabled'])
    audioForwardingChanged = Signal(bool, arguments=['enabled'])
    currentProfileChanged = Signal(str, arguments=['profile'])
    profilesChanged = Signal(list, arguments=['profiles'])
    
    # Internal Signals to trigger worker
    requestDevices = Signal()
    requestPackages = Signal(str)
    requestToggleScreen = Signal(str)
    requestScrcpyShortcut = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._scrcpy = ScrcpyHandler()
        self._current_device_serial = ""
        self._devices = []
        self._packages = []
        self._launch_mode = "Tablet" # Default
        self._launch_with_screen_off = False
        self._audio_forwarding = False
        self._current_profile = "Default"
        self._profiles = get_profile_names()
        
        # Setup Worker Thread
        self._thread = QThread()
        self._worker = ADBWorker()
        self._worker.moveToThread(self._thread)
        
        # Connect Signals
        self.requestDevices.connect(self._worker.fetch_devices)
        self.requestPackages.connect(self._worker.fetch_packages)
        self.requestToggleScreen.connect(self._worker.toggle_device_screen)
        self.requestScrcpyShortcut.connect(self._worker.send_scrcpy_shortcut)
        
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
    
    def get_launch_with_screen_off(self):
        return self._launch_with_screen_off

    def get_current_device_serial(self):
        return self._current_device_serial

    def set_launch_mode(self, mode):
        if self._launch_mode != mode:
            self._launch_mode = mode
            self.launchModeChanged.emit(mode)

    def set_launch_with_screen_off(self, enabled):
        if self._launch_with_screen_off != enabled:
            self._launch_with_screen_off = enabled
            self.launchWithScreenOffChanged.emit(enabled)

    def get_audio_forwarding(self):
        return self._audio_forwarding

    def set_audio_forwarding(self, enabled):
        if self._audio_forwarding != enabled:
            self._audio_forwarding = enabled
            self.audioForwardingChanged.emit(enabled)

    def get_current_profile(self):
        return self._current_profile
        
    def set_current_profile(self, profile):
        if self._current_profile != profile and profile in self._profiles:
            self._current_profile = profile
            self.currentProfileChanged.emit(profile)

    def get_profiles(self):
        return self._profiles

    devices = Property(list, fget=get_devices, notify=devicesChanged)
    packages = Property(list, fget=get_packages, notify=packagesChanged)
    launchMode = Property(str, fget=get_launch_mode, fset=set_launch_mode, notify=launchModeChanged)
    launchWithScreenOff = Property(bool, fget=get_launch_with_screen_off, fset=set_launch_with_screen_off, notify=launchWithScreenOffChanged)
    audioForwarding = Property(bool, fget=get_audio_forwarding, fset=set_audio_forwarding, notify=audioForwardingChanged)
    currentProfile = Property(str, fget=get_current_profile, fset=set_current_profile, notify=currentProfileChanged)
    profiles = Property(list, fget=get_profiles, notify=profilesChanged)
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
    def toggle_screen(self, serial):
        if not serial:
            return
        self.statusMessage.emit(f"Toggling Power (Sleep/Wake) for {serial}")
        self.requestToggleScreen.emit(serial)
    
    @Slot(str)
    def toggle_scrcpy_display(self, serial):
        """Sends Super+o (Screen Off) via xdotool to the window"""
        if not serial:
            return
        self.statusMessage.emit(f"Sending Screen Off (Super+o) to {serial}...")
        self.requestScrcpyShortcut.emit(serial, "screen_off")
        
    @Slot(str)
    def turn_scrcpy_display_on(self, serial):
        """Sends Super+Shift+o (Screen On) via xdotool to the window"""
        if not serial:
            return
        self.statusMessage.emit(f"Sending Screen On (Super+Shift+o) to {serial}...")
        self.requestScrcpyShortcut.emit(serial, "screen_on")

    @Slot(str)
    def launch_app(self, package_name):
        if not self._current_device_serial:
            self.statusMessage.emit("No device selected")
            return
            
        self.statusMessage.emit(f"Launching {package_name} with profile {self._current_profile}...")
        
        width, height, density = 1280, 800, 160 # Tablet Defaults

        if self._launch_mode == "Desktop":
            width, height, density = 1920, 1080, 180
        elif self._launch_mode == "Phone":
             # This is a synchronous call to the worker object living in another thread.
             # Python handles this, but it blocks the main thread slightly. 
             # For now, it's acceptable for the "Launch" action.
            w, h, d = self._worker.get_device_info(self._current_device_serial)
            width, height, density = w, h, d
            
        profile_flags = get_profile_flags(self._current_profile)
        
        success = self._scrcpy.launch_app(
            self._current_device_serial, 
            package_name,
            width=width,
            height=height,
            dpi=density,
            turn_screen_off=self._launch_with_screen_off,
            forward_audio=self._audio_forwarding,
            extra_flags=profile_flags
        )
        
        if success:
            self.statusMessage.emit(f"Launched {package_name}")
        else:
            self.statusMessage.emit("Failed to launch scrcpy")

    def cleanup(self):
        """Stops the worker thread gracefully."""
        if self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()