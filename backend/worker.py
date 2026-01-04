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

    @Slot()
    def fetch_devices(self):
        """Fetches the list of connected devices."""
        devices = self.adb_handler.get_devices()
        self.devicesReady.emit(devices)
    
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

        try:
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
    
    def stop(self):
        """Stop all operations immediately."""
        self._should_stop = True
