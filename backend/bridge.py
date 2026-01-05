from PySide6.QtCore import QObject, Slot, Signal, Property, QTimer, QThread, QSettings, QMimeData, QUrl, Qt
from PySide6.QtGui import QGuiApplication, QClipboard
from PySide6.QtWidgets import QFileDialog
from .worker import ADBWorker
from .scrcpy_handler import ScrcpyHandler
from .adb_handler import ADBHandler
from .profiles import get_profile_names, get_profile_flags
import json
import os
import subprocess

class BackendBridge(QObject):
    # Signals
    devicesChanged = Signal(list, arguments=['devices'])
    packagesChanged = Signal(list, arguments=['packages'])
    iconReady = Signal(str, str, arguments=['pkg', 'iconPath'])  # pkg, iconPath
    deviceStatusChanged = Signal(str, dict, arguments=['serial', 'status'])  # serial, status_info
    fileTransferProgress = Signal(str, str, int, arguments=['serial', 'operation', 'progress'])
    fileTransferComplete = Signal(str, str, bool, arguments=['serial', 'operation', 'success'])
    clipboardChanged = Signal(str, str, arguments=['serial', 'text'])
    fileSelected = Signal(str, arguments=['filePath'])
    screenshotReady = Signal(str, str, arguments=['serial', 'screenshotPath'])
    deviceControlChanged = Signal(str, str, arguments=['serial', 'controlType'])
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
    requestIcon = Signal(str, str)  # serial, package_name
    requestDeviceStatus = Signal(str)  # serial
    requestPushFile = Signal(str, str, str)  # serial, local_path, remote_path
    requestPullFile = Signal(str, str, str)  # serial, remote_path, local_path
    requestScreenshot = Signal(str)  # serial
    requestSetVolume = Signal(str, str, int)  # serial, stream, level
    requestSetBrightness = Signal(str, int)  # serial, level
    requestSetRotationLock = Signal(str, bool)  # serial, locked
    requestSetAirplaneMode = Signal(str, bool)  # serial, enabled
    requestSetWifi = Signal(str, bool)  # serial, enabled
    requestSetBluetooth = Signal(str, bool)  # serial, enabled

    def __init__(self):
        super().__init__()
        self._scrcpy = ScrcpyHandler()
        self._adb_handler = ADBHandler()  # For synchronous calls from main thread
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
        
        # Clipboard sync settings
        self._clipboard_sync_enabled = {}  # serial -> bool
        self._clipboard_history = []  # List of clipboard entries
        self._max_clipboard_history = 50
        
        # Clipboard monitoring
        app = QGuiApplication.instance()
        if app:
            self._clipboard = app.clipboard()
            self._last_clipboard_text = self._clipboard.text() if self._clipboard else ""
            self._clipboard_timer = QTimer()
            self._clipboard_timer.timeout.connect(self._check_desktop_clipboard)
            self._clipboard_timer.start(500)  # Check every 500ms
        else:
            self._clipboard = None
            self._last_clipboard_text = ""
            self._clipboard_timer = None
        
        # File transfer progress tracking
        self._file_transfer_progress = {}  # (serial, operation) -> progress
        
        # Setup Worker Thread
        self._thread = QThread()
        self._worker = ADBWorker()
        self._worker.moveToThread(self._thread)
        
        # Connect Signals (use QueuedConnection for cross-thread communication)
        self.requestDevices.connect(self._worker.fetch_devices, Qt.ConnectionType.QueuedConnection)
        self.requestPackages.connect(self._worker.fetch_packages, Qt.ConnectionType.QueuedConnection)
        self.requestToggleScreen.connect(self._worker.toggle_device_screen, Qt.ConnectionType.QueuedConnection)
        self.requestIcon.connect(self._worker.fetch_icon, Qt.ConnectionType.QueuedConnection)
        self.requestDeviceStatus.connect(self._worker.fetch_device_status, Qt.ConnectionType.QueuedConnection)
        self.requestScreenshot.connect(self._worker.capture_screenshot, Qt.ConnectionType.QueuedConnection)
        self.requestSetVolume.connect(self._worker.set_volume, Qt.ConnectionType.QueuedConnection)
        self.requestSetBrightness.connect(self._worker.set_brightness, Qt.ConnectionType.QueuedConnection)
        self.requestSetRotationLock.connect(self._worker.set_rotation_lock, Qt.ConnectionType.QueuedConnection)
        self.requestSetAirplaneMode.connect(self._worker.set_airplane_mode, Qt.ConnectionType.QueuedConnection)
        self.requestSetWifi.connect(self._worker.set_wifi_enabled, Qt.ConnectionType.QueuedConnection)
        self.requestSetBluetooth.connect(self._worker.set_bluetooth_enabled, Qt.ConnectionType.QueuedConnection)
        
        self._worker.devicesReady.connect(self._on_devices_ready)
        self._worker.packagesReady.connect(self._on_packages_ready)
        self._worker.iconReady.connect(self._on_icon_ready)
        self._worker.deviceStatusReady.connect(self._on_device_status_ready)
        self._worker.fileTransferProgress.connect(self._on_file_transfer_progress)
        self._worker.fileTransferComplete.connect(self._on_file_transfer_complete)
        self._worker.clipboardChanged.connect(self._on_device_clipboard_changed)
        self._worker.screenshotReady.connect(self._on_screenshot_ready)
        self._worker.deviceControlChanged.connect(self._on_device_control_changed)
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
        try:
            # Manual refresh trigger
            self.requestDevices.emit()
        except Exception:
            pass

    @Slot(list)
    def _on_devices_ready(self, devices):
        try:
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
        except Exception:
            pass
    
    @Slot(str, dict)
    def _on_device_status_ready(self, serial, status_info):
        """Handle device status update."""
        try:
            self._device_status[serial] = status_info
            self.deviceStatusChanged.emit(serial, status_info)
            
            # Check clipboard if sync is enabled
            if self._clipboard_sync_enabled.get(serial, False):
                self._worker.get_clipboard(serial)
        except Exception:
            pass

    @Slot(str, list)
    def _on_packages_ready(self, serial, packages):
        try:
            if serial == self._current_device_serial:
                self._packages = packages
                self.packagesChanged.emit(packages)
        except Exception:
            pass

    @Slot(str)
    def _on_worker_error(self, message):
        try:
            self.statusMessage.emit(f"Error: {message}")
        except Exception:
            pass
    
    @Slot(str, str)
    def _on_icon_ready(self, package_name, icon_path):
        """Update icon for a package in the packages list."""
        try:
            for i, app in enumerate(self._packages):
                if app.get("package") == package_name:
                    # Update the icon in the list
                    updated_app = app.copy()
                    updated_app["icon"] = icon_path
                    self._packages[i] = updated_app
                    # Emit signal to update UI
                    self.packagesChanged.emit(self._packages)
                    break
        except Exception:
            pass
    
    @Slot(str, str, int)
    def _on_file_transfer_progress(self, serial, operation, progress):
        """Handle file transfer progress update."""
        try:
            self._file_transfer_progress[(serial, operation)] = progress
            self.fileTransferProgress.emit(serial, operation, progress)
        except Exception:
            pass
    
    @Slot(str, str, bool)
    def _on_file_transfer_complete(self, serial, operation, success):
        """Handle file transfer completion."""
        try:
            if (serial, operation) in self._file_transfer_progress:
                del self._file_transfer_progress[(serial, operation)]
            
            self.fileTransferComplete.emit(serial, operation, success)
            if success:
                self.statusMessage.emit(f"File {operation} completed for {serial}")
            else:
                self.statusMessage.emit(f"File {operation} failed for {serial}")
        except Exception:
            pass
    
    @Slot(str, str)
    def _on_device_clipboard_changed(self, serial, text):
        """Handle clipboard change from device."""
        try:
            if self._clipboard_sync_enabled.get(serial, False) and self._clipboard and text:
                # Update desktop clipboard
                self._clipboard.setText(text)
                self._last_clipboard_text = text
                # Add to history
                self._add_to_clipboard_history(text)
        except Exception:
            pass  # Silently handle clipboard errors
    
    @Slot(str, str)
    def _on_screenshot_ready(self, serial, screenshot_path):
        """Handle screenshot capture completion."""
        try:
            self.screenshotReady.emit(serial, screenshot_path)
            self.statusMessage.emit(f"Screenshot saved: {os.path.basename(screenshot_path)}")
        except Exception:
            pass
    
    @Slot(str, str)
    def _on_device_control_changed(self, serial, control_type):
        """Handle device control change."""
        try:
            self.deviceControlChanged.emit(serial, control_type)
        except Exception:
            pass
    
    def _check_desktop_clipboard(self):
        """Check for desktop clipboard changes and sync to devices."""
        try:
            if not self._clipboard:
                return
            
            try:
                current_text = self._clipboard.text()
            except (AttributeError, RuntimeError):
                # Clipboard may not be available
                return
            
            if current_text and current_text != self._last_clipboard_text:
                self._last_clipboard_text = current_text
                # Sync to all devices with clipboard sync enabled
                for serial, enabled in list(self._clipboard_sync_enabled.items()):
                    if enabled and serial:
                        try:
                            self._worker.set_clipboard(serial, current_text)
                        except Exception:
                            pass  # Silently fail per device
                # Add to history
                try:
                    self._add_to_clipboard_history(current_text)
                except Exception:
                    pass
        except Exception:
            # Silently handle all clipboard access errors
            pass
    
    def _add_to_clipboard_history(self, text: str):
        """Add text to clipboard history."""
        try:
            if text and text not in self._clipboard_history:
                self._clipboard_history.insert(0, text)
                # Limit history size
                if len(self._clipboard_history) > self._max_clipboard_history:
                    self._clipboard_history = self._clipboard_history[:self._max_clipboard_history]
        except Exception:
            pass  # Silently handle history errors
    
    @Slot(str, str)
    @Slot(str, str, str)
    def push_file_to_device(self, serial: str, local_path: str, remote_path: str = ""):
        """Push file to device."""
        try:
            if not serial or not local_path:
                return
            
            if not remote_path:
                # Default to /sdcard/Download/
                filename = os.path.basename(local_path)
                remote_path = f"/sdcard/Download/{filename}"
            
            self.statusMessage.emit(f"Pushing {os.path.basename(local_path)} to {serial}...")
            self.requestPushFile.emit(serial, local_path, remote_path)
        except Exception:
            pass
    
    @Slot(str, str, str)
    def pull_file_from_device(self, serial: str, remote_path: str, local_path: str):
        """Pull file from device."""
        try:
            if not serial or not remote_path or not local_path:
                return
            
            self.statusMessage.emit(f"Pulling {os.path.basename(remote_path)} from {serial}...")
            self.requestPullFile.emit(serial, remote_path, local_path)
        except Exception:
            pass
    
    @Slot(str, bool)
    def set_clipboard_sync(self, serial: str, enabled: bool):
        """Enable/disable clipboard sync for a device."""
        try:
            self._clipboard_sync_enabled[serial] = enabled
            if enabled:
                # Start monitoring device clipboard periodically
                # Create a timer for this device if needed
                # For now, we'll poll on device status updates
                pass
        except Exception:
            pass
    
    @Slot(str, result=bool)
    def get_clipboard_sync(self, serial: str) -> bool:
        """Get clipboard sync status for a device."""
        try:
            return self._clipboard_sync_enabled.get(serial, False)
        except Exception:
            return False
    
    @Slot(result=list)
    def get_clipboard_history(self) -> list:
        """Get clipboard history."""
        try:
            return self._clipboard_history.copy()
        except Exception:
            return []
    
    @Slot(str, result=str)
    def get_file_transfer_progress(self, serial: str, operation: str) -> int:
        """Get file transfer progress (0-100)."""
        try:
            return self._file_transfer_progress.get((serial, operation), 0)
        except Exception:
            return 0
    
    @Slot(str)
    def request_file_selection(self, serial: str):
        """Open file dialog and push selected file to device."""
        try:
            from PySide6.QtWidgets import QFileDialog, QApplication
            
            app = QApplication.instance()
            if not app:
                self.statusMessage.emit("Application not available")
                return
            
            file_path, _ = QFileDialog.getOpenFileName(
                None,
                "Select file to transfer",
                os.path.expanduser("~"),
                "All Files (*)"
            )
            
            if file_path:
                self.push_file_to_device(serial, file_path)
        except Exception as e:
            self.statusMessage.emit(f"File dialog error: {str(e)}")
    
    @Slot(str)
    def fetch_icon_for_package(self, package_name):
        """Request icon fetch for a specific package (non-blocking)."""
        try:
            if self._current_device_serial and package_name:
                # Emit in a way that doesn't block
                self.requestIcon.emit(self._current_device_serial, package_name)
        except Exception:
            pass
    
    @Slot(str)
    def fetch_label_for_package(self, package_name):
        """Request proper label fetch for a specific package (non-blocking)."""
        try:
            if self._current_device_serial and package_name:
                # Could add label fetching in background if needed
                pass
        except Exception:
            pass

    @Slot(str)
    def select_device(self, serial):
        try:
            self._current_device_serial = serial
            self.statusMessage.emit(f"Selected: {serial}")
            # Clear packages immediately to indicate loading
            self._packages = []
            self.packagesChanged.emit([])
            self.requestPackages.emit(serial)
        except Exception:
            pass

    @Slot(str)
    def toggle_screen(self, serial):
        """Toggle device screen power (sleep/wake) using ADB directly."""
        try:
            if not serial:
                print(f"[DEBUG] toggle_screen: No serial provided")
                return
            
            if not self._adb_handler.adb_path:
                self.statusMessage.emit("ADB not found. Please install Android SDK platform-tools.")
                return
            
            print(f"[DEBUG] toggle_screen: Toggling power for {serial}")
            self.statusMessage.emit(f"Toggling Power (Sleep/Wake) for {serial}")
            
            # Call ADB directly from main thread (it's a quick operation)
            import subprocess
            try:
                subprocess.run(
                    [self._adb_handler.adb_path, "-s", serial, "shell", "input", "keyevent", "26"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                print(f"[DEBUG] toggle_screen: Success for {serial}")
                self.statusMessage.emit(f"Power toggled for {serial}")
            except subprocess.TimeoutExpired:
                print(f"[DEBUG] toggle_screen: Timeout for {serial}")
                self.statusMessage.emit(f"Timeout while toggling screen for {serial}")
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
                print(f"[DEBUG] toggle_screen: Error for {serial}: {error_msg}")
                self.statusMessage.emit(f"Failed to toggle screen for {serial}")
            except Exception as e:
                print(f"[DEBUG] toggle_screen: Exception for {serial}: {e}")
                self.statusMessage.emit(f"Error: {str(e)}")
        except Exception as e:
            print(f"[DEBUG] toggle_screen exception: {e}")
            import traceback
            traceback.print_exc()
            self.statusMessage.emit(f"Error: {str(e)}")
    

    def _get_display_params(self, serial, mode):
        width, height, density = 1280, 800, 240 # Tablet / Default (HD+ @ 240 DPI)
        
        if mode == "Desktop":
            width, height, density = 1920, 1080, 240 # Full HD @ 240 DPI
        elif mode == "Phone":
             # Use ADB handler directly to avoid cross-thread calls
             try:
                 w, h = self._adb_handler.get_device_resolution(serial)
                 d = self._adb_handler.get_device_density(serial)
                 if w and h:
                     width, height, density = w, h, d
                 else:
                     # Fallback (HD resolution @ 320 DPI for better quality)
                     width, height, density = 1280, 720, 320
             except Exception:
                 # Fallback (HD resolution @ 320 DPI for better quality)
                 width, height, density = 1280, 720, 320
        
        return width, height, density

    @Slot(str)
    def mirror_device(self, serial):
        try:
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
        except Exception:
            pass

    @Slot(str, str)
    def open_display(self, serial, mode):
        try:
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
        except Exception:
            pass

    @Slot(str)
    def launch_app(self, package_name):
        try:
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
        except Exception:
            pass

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
        try:
            if serial:
                self._device_names[serial] = name
                self._save_device_names()
                # Update devices list
                for device in self._devices:
                    if device.get("serial") == serial:
                        device["custom_name"] = name
                self.devicesChanged.emit(self._devices)
        except Exception:
            pass
    
    @Slot(str)
    def get_device_name(self, serial: str) -> str:
        """Get custom name for a device, or return empty string."""
        try:
            return self._device_names.get(serial, "")
        except Exception:
            return ""
    
    @Slot(str, str)
    def add_device_to_group(self, serial: str, group_name: str):
        """Add device to a group."""
        try:
            if serial and group_name:
                if group_name not in self._device_groups:
                    self._device_groups[group_name] = []
                if serial not in self._device_groups[group_name]:
                    self._device_groups[group_name].append(serial)
                    self._save_device_groups()
        except Exception:
            pass
    
    @Slot(str, str)
    def remove_device_from_group(self, serial: str, group_name: str):
        """Remove device from a group."""
        try:
            if group_name in self._device_groups and serial in self._device_groups[group_name]:
                self._device_groups[group_name].remove(serial)
                if not self._device_groups[group_name]:
                    del self._device_groups[group_name]
                self._save_device_groups()
        except Exception:
            pass
    
    def get_device_groups(self) -> dict:
        """Get all device groups."""
        return self._device_groups.copy()
    
    def get_devices_in_group(self, group_name: str) -> list:
        """Get list of device serials in a group."""
        return self._device_groups.get(group_name, []).copy()
    
    @Slot(str, result=dict)
    def get_device_status(self, serial: str) -> dict:
        """Get cached device status."""
        try:
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
        except Exception:
            return {}
    
    @Slot(str, "QVariantList")
    def launch_app_on_multiple_devices(self, package_name: str, device_serials):
        """Launch an app on multiple devices simultaneously."""
        try:
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
        except Exception:
            pass
    
    @Slot(str)
    def capture_screenshot(self, serial: str):
        """Capture screenshot from device."""
        try:
            if serial:
                self.requestScreenshot.emit(serial)
        except Exception:
            pass
    
    @Slot(str, str, int)
    def set_volume(self, serial: str, stream: str, level: int):
        """Set volume for a stream (music, ring, alarm, etc.)."""
        try:
            if serial and stream and 0 <= level <= 15:
                self.requestSetVolume.emit(serial, stream, level)
        except Exception:
            pass
    
    @Slot(str, str, result=int)
    def get_volume(self, serial: str, stream: str) -> int:
        """Get current volume level for a stream."""
        try:
            if not serial or not stream:
                return 0
            if not self._worker or not hasattr(self._worker, 'adb_handler'):
                return 0
            if not self._worker.adb_handler:
                return 0
            result = self._worker.adb_handler.get_volume(serial, stream)
            return result if result is not None else 0
        except Exception:
            return 0
    
    @Slot(str, int)
    def set_brightness(self, serial: str, level: int):
        """Set screen brightness (0-255)."""
        try:
            if serial and 0 <= level <= 255:
                self.requestSetBrightness.emit(serial, level)
        except Exception:
            pass
    
    @Slot(str, result=int)
    def get_brightness(self, serial: str) -> int:
        """Get current screen brightness."""
        try:
            if not serial:
                return 128
            if not self._worker or not hasattr(self._worker, 'adb_handler'):
                return 128
            if not self._worker.adb_handler:
                return 128
            result = self._worker.adb_handler.get_brightness(serial)
            return result if result is not None else 128
        except Exception:
            return 128
    
    @Slot(str, bool)
    def set_rotation_lock(self, serial: str, locked: bool):
        """Set rotation lock."""
        try:
            if serial:
                self.requestSetRotationLock.emit(serial, locked)
        except Exception:
            pass
    
    @Slot(str, result=bool)
    def get_rotation_lock(self, serial: str) -> bool:
        """Get current rotation lock status."""
        try:
            if not serial:
                return False
            if not self._worker or not hasattr(self._worker, 'adb_handler'):
                return False
            if not self._worker.adb_handler:
                return False
            result = self._worker.adb_handler.get_rotation_lock(serial)
            return result if result is not None else False
        except Exception:
            return False
    
    @Slot(str, bool)
    def set_airplane_mode(self, serial: str, enabled: bool):
        """Set airplane mode."""
        try:
            if serial:
                self.requestSetAirplaneMode.emit(serial, enabled)
        except Exception:
            pass
    
    @Slot(str, result=bool)
    def get_airplane_mode(self, serial: str) -> bool:
        """Get current airplane mode status."""
        try:
            if not serial:
                return False
            if not self._worker or not hasattr(self._worker, 'adb_handler'):
                return False
            if not self._worker.adb_handler:
                return False
            result = self._worker.adb_handler.get_airplane_mode(serial)
            return result if result is not None else False
        except Exception:
            return False
    
    @Slot(str, bool)
    def set_wifi_enabled(self, serial: str, enabled: bool):
        """Enable/disable WiFi."""
        try:
            if serial:
                self.requestSetWifi.emit(serial, enabled)
        except Exception:
            pass
    
    @Slot(str, result=bool)
    def get_wifi_enabled(self, serial: str) -> bool:
        """Get current WiFi status."""
        try:
            if not serial:
                return True
            if not self._worker or not hasattr(self._worker, 'adb_handler'):
                return True
            if not self._worker.adb_handler:
                return True
            result = self._worker.adb_handler.get_wifi_enabled(serial)
            return result if result is not None else True
        except Exception:
            return True
    
    @Slot(str, bool)
    def set_bluetooth_enabled(self, serial: str, enabled: bool):
        """Enable/disable Bluetooth."""
        try:
            if serial:
                self.requestSetBluetooth.emit(serial, enabled)
        except Exception:
            pass
    
    @Slot(str, result=bool)
    def get_bluetooth_enabled(self, serial: str) -> bool:
        """Get current Bluetooth status."""
        try:
            if not serial:
                return False
            if not self._worker or not hasattr(self._worker, 'adb_handler'):
                return False
            if not self._worker.adb_handler:
                return False
            result = self._worker.adb_handler.get_bluetooth_enabled(serial)
            return result if result is not None else False
        except Exception:
            return False
    
    def cleanup(self):
        """Stops the worker thread gracefully."""
        try:
            # Stop clipboard monitoring
            if self._clipboard_timer:
                self._clipboard_timer.stop()
            
            # Stop worker operations immediately
            if self._worker:
                self._worker.stop()
            
            # Stop timer
            if self._timer:
                self._timer.stop()
            
            # Quit thread and wait with timeout
            if self._thread and self._thread.isRunning():
                self._thread.quit()
                # Wait max 1 second for thread to finish
                if not self._thread.wait(1000):
                    # Force terminate if it doesn't stop
                    self._thread.terminate()
                    self._thread.wait(500)
        except Exception:
            pass  # Silently handle cleanup errors