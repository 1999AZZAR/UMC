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
    Thread-safe communication via Signals/Slots.
    """
    devicesReady = Signal(list)
    packagesReady = Signal(str, list)
    iconReady = Signal(str, str)
    deviceStatusReady = Signal(str, dict)
    fileTransferProgress = Signal(str, str, int)
    fileTransferComplete = Signal(str, str, bool)
    clipboardChanged = Signal(str, str)
    screenshotReady = Signal(str, str)
    deviceControlChanged = Signal(str, str)
    errorOccurred = Signal(str)
    wirelessPairingFinished = Signal(str, bool, str)
    wirelessDisconnectFinished = Signal(str, bool, str)
    tcpipModeFinished = Signal(str, int, bool, str)
    
    def __init__(self):
        super().__init__()
        self.adb_handler = ADBHandler()
        self.adb_path = self.adb_handler.adb_path
        self._should_stop = False
        self._fetching_icons = set() # Track icons currently being fetched
        
        cache_dir = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
        self.icon_cache_dir = os.path.join(cache_dir, "umc", "icons")
        os.makedirs(self.icon_cache_dir, exist_ok=True)
        self.screenshot_dir = os.path.join(cache_dir, "umc", "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)

    @Slot()
    def fetch_devices(self):
        if self._should_stop: return
        devices = self.adb_handler.get_devices()
        self.devicesReady.emit(devices)
    
    @Slot(str)
    def fetch_device_status(self, serial: str):
        if self._should_stop or not serial: return
        status_info = self.adb_handler.get_device_status_info(serial)
        self.deviceStatusReady.emit(serial, status_info)

    @Slot(str)
    def fetch_packages(self, serial: str):
        if self._should_stop or not serial: return
        try:
            # Query activities to find launcher apps
            cmd = [self.adb_path, "-s", serial, "shell", "cmd", "package", "query-activities", "--brief", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
            
            # Fetch labels for all apps in one go or per batch might be slow, 
            # but we can try to guess from the package name first and then refine.
            apps = []
            seen = set()
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if not line or line.startswith("Activity") or "/" not in line: continue
                pkg = line.split("/")[0].strip()
                if pkg not in seen:
                    # Better default label: remove com. prefix and capitalize
                    parts = pkg.split(".")
                    if len(parts) > 2: label = parts[-1].capitalize()
                    elif len(parts) > 1: label = parts[1].capitalize()
                    else: label = pkg.capitalize()
                    
                    if label.lower() == "android":
                        # If it's still "Android", try the previous part
                        if len(parts) > 1: label = parts[-2].capitalize()
                    
                    icon = os.path.join(self.icon_cache_dir, f"{pkg}.png")
                    apps.append({"package": pkg, "name": label, "icon": icon if os.path.exists(icon) else None})
                    seen.add(pkg)
            
            apps.sort(key=lambda x: x["name"].lower())
            self.packagesReady.emit(serial, apps)
        except Exception as e:
            self.errorOccurred.emit(f"Package fetch failed: {e}")

    @Slot(str)
    def toggle_device_screen(self, serial: str):
        if self._should_stop or not serial: return
        try:
            subprocess.run([self.adb_path, "-s", serial, "shell", "input", "keyevent", "26"], timeout=5)
            self.deviceControlChanged.emit(serial, "screen_toggle")
        except: pass

    @Slot(str, str)
    def fetch_icon(self, serial, package_name):
        if self._should_stop or package_name in self._fetching_icons: return
        
        # Check cache first
        cache_file = os.path.join(self.icon_cache_dir, f"{package_name}.png")
        if os.path.exists(cache_file):
            self.iconReady.emit(package_name, cache_file)
            return

        self._fetching_icons.add(package_name)
        try:
            path = self.adb_handler.get_app_icon_path(serial, package_name, self.icon_cache_dir)
            if path and not self._should_stop:
                self.iconReady.emit(package_name, path)
        finally:
            self._fetching_icons.remove(package_name)

    @Slot(str, str, str)
    def push_file(self, serial, local, remote):
        self.fileTransferProgress.emit(serial, "push", 0)
        success = self.adb_handler.push_file(serial, local, remote)
        self.fileTransferComplete.emit(serial, "push", success)

    @Slot(str, str, str)
    def pull_file(self, serial, remote, local):
        self.fileTransferProgress.emit(serial, "pull", 0)
        success = self.adb_handler.pull_file(serial, remote, local)
        self.fileTransferComplete.emit(serial, "pull", success)

    @Slot(str)
    def get_clipboard(self, serial):
        text = self.adb_handler.get_clipboard(serial)
        if text: self.clipboardChanged.emit(serial, text)

    @Slot(str, str)
    def set_clipboard(self, serial, text):
        self.adb_handler.set_clipboard(serial, text)

    @Slot(str)
    def capture_screenshot(self, serial):
        from datetime import datetime
        # Use ISO-like format for sortable and unique filenames
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(self.screenshot_dir, f"screenshot_{serial}_{ts}.png")
        if self.adb_handler.capture_screenshot(serial, path):
            self.screenshotReady.emit(serial, path)

    @Slot(str, str, int)
    def set_volume(self, s, st, l):
        if self.adb_handler.set_volume(s, st, l): self.deviceControlChanged.emit(s, f"volume_{st}")

    @Slot(str, int)
    def set_brightness(self, s, l):
        if self.adb_handler.set_brightness(s, l): self.deviceControlChanged.emit(s, "brightness")

    @Slot(str, bool)
    def set_rotation_lock(self, s, l):
        if self.adb_handler.set_rotation_lock(s, l): self.deviceControlChanged.emit(s, "rotation")

    @Slot(str, bool)
    def set_airplane_mode(self, s, e):
        if self.adb_handler.set_airplane_mode(s, e): self.deviceControlChanged.emit(s, "airplane")

    @Slot(str, bool)
    def set_wifi_enabled(self, s, e):
        if self.adb_handler.set_wifi_enabled(s, e): self.deviceControlChanged.emit(s, "wifi")

    @Slot(str, bool)
    def set_bluetooth_enabled(self, s, e):
        if self.adb_handler.set_bluetooth_enabled(s, e): self.deviceControlChanged.emit(s, "bluetooth")

    @Slot(str)
    def connect_wireless(self, address):
        success, message = self.adb_handler.connect_wireless(address)
        if success: self.fetch_devices()
        else: self.errorOccurred.emit(message)

    @Slot(str, str)
    def pair_wireless(self, address, code):
        success, message = self.adb_handler.pair_device(address, code)
        self.wirelessPairingFinished.emit(address, success, message)

    @Slot(str)
    def disconnect_wireless(self, address):
        success, message = self.adb_handler.disconnect_device(address)
        self.wirelessDisconnectFinished.emit(address, success, message)

    @Slot(str, int)
    def enable_tcpip_mode(self, serial, port):
        success, message = self.adb_handler.enable_tcpip_mode(serial, port)
        self.tcpipModeFinished.emit(serial, port, success, message)

    def stop(self):
        self._should_stop = True
