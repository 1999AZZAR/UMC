from PySide6.QtCore import QObject, Slot, Signal, Property, QTimer, QThread, QSettings, QMimeData, QUrl, Qt, QAbstractListModel, QModelIndex
from PySide6.QtGui import QGuiApplication, QClipboard
from PySide6.QtWidgets import QFileDialog
from .worker import ADBWorker
from .scrcpy_handler import ScrcpyHandler
from .adb_handler import ADBHandler
from .profiles import get_profile_names, get_profile_flags
import json
import os
import subprocess

class PackageModel(QAbstractListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    PackageRole = Qt.ItemDataRole.UserRole + 2
    IconRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_packages = []
        self._visible_packages = []
        self._filter_text = ""

    def roleNames(self):
        return {
            self.NameRole: b"name",
            self.PackageRole: b"package",
            self.IconRole: b"icon"
        }

    def rowCount(self, parent=QModelIndex()):
        return len(self._visible_packages)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._visible_packages)):
            return None
        pkg = self._visible_packages[index.row()]
        if role == self.NameRole: return pkg.get("name")
        if role == self.PackageRole: return pkg.get("package")
        if role == self.IconRole: return pkg.get("icon")
        return None

    def setPackages(self, packages):
        self._all_packages = packages
        self._apply_filter()

    @Property(str)
    def filterText(self):
        return self._filter_text

    @filterText.setter
    def filterText(self, text):
        if self._filter_text != text:
            self._filter_text = text
            self._apply_filter()

    def _apply_filter(self):
        self.beginResetModel()
        if not self._filter_text:
            self._visible_packages = self._all_packages.copy()
        else:
            q = self._filter_text.lower()
            self._visible_packages = [
                p for p in self._all_packages 
                if q in p.get("name", "").lower() or q in p.get("package", "").lower()
            ]
        self.endResetModel()

    def updateIcon(self, package_name, icon_path):
        for p in self._all_packages:
            if p.get("package") == package_name:
                p["icon"] = icon_path
                break
        for i, p in enumerate(self._visible_packages):
            if p.get("package") == package_name:
                p["icon"] = icon_path
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [self.IconRole])
                break
    
    def clear(self):
        self.beginResetModel()
        self._all_packages = []
        self._visible_packages = []
        self.endResetModel()

