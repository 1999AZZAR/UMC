import subprocess
import shutil
import re
import os
from typing import List, Dict, Optional, Tuple
from PySide6.QtCore import QObject, Signal, Slot, QThread, QStandardPaths
from .adb_handler import ADBHandler

class ADBWorker(QObject):
    """
    Worker thread for handling blocking ADB operations.
    """
    devicesReady = Signal(list)
    packagesReady = Signal(str, list)
    iconReady = Signal(str, str)  # package_name, icon_path
    deviceStatusReady = Signal(str, dict)  # serial, status_info
    fileTransferProgress = Signal(str, str, int, arguments=['serial', 'operation', 'progress'])  # serial, operation (push/pull), progress 0-100
    fileTransferComplete = Signal(str, str, bool, arguments=['serial', 'operation', 'success'])  # serial, operation, success
    clipboardChanged = Signal(str, str, arguments=['serial', 'text'])  # serial, clipboard_text
    screenshotReady = Signal(str, str, arguments=['serial', 'screenshotPath'])  # serial, screenshot_path
    deviceControlChanged = Signal(str, str, arguments=['serial', 'controlType'])  # serial, control_type (volume, brightness, etc.)
    errorOccurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.adb_handler = ADBHandler()
        self.adb_path = self.adb_handler.adb_path
        self.mock_mode = self.adb_handler.mock_mode
        self._should_stop = False  # Flag to stop operations quickly
        
        # Set up icon cache directory
        cache_dir = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
        self.icon_cache_dir = os.path.join(cache_dir, "umc", "icons")
        os.makedirs(self.icon_cache_dir, exist_ok=True)
        
        # Set up screenshot directory
        self.screenshot_dir = os.path.join(cache_dir, "umc", "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)

    @Slot()
    def fetch_devices(self):
        """Fetches the list of connected devices."""
        try:
            devices = self.adb_handler.get_devices()
            self.devicesReady.emit(devices)
        except Exception:
            self.devicesReady.emit([])
    
    @Slot(str)
    def fetch_device_status(self, serial: str):
        """Fetches device status information (battery, temperature, storage, etc.)."""
        if not serial or self.mock_mode or serial.startswith("MOCK"):
            return
        
        try:
            status_info = self.adb_handler.get_device_status_info(serial)
            self.deviceStatusReady.emit(serial, status_info)
        except Exception as e:
            # Silently fail - status fetching is optional
            pass

    @Slot(str)
    def fetch_packages(self, serial: str):
        """Fetches all launchable packages (users apps + system apps with launcher activity)."""
        try:
            if self.mock_mode or serial.startswith("MOCK"):
                mock_apps = [
                    {"package": "com.android.chrome", "name": "Chrome", "icon": None},
                    {"package": "com.google.android.youtube", "name": "YouTube", "icon": None},
                    {"package": "com.whatsapp", "name": "WhatsApp", "icon": None},
                    {"package": "com.instagram.android", "name": "Instagram", "icon": None},
                    {"package": "com.android.settings", "name": "Settings", "icon": None}
                ]
                self.packagesReady.emit(serial, mock_apps)
                return

            # Use cmd package query-activities to get all launchable apps
            # This is faster and more accurate than pm list packages
            cmd = [
                self.adb_path, "-s", serial, "shell", 
                "cmd", "package", "query-activities", "--brief", 
                "-a", "android.intent.action.MAIN", 
                "-c", "android.intent.category.LAUNCHER"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            apps = []
            
            seen_packages = set()
            
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if not line or line.startswith("Activity"):
                    continue
                
                # Format is usually: package/activity or package/.Activity
                # e.g., com.android.settings/com.android.settings.Settings
                
                if "/" in line:
                    parts = line.split("/")
                    package_name = parts[0]
                    
                    if package_name not in seen_packages:
                        # Use fast heuristic for app name (don't call pm dump - too slow)
                        # Icons and proper labels can be fetched lazily later
                        app_label = package_name
                        if "." in package_name:
                            # Use the last part of the package name as a heuristic for the name
                            app_label = package_name.split(".")[-1].capitalize()
                        
                        # Only check if icon exists in cache (lazy loading)
                        # Don't fetch icons synchronously - too slow for many apps
                        icon_path = None
                        cache_file = os.path.join(self.icon_cache_dir, f"{package_name}.png")
                        if os.path.exists(cache_file):
                            icon_path = cache_file
                        
                        apps.append({
                            "package": package_name,
                            "name": app_label,
                            "icon": icon_path if icon_path else None
                        })
                        seen_packages.add(package_name)

            apps.sort(key=lambda x: x["name"].lower())
            self.packagesReady.emit(serial, apps)

        except Exception as e:
            self.errorOccurred.emit(f"Failed to fetch packages: {str(e)}")

    @Slot(str)
    def toggle_device_screen(self, serial: str):
        """Toggles the device screen power (KEYCODE_POWER)."""
        if self.mock_mode or serial.startswith("MOCK"):
            print(f"Mock toggling screen for {serial}")
            return

        try:
            # KEYCODE_POWER = 26
            subprocess.run(
                [self.adb_path, "-s", serial, "shell", "input", "keyevent", "26"], 
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception as e:
            self.errorOccurred.emit(f"Failed to toggle screen for {serial}: {str(e)}")

    @Slot(str, str)
    def send_scrcpy_shortcut(self, serial: str, shortcut: str):
        """
        Sends a shortcut to the scrcpy window for the given serial using xdotool.
        shortcut: 'screen_off' (Super+o) or 'screen_on' (Super+Shift+o)
        """
        if self.mock_mode:
            print(f"Mock sending shortcut {shortcut} to {serial}")
            return

        window_name = f"UMC - {serial}"
        key_combo = "Super+o" if shortcut == 'screen_off' else "Super+Shift+o"
        
        try:
            # Check if xdotool exists first (could cache this)
            if not shutil.which("xdotool"):
                self.errorOccurred.emit("xdotool not found. Install it to use this feature.")
                return

            # Search for window and send key
            # xdotool search --name "Title" windowactivate --sync key keys
            cmd = [
                "xdotool", "search", "--name", window_name, 
                "windowactivate", "--sync", 
                "key", key_combo
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
        except subprocess.CalledProcessError:
            self.errorOccurred.emit(f"Could not find window for device {serial}")
        except Exception as e:
            self.errorOccurred.emit(f"Failed to send shortcut: {str(e)}")

    def get_device_info(self, serial: str) -> Tuple[int, int, int]:
        """
        Synchronous helper to get resolution and density.
        """
        width, height = self.adb_handler.get_device_resolution(serial)
        density = self.adb_handler.get_device_density(serial)
        return width, height, density
    
    @Slot(str, str)
    def fetch_icon(self, serial: str, package_name: str):
        """Fetches icon for a specific package in background (non-blocking, optional)."""
        if self._should_stop or self.mock_mode or serial.startswith("MOCK"):
            return
        
        # Check cache first - if exists, return immediately
        cache_file = os.path.join(self.icon_cache_dir, f"{package_name}.png")
        if os.path.exists(cache_file):
            if not self._should_stop:
                self.iconReady.emit(package_name, cache_file)
            return
        
        # Only fetch if not in cache, with shorter timeout to prevent blocking
        try:
            if self._should_stop:
                return
            # Use shorter timeout (3 seconds) to prevent hanging
            icon_path = self.adb_handler.get_app_icon_path(serial, package_name, self.icon_cache_dir, timeout=3)
            if icon_path and not self._should_stop:
                self.iconReady.emit(package_name, icon_path)
        except (subprocess.TimeoutExpired, KeyboardInterrupt, Exception) as e:
            # Silently fail - icon fetching is optional and shouldn't block app list
            pass
    
    @Slot(str, str, str)
    def push_file(self, serial: str, local_path: str, remote_path: str):
        """Push file to device."""
        if self._should_stop or self.mock_mode or serial.startswith("MOCK"):
            return
        
        try:
            self.fileTransferProgress.emit(serial, "push", 0)
            success = self.adb_handler.push_file(serial, local_path, remote_path)
            self.fileTransferProgress.emit(serial, "push", 100)
            self.fileTransferComplete.emit(serial, "push", success)
        except Exception as e:
            self.fileTransferComplete.emit(serial, "push", False)
            self.errorOccurred.emit(f"File transfer failed: {str(e)}")
    
    @Slot(str, str, str)
    def pull_file(self, serial: str, remote_path: str, local_path: str):
        """Pull file from device."""
        if self._should_stop or self.mock_mode or serial.startswith("MOCK"):
            return
        
        try:
            self.fileTransferProgress.emit(serial, "pull", 0)
            success = self.adb_handler.pull_file(serial, remote_path, local_path)
            self.fileTransferProgress.emit(serial, "pull", 100)
            self.fileTransferComplete.emit(serial, "pull", success)
        except Exception as e:
            self.fileTransferComplete.emit(serial, "pull", False)
            self.errorOccurred.emit(f"File transfer failed: {str(e)}")
    
    @Slot(str, str)
    def get_clipboard(self, serial: str):
        """Get clipboard from device."""
        if self._should_stop or self.mock_mode or serial.startswith("MOCK"):
            return
        
        try:
            text = self.adb_handler.get_clipboard(serial)
            if text:
                self.clipboardChanged.emit(serial, text)
        except Exception as e:
            pass  # Silently fail
    
    @Slot(str, str)
    def set_clipboard(self, serial: str, text: str):
        """Set clipboard on device."""
        if self._should_stop or self.mock_mode or serial.startswith("MOCK"):
            return
        
        try:
            self.adb_handler.set_clipboard(serial, text)
        except Exception as e:
            pass  # Silently fail
    
    @Slot(str)
    def capture_screenshot(self, serial: str):
        """Capture screenshot from device."""
        if self._should_stop or self.mock_mode or serial.startswith("MOCK"):
            return
        
        try:
            from datetime import datetime
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{serial}_{timestamp}.png"
            save_path = os.path.join(self.screenshot_dir, filename)
            
            success = self.adb_handler.capture_screenshot(serial, save_path)
            if success:
                self.screenshotReady.emit(serial, save_path)
            else:
                self.errorOccurred.emit(f"Failed to capture screenshot from {serial}")
        except Exception as e:
            self.errorOccurred.emit(f"Screenshot error: {str(e)}")
    
    @Slot(str, str, int)
    def set_volume(self, serial: str, stream: str, level: int):
        """Set volume for a stream."""
        if self._should_stop or self.mock_mode or serial.startswith("MOCK"):
            return
        
        try:
            success = self.adb_handler.set_volume(serial, stream, level)
            if success:
                self.deviceControlChanged.emit(serial, f"volume_{stream}")
            else:
                self.errorOccurred.emit(f"Volume control failed - may require root or special permissions")
        except Exception as e:
            self.errorOccurred.emit(f"Volume control error: {str(e)}")
    
    @Slot(str, int)
    def set_brightness(self, serial: str, level: int):
        """Set screen brightness."""
        if self._should_stop or self.mock_mode or serial.startswith("MOCK"):
            return
        
        try:
            success = self.adb_handler.set_brightness(serial, level)
            if success:
                self.deviceControlChanged.emit(serial, "brightness")
            else:
                self.errorOccurred.emit(f"Brightness control failed - may require root or WRITE_SETTINGS permission")
        except Exception as e:
            self.errorOccurred.emit(f"Brightness control error: {str(e)}")
    
    @Slot(str, bool)
    def set_rotation_lock(self, serial: str, locked: bool):
        """Set rotation lock."""
        if self._should_stop or self.mock_mode or serial.startswith("MOCK"):
            return
        
        try:
            success = self.adb_handler.set_rotation_lock(serial, locked)
            if success:
                self.deviceControlChanged.emit(serial, "rotation")
            else:
                self.errorOccurred.emit(f"Rotation lock failed - may require WRITE_SETTINGS permission")
        except Exception as e:
            self.errorOccurred.emit(f"Rotation lock error: {str(e)}")
    
    @Slot(str, bool)
    def set_airplane_mode(self, serial: str, enabled: bool):
        """Set airplane mode."""
        if self._should_stop or self.mock_mode or serial.startswith("MOCK"):
            return
        
        try:
            success = self.adb_handler.set_airplane_mode(serial, enabled)
            if success:
                self.deviceControlChanged.emit(serial, "airplane_mode")
        except Exception as e:
            self.errorOccurred.emit(f"Airplane mode error: {str(e)}")
    
    @Slot(str, bool)
    def set_wifi_enabled(self, serial: str, enabled: bool):
        """Enable/disable WiFi."""
        if self._should_stop or self.mock_mode or serial.startswith("MOCK"):
            return
        
        try:
            success = self.adb_handler.set_wifi_enabled(serial, enabled)
            if success:
                self.deviceControlChanged.emit(serial, "wifi")
            else:
                self.errorOccurred.emit(f"WiFi control failed - may require root access")
        except Exception as e:
            self.errorOccurred.emit(f"WiFi control error: {str(e)}")
    
    @Slot(str, bool)
    def set_bluetooth_enabled(self, serial: str, enabled: bool):
        """Enable/disable Bluetooth."""
        if self._should_stop or self.mock_mode or serial.startswith("MOCK"):
            return
        
        try:
            success = self.adb_handler.set_bluetooth_enabled(serial, enabled)
            if success:
                self.deviceControlChanged.emit(serial, "bluetooth")
            else:
                self.errorOccurred.emit(f"Bluetooth control failed - may require root access")
        except Exception as e:
            self.errorOccurred.emit(f"Bluetooth control error: {str(e)}")
    
    def stop(self):
        """Stop all operations immediately."""
        self._should_stop = True
