from PySide6.QtCore import QObject, Slot, Signal, Property, QTimer, QThread, QSettings
from .worker import ADBWorker
from .scrcpy_handler import ScrcpyHandler
from .profiles import get_profile_names, get_profile_flags
import json
import os

class BackendBridge(QObject):
    # Signals
    devicesChanged = Signal(list, arguments=['devices'])
    packagesChanged = Signal(list, arguments=['packages'])
    iconReady = Signal(str, str, arguments=['pkg', 'iconPath'])  # pkg, iconPath
    deviceStatusChanged = Signal(str, dict, arguments=['serial', 'status'])  # serial, status_info
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
    requestIcon = Signal(str, str)  # serial, package_name
    requestDeviceStatus = Signal(str)  # serial

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
        
        # Device status cache
        self._device_status = {}  # serial -> status_info
        
        # Device naming and groups
        self._settings = QSettings("UMC", "DeviceManager")
        self._device_names = self._load_device_names()
        self._device_groups = self._load_device_groups()
        
        # Setup Worker Thread
        self._thread = QThread()
        self._worker = ADBWorker()
        self._worker.moveToThread(self._thread)
        
        # Connect Signals
        self.requestDevices.connect(self._worker.fetch_devices)
        self.requestPackages.connect(self._worker.fetch_packages)
        self.requestToggleScreen.connect(self._worker.toggle_device_screen)
        self.requestScrcpyShortcut.connect(self._worker.send_scrcpy_shortcut)
        self.requestIcon.connect(self._worker.fetch_icon)
        self.requestDeviceStatus.connect(self._worker.fetch_device_status)
        
        self._worker.devicesReady.connect(self._on_devices_ready)
        self._worker.packagesReady.connect(self._on_packages_ready)
        self._worker.iconReady.connect(self._on_icon_ready)
        self._worker.deviceStatusReady.connect(self._on_device_status_ready)
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
        # Add custom names and request status for each device
        for device in devices:
            serial = device.get("serial", "")
            # Add custom name if exists
            if serial in self._device_names:
                device["custom_name"] = self._device_names[serial]
            # Request device status
            if serial:
                self.requestDeviceStatus.emit(serial)
        
        if devices != self._devices:
            self._devices = devices
            self.devicesChanged.emit(self._devices)
    
    @Slot(str, dict)
    def _on_device_status_ready(self, serial, status_info):
        """Handle device status update."""
        self._device_status[serial] = status_info
        self.deviceStatusChanged.emit(serial, status_info)

    @Slot(str, list)
    def _on_packages_ready(self, serial, packages):
        if serial == self._current_device_serial:
            self._packages = packages
            self.packagesChanged.emit(packages)

    @Slot(str)
    def _on_worker_error(self, message):
        self.statusMessage.emit(f"Error: {message}")
    
    @Slot(str, str)
    def _on_icon_ready(self, package_name, icon_path):
        """Update icon for a package in the packages list."""
        for i, app in enumerate(self._packages):
            if app.get("package") == package_name:
                # Update the icon in the list
                updated_app = app.copy()
                updated_app["icon"] = icon_path
                self._packages[i] = updated_app
                # Emit signal to update UI
                self.packagesChanged.emit(self._packages)
                break
    
    @Slot(str)
    def fetch_icon_for_package(self, package_name):
        """Request icon fetch for a specific package (non-blocking)."""
        if self._current_device_serial and package_name:
            # Emit in a way that doesn't block
            self.requestIcon.emit(self._current_device_serial, package_name)
    
    @Slot(str)
    def fetch_label_for_package(self, package_name):
        """Request proper label fetch for a specific package (non-blocking)."""
        if self._current_device_serial and package_name:
            # Could add label fetching in background if needed
            pass

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

    def _get_display_params(self, serial, mode):
        width, height, density = 1280, 800, 160 # Tablet / Default
        
        if mode == "Desktop":
            width, height, density = 1920, 1080, 160
        elif mode == "Phone":
             # This is a synchronous call to the worker object living in another thread.
             w, h, d = self._worker.get_device_info(serial)
             if w and h:
                 width, height, density = w, h, d
             else:
                 # Fallback
                 width, height, density = 1080, 2400, 420
        
        return width, height, density

    @Slot(str)
    def mirror_device(self, serial):
        if not serial:
            return
        self.statusMessage.emit(f"Mirroring {serial}...")
        
        # Use current profile flags
        profile_flags = get_profile_flags(self._current_profile)
        
        success = self._scrcpy.mirror(
            serial,
            forward_audio=self._audio_forwarding,
            turn_screen_off=self._launch_with_screen_off,
            extra_flags=profile_flags
        )
        
        if not success:
            self.statusMessage.emit("Failed to start mirror")

    @Slot(str, str)
    def open_display(self, serial, mode):
        if not serial:
            return
        self.statusMessage.emit(f"Opening new {mode} display for {serial}...")
        
        width, height, density = self._get_display_params(serial, mode)
        profile_flags = get_profile_flags(self._current_profile)
        
        success = self._scrcpy.create_display(
            serial,
            width=width,
            height=height,
            dpi=density,
            forward_audio=self._audio_forwarding,
            turn_screen_off=self._launch_with_screen_off,
            extra_flags=profile_flags
        )
        
        if not success:
            self.statusMessage.emit(f"Failed to create {mode} display")

    @Slot(str)
    def launch_app(self, package_name):
        if not self._current_device_serial:
            self.statusMessage.emit("No device selected")
            return
            
        self.statusMessage.emit(f"Launching {package_name} with profile {self._current_profile}...")
        
        width, height, density = self._get_display_params(self._current_device_serial, self._launch_mode)
            
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

    def _load_device_names(self) -> dict:
        """Load device names from settings."""
        names_json = self._settings.value("device_names", "{}")
        try:
            return json.loads(names_json) if names_json else {}
        except:
            return {}
    
    def _save_device_names(self):
        """Save device names to settings."""
        self._settings.setValue("device_names", json.dumps(self._device_names))
    
    def _load_device_groups(self) -> dict:
        """Load device groups from settings."""
        groups_json = self._settings.value("device_groups", "{}")
        try:
            return json.loads(groups_json) if groups_json else {}
        except:
            return {}
    
    def _save_device_groups(self):
        """Save device groups to settings."""
        self._settings.setValue("device_groups", json.dumps(self._device_groups))
    
    @Slot(str, str)
    def set_device_name(self, serial: str, name: str):
        """Set custom name for a device."""
        if serial:
            self._device_names[serial] = name
            self._save_device_names()
            # Update devices list
            for device in self._devices:
                if device.get("serial") == serial:
                    device["custom_name"] = name
            self.devicesChanged.emit(self._devices)
    
    @Slot(str)
    def get_device_name(self, serial: str) -> str:
        """Get custom name for a device, or return empty string."""
        return self._device_names.get(serial, "")
    
    @Slot(str, str)
    def add_device_to_group(self, serial: str, group_name: str):
        """Add device to a group."""
        if serial and group_name:
            if group_name not in self._device_groups:
                self._device_groups[group_name] = []
            if serial not in self._device_groups[group_name]:
                self._device_groups[group_name].append(serial)
                self._save_device_groups()
    
    @Slot(str, str)
    def remove_device_from_group(self, serial: str, group_name: str):
        """Remove device from a group."""
        if group_name in self._device_groups and serial in self._device_groups[group_name]:
            self._device_groups[group_name].remove(serial)
            if not self._device_groups[group_name]:
                del self._device_groups[group_name]
            self._save_device_groups()
    
    def get_device_groups(self) -> dict:
        """Get all device groups."""
        return self._device_groups.copy()
    
    def get_devices_in_group(self, group_name: str) -> list:
        """Get list of device serials in a group."""
        return self._device_groups.get(group_name, []).copy()
    
    @Slot(str, result=dict)
    def get_device_status(self, serial: str) -> dict:
        """Get cached device status."""
        status = self._device_status.get(serial, {})
        # Ensure all values are properly typed for QML
        result = {}
        if status:
            if "battery_level" in status and status["battery_level"] is not None:
                result["battery_level"] = status["battery_level"]
            if "battery_status" in status and status["battery_status"]:
                result["battery_status"] = status["battery_status"]
            if "temperature" in status and status["temperature"] is not None:
                result["temperature"] = status["temperature"]
            if "storage" in status and status["storage"]:
                result["storage"] = status["storage"]
            if "network_type" in status and status["network_type"]:
                result["network_type"] = status["network_type"]
        return result
    
    @Slot(str, "QVariantList")
    def launch_app_on_multiple_devices(self, package_name: str, device_serials):
        """Launch an app on multiple devices simultaneously."""
        if not package_name or not device_serials:
            return
        
        # Convert QVariantList to Python list
        serials_list = []
        for item in device_serials:
            if item:
                serials_list.append(str(item))
        
        if not serials_list:
            return
        
        for serial in serials_list:
            if serial:
                width, height, density = self._get_display_params(serial, self._launch_mode)
                profile_flags = get_profile_flags(self._current_profile)
                
                self._scrcpy.launch_app(
                    serial,
                    package_name,
                    width=width,
                    height=height,
                    dpi=density,
                    turn_screen_off=self._launch_with_screen_off,
                    forward_audio=self._audio_forwarding,
                    extra_flags=profile_flags
                )
        
        self.statusMessage.emit(f"Launched {package_name} on {len(serials_list)} device(s)")
    
    def cleanup(self):
        """Stops the worker thread gracefully."""
        # Stop worker operations immediately
        if self._worker:
            self._worker.stop()
        
        # Stop timer
        if self._timer:
            self._timer.stop()
        
        # Quit thread and wait with timeout
        if self._thread.isRunning():
            self._thread.quit()
            # Wait max 1 second for thread to finish
            if not self._thread.wait(1000):
                # Force terminate if it doesn't stop
                self._thread.terminate()
                self._thread.wait(500)