class BackendBridge(QObject):
    # Signals for UI
    devicesChanged = Signal(list, arguments=['devices'])
    packagesChanged = Signal(list, arguments=['packages'])
    iconReady = Signal(str, str, arguments=['pkg', 'iconPath'])
    deviceStatusChanged = Signal(str, dict, arguments=['serial', 'status'])
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
    requestIcon = Signal(str, str)
    requestDeviceStatus = Signal(str)
    requestPushFile = Signal(str, str, str)
    requestPullFile = Signal(str, str, str)
    requestScreenshot = Signal(str)
    requestSetVolume = Signal(str, str, int)
    requestSetBrightness = Signal(str, int)
    requestSetRotationLock = Signal(str, bool)
    requestSetAirplaneMode = Signal(str, bool)
    requestSetWifi = Signal(str, bool)
    requestSetBluetooth = Signal(str, bool)
    requestGetClipboard = Signal(str)
    requestSetClipboard = Signal(str, str)
    requestConnectWireless = Signal(str)

    def __init__(self):
        super().__init__()
        self._scrcpy = ScrcpyHandler()
        self._current_device_serial = ""
        self._devices = []
        self._packages = []
        self._launch_mode = "Tablet"
        self._launch_with_screen_off = False
        self._audio_forwarding = False
        self._current_profile = "Default"
        self._profiles = get_profile_names()
        
        self._device_status = {}
        self._package_model = PackageModel()
        self._settings = QSettings("UMC", "DeviceManager")
        self._device_names = self._load_device_names()
        self._device_groups = {} # Placeholder
        
        self._clipboard_sync_enabled = {}
        self._clipboard_history = []
        self._max_clipboard_history = 50
        
        app = QGuiApplication.instance()
        if app:
            self._clipboard = app.clipboard()
            self._last_clipboard_text = self._clipboard.text() if self._clipboard else ""
            if self._clipboard:
                self._clipboard.dataChanged.connect(self._on_desktop_clipboard_data_changed)
        else:
            self._clipboard = None
            self._last_clipboard_text = ""
        
        self._file_transfer_progress = {}
        self._thread = QThread()
        self._worker = ADBWorker()
        self._worker.moveToThread(self._thread)
        
        # Connections
        self.requestDevices.connect(self._worker.fetch_devices)
        self.requestPackages.connect(self._worker.fetch_packages)
        self.requestToggleScreen.connect(self._worker.toggle_device_screen)
        self.requestIcon.connect(self._worker.fetch_icon)
        self.requestDeviceStatus.connect(self._worker.fetch_device_status)
        self.requestScreenshot.connect(self._worker.capture_screenshot)
        self.requestSetVolume.connect(self._worker.set_volume)
        self.requestSetBrightness.connect(self._worker.set_brightness)
        self.requestSetRotationLock.connect(self._worker.set_rotation_lock)
        self.requestSetAirplaneMode.connect(self._worker.set_airplane_mode)
        self.requestSetWifi.connect(self._worker.set_wifi_enabled)
        self.requestSetBluetooth.connect(self._worker.set_bluetooth_enabled)
        self.requestGetClipboard.connect(self._worker.get_clipboard)
        self.requestSetClipboard.connect(self._worker.set_clipboard)
        self.requestConnectWireless.connect(self._worker.connect_wireless)
        
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
        self._timer = QTimer()
        self._timer.timeout.connect(self.requestDevices.emit)
        self._timer.start(3000)
        self.requestDevices.emit()

    # Properties
    @Property(list, notify=devicesChanged)
    def devices(self): return self._devices
    @Property(list, notify=packagesChanged)
    def packages(self): return self._packages
    @Property(str, notify=launchModeChanged)
    def launchMode(self): return self._launch_mode
    @launchMode.setter
    def launchMode(self, m):
        if self._launch_mode != m: self._launch_mode = m; self.launchModeChanged.emit(m)
    @Property(bool, notify=launchWithScreenOffChanged)
    def launchWithScreenOff(self): return self._launch_with_screen_off
    @launchWithScreenOff.setter
    def launchWithScreenOff(self, e):
        if self._launch_with_screen_off != e: self._launch_with_screen_off = e; self.launchWithScreenOffChanged.emit(e)
    @Property(bool, notify=audioForwardingChanged)
    def audioForwarding(self): return self._audio_forwarding
    @audioForwarding.setter
    def audioForwarding(self, e):
        if self._audio_forwarding != e: self._audio_forwarding = e; self.audioForwardingChanged.emit(e)
    @Property(str, notify=currentProfileChanged)
    def currentProfile(self): return self._current_profile
    @currentProfile.setter
    def currentProfile(self, p):
        if self._current_profile != p: self._current_profile = p; self.currentProfileChanged.emit(p)
    @Property(list, notify=profilesChanged)
    def profiles(self): return self._profiles
    @Property(str, notify=statusMessage)
    def currentDeviceSerial(self): return self._current_device_serial
    @Property(QObject, constant=True)
    def packagesModel(self): return self._package_model

    # Slots
    @Slot()
    def refresh_devices(self): self.requestDevices.emit()
    @Slot(str)
    def select_device(self, serial):
        self._current_device_serial = serial; self.statusMessage.emit(f"Selected: {serial}")
        self._package_model.clear(); self.requestPackages.emit(serial)
    @Slot(str)
    def toggle_screen(self, serial):
        if serial: self.requestToggleScreen.emit(serial)
    @Slot(str)
    def mirror_device(self, serial):
        if not serial: return
        self._scrcpy.mirror(serial, forward_audio=self._audio_forwarding, 
                           turn_screen_off=self._launch_with_screen_off, extra_flags=get_profile_flags(self._current_profile))
    @Slot(str, str)
    def open_display(self, serial, mode):
        if not serial: return
        w, h, d = self._get_display_params(serial, mode)
        self._scrcpy.create_display(serial, width=w, height=h, dpi=d, forward_audio=self._audio_forwarding, 
                                   turn_screen_off=self._launch_with_screen_off, extra_flags=get_profile_flags(self._current_profile))
    @Slot(str)
    def launch_app(self, package_name):
        if not self._current_device_serial: return
        w, h, d = self._get_display_params(self._current_device_serial, self._launch_mode)
        self._scrcpy.launch_app(self._current_device_serial, package_name, width=w, height=h, 
                               dpi=d, turn_screen_off=self._launch_with_screen_off, 
                               forward_audio=self._audio_forwarding, extra_flags=get_profile_flags(self._current_profile))
    @Slot(str, str)
    @Slot(str, str, str)
    def push_file_to_device(self, s, l, r=""):
        if not s or not l: return
        r = r or f"/sdcard/Download/{os.path.basename(l)}"
        self.requestPushFile.emit(s, l, r)
    @Slot(str, str, str)
    def pull_file_from_device(self, s, r, l):
        if s and r and l: self.requestPullFile.emit(s, r, l)
    
    # Internal Handlers
    @Slot(list)
    def _on_devices_ready(self, devices):
        for d in devices:
            if d['serial'] in self._device_names: d["custom_name"] = self._device_names[d['serial']]
            self.requestDeviceStatus.emit(d['serial'])
        if devices != self._devices: self._devices = devices; self.devicesChanged.emit(self._devices)
    @Slot(str, dict)
    def _on_device_status_ready(self, s, st):
        self._device_status[s] = st; self.deviceStatusChanged.emit(s, st)
        if self._clipboard_sync_enabled.get(s, False): self.requestGetClipboard.emit(s)
    @Slot(str, list)
    def _on_packages_ready(self, serial, packages):
        if serial == self._current_device_serial: self._package_model.setPackages(packages)
    @Slot(str, str)
    def _on_icon_ready(self, pkg, path): self._package_model.updateIcon(pkg, path)
    @Slot(str, str, int)
    def _on_file_transfer_progress(self, s, o, p): self.fileTransferProgress.emit(s, o, p)
    @Slot(str, str, bool)
    def _on_file_transfer_complete(self, s, o, sc): self.fileTransferComplete.emit(s, o, sc)
    @Slot(str, str)
    def _on_screenshot_ready(self, s, p): 
        self.screenshotReady.emit(s, p)
        self.statusMessage.emit(f"Screenshot saved: {os.path.basename(p)}")
    @Slot(str, str)
    def _on_device_control_changed(self, s, c): self.deviceControlChanged.emit(s, c)
    @Slot(str)
    def _on_worker_error(self, m): self.statusMessage.emit(f"Error: {m}")
    @Slot()
    def _on_desktop_clipboard_data_changed(self):
        try:
            txt = self._clipboard.text()
            if txt and txt != self._last_clipboard_text:
                self._last_clipboard_text = txt
                for s, e in self._clipboard_sync_enabled.items():
                    if e: self.requestSetClipboard.emit(s, txt)
                self._add_to_clipboard_history(txt)
        except: pass
    @Slot(str, str)
    def _on_device_clipboard_changed(self, s, t):
        if self._clipboard_sync_enabled.get(s, False) and self._clipboard and t:
            if t != self._clipboard.text():
                self._clipboard.setText(t); self._last_clipboard_text = t; self._add_to_clipboard_history(t)

    # Sync Getters
    @Slot(str, str, result=int)
    def get_volume(self, s, st): return self._device_status.get(s, {}).get(f"volume_{st}", 0)
    @Slot(str, result=int)
    def get_brightness(self, s): return self._device_status.get(s, {}).get("brightness", 128)
    @Slot(str, result=bool)
    def get_rotation_lock(self, s): return self._device_status.get(s, {}).get("rotation_locked", False)
    @Slot(str, result=bool)
    def get_airplane_mode(self, s): return self._device_status.get(s, {}).get("airplane_mode", False)
    
    # Setters
    @Slot(str, str, int)
    def set_volume(self, s, st, l): self.requestSetVolume.emit(s, st, l)
    @Slot(str, int)
    def set_brightness(self, s, l): self.requestSetBrightness.emit(s, l)
    @Slot(str, bool)
    def set_rotation_lock(self, s, l): self.requestSetRotationLock.emit(s, l)
    @Slot(str, bool)
    def set_airplane_mode(self, s, e): self.requestSetAirplaneMode.emit(s, e)
    @Slot(str, bool)
    def set_wifi_enabled(self, s, e): self.requestSetWifi.emit(s, e)
    @Slot(str, bool)
    def set_bluetooth_enabled(self, s, e): self.requestSetBluetooth.emit(s, e)
    @Slot(str, bool)
    def set_clipboard_sync(self, s, e): self._clipboard_sync_enabled[s] = e
    @Slot(str, result=bool)
    def get_clipboard_sync(self, s): return self._clipboard_sync_enabled.get(s, False)
    @Slot(result=list)
    def get_clipboard_history(self): return self._clipboard_history.copy()
    @Slot(str)
    def request_file_selection(self, s):
        path, _ = QFileDialog.getOpenFileName(None, "Select file", os.path.expanduser("~"), "All Files (*)")
        if path: self.push_file_to_device(s, path)
    @Slot(str)
    def fetch_icon_for_package(self, p): self.requestIcon.emit(self._current_device_serial, p)
    @Slot(str, result="QVariantMap")
    def connect_wireless_device(self, a):
        if ":" not in a: a = f"{a}:5555"
        self.requestConnectWireless.emit(a)
        return {"success": True, "message": "Triggered connect"}
    @Slot(str, str, result="QVariantMap")
    def pair_wireless_device(self, a, c):
        s, m = self._worker.adb_handler.pair_device(a, c)
        return {"success": s, "message": m}
    @Slot(str, result="QVariantMap")
    def disconnect_wireless_device(self, a):
        s, m = self._worker.adb_handler.disconnect_device(a)
        self.requestDevices.emit()
        return {"success": s, "message": m}
    @Slot(str, str)
    def set_device_name(self, s, n):
        if s: self._device_names[s] = n; self._settings.setValue("device_names", json.dumps(self._device_names))
        for d in self._devices:
            if d.get("serial") == s: d["custom_name"] = n
        self.devicesChanged.emit(self._devices)

    # Helpers
    def _get_display_params(self, s, m):
        w, h, d = 1280, 800, 240
        if m == "Desktop": w, h, d = 1920, 1080, 240
        elif m == "Phone":
            st = self._device_status.get(s, {})
            w, h, d = st.get("width", 1080), st.get("height", 2400), st.get("density", 400)
        return w, h, d
    def _load_device_names(self):
        j = self._settings.value("device_names", "{}")
        try: return json.loads(j) if j else {}
        except: return {}
    def _add_to_clipboard_history(self, t):
        if t and t not in self._clipboard_history:
            self._clipboard_history.insert(0, t)
            if len(self._clipboard_history) > self._max_clipboard_history: self._clipboard_history = self._clipboard_history[:self._max_clipboard_history]
    def cleanup(self):
        if self._worker: self._worker.stop()
        if self._timer: self._timer.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            if not self._thread.wait(1000): self._thread.terminate()
