from PySide6.QtCore import QObject, Slot, Signal, Property, QTimer, QThread, QSettings, Qt, QAbstractListModel, QModelIndex
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFileDialog
from .worker import ADBWorker
from .scrcpy_handler import ScrcpyHandler
from .profiles import get_profile_names, get_profile_flags
import json
import os
import sys

class PackageModel(QAbstractListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    PackageRole = Qt.ItemDataRole.UserRole + 2
    IconRole = Qt.ItemDataRole.UserRole + 3
    countChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_packages = []
        self._visible_packages = []
        self._filter_text = ""

    def roleNames(self):
        return { self.NameRole: b"name", self.PackageRole: b"packageId", self.IconRole: b"icon" }

    def rowCount(self, parent=QModelIndex()): return len(self._visible_packages)
    
    @Property(int, notify=countChanged)
    def count(self): return len(self._visible_packages)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._visible_packages)): return None
        pkg = self._visible_packages[index.row()]
        if role == self.NameRole: return pkg.get("name")
        if role == self.PackageRole: return pkg.get("package")
        if role == self.IconRole: return pkg.get("icon")
        return None

    def setPackages(self, packages):
        self.beginResetModel()
        self._all_packages = packages
        self._apply_filter_logic()
        self.endResetModel()
        self.countChanged.emit()

    @Property(str)
    def filterText(self): return self._filter_text
    @filterText.setter
    def filterText(self, text):
        if self._filter_text != text:
            self._filter_text = text
            self.beginResetModel()
            self._apply_filter_logic()
            self.endResetModel()
            self.countChanged.emit()

    def _apply_filter_logic(self):
        if not self._filter_text:
            self._visible_packages = self._all_packages.copy()
        else:
            q = self._filter_text.lower()
            self._visible_packages = [
                p for p in self._all_packages 
                if q in p.get("name", "").lower() or q in p.get("package", "").lower()
            ]

    def updateIcon(self, package_name, icon_path):
        found = False
        for p in self._all_packages:
            if p.get("package") == package_name:
                if p["icon"] != icon_path:
                    p["icon"] = icon_path
                    found = True
                break
        if found:
            for i, p in enumerate(self._visible_packages):
                if p.get("package") == package_name:
                    idx = self.index(i)
                    self.dataChanged.emit(idx, idx, [self.IconRole])
                    break
    
    def clear(self):
        self.beginResetModel()
        self._all_packages = []
        self._visible_packages = []
        self.endResetModel()
        self.countChanged.emit()

class BackendBridge(QObject):
    # UI Signals
    devicesChanged = Signal(list)
    deviceStatusChanged = Signal(str, dict)
    fileTransferProgress = Signal(str, str, int)
    fileTransferComplete = Signal(str, str, bool)
    clipboardChanged = Signal(str, str)
    fileSelected = Signal(str)
    screenshotReady = Signal(str, str)
    deviceControlChanged = Signal(str, str)
    statusMessage = Signal(str)
    launchModeChanged = Signal(str)
    launchWithScreenOffChanged = Signal(bool)
    audioForwardingChanged = Signal(bool)
    currentProfileChanged = Signal(str)
    profilesChanged = Signal(list)
    currentDeviceChanged = Signal(str)
    loadingChanged = Signal(bool)
    
    # Internal Signals (Ensures Queued Connection to Worker)
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
    requestPairWireless = Signal(str, str)
    requestDisconnectWireless = Signal(str)
    requestEnableTcpip = Signal(str, int)

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
        self._is_loading = False
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
        
        # Connect signals with proper error safety
        self.requestDevices.connect(self._worker.fetch_devices)
        self.requestPackages.connect(self._worker.fetch_packages)
        self.requestToggleScreen.connect(self._worker.toggle_device_screen)
        self.requestIcon.connect(self._worker.fetch_icon)
        self.requestDeviceStatus.connect(self._worker.fetch_device_status)
        self.requestPushFile.connect(self._worker.push_file)
        self.requestPullFile.connect(self._worker.pull_file)
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
        self.requestPairWireless.connect(self._worker.pair_wireless)
        self.requestDisconnectWireless.connect(self._worker.disconnect_wireless)
        self.requestEnableTcpip.connect(self._worker.enable_tcpip_mode)
        
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
        self._worker.wirelessPairingFinished.connect(self._on_wireless_pairing_finished)
        self._worker.wirelessDisconnectFinished.connect(self._on_wireless_disconnect_finished)
        self._worker.tcpipModeFinished.connect(self._on_tcpip_mode_finished)
        
        self._thread.start()
        self._timer = QTimer()
        self._timer.timeout.connect(self.requestDevices.emit)
        self._timer.start(3000)
        self.requestDevices.emit()

    # --- Properties ---
    @Property(list, notify=devicesChanged)
    def devices(self): return self._devices
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
    @Property(str, notify=currentDeviceChanged)
    def currentDeviceSerial(self): return self._current_device_serial
    @Property(QObject, constant=True)
    def packagesModel(self): return self._package_model
    @Property(bool, notify=loadingChanged)
    def loading(self): return self._is_loading

    def _emit_action_error(self, action: str, error: Exception):
        self.statusMessage.emit(f"{action} failed: {error}")

    # --- Slots for QML ---
    @Slot()
    def refresh_devices(self): 
        try:
            self.requestDevices.emit()
        except Exception as e:
            self.statusMessage.emit(f"Refresh failed: {e}")
    @Slot(str)
    def select_device(self, serial):
        try:
            if not serial: return
            self._current_device_serial = serial; self.currentDeviceChanged.emit(serial)
            self._is_loading = True; self.loadingChanged.emit(True)
            self.statusMessage.emit(f"Selected: {serial}")
            self._package_model.clear(); self.requestPackages.emit(serial)
        except Exception as e:
            self._emit_action_error("Select device", e)
    @Slot(str)
    def toggle_screen(self, serial):
        try:
            if serial: self.requestToggleScreen.emit(serial)
        except Exception as e:
            self._emit_action_error("Toggle screen", e)
    @Slot(str)
    def mirror_device(self, serial):
        try:
            if not serial: return
            success = self._scrcpy.mirror(
                serial,
                width=1280,
                height=720,
                turn_screen_off=self._launch_with_screen_off,
                forward_audio=self._audio_forwarding,
                extra_flags=get_profile_flags(self._current_profile),
            )
            if not success:
                self.statusMessage.emit(f"Mirror failed: {self._scrcpy.last_error or 'Unable to start scrcpy'}")
        except Exception as e: self.statusMessage.emit(f"Mirror failed: {e}")
    @Slot(str, str)
    def open_display(self, serial, mode):
        try:
            if not serial: return
            w, h, d = self._get_display_params(serial, mode)
            success = self._scrcpy.create_display(
                serial,
                width=w,
                height=h,
                dpi=d,
                forward_audio=self._audio_forwarding,
                turn_screen_off=self._launch_with_screen_off,
                extra_flags=get_profile_flags(self._current_profile),
            )
            if not success:
                self.statusMessage.emit(f"Display creation failed: {self._scrcpy.last_error or 'Unable to start scrcpy'}")
        except Exception as e: self.statusMessage.emit(f"Display creation failed: {e}")
    @Slot(str)
    def launch_app(self, package_name):
        try:
            if not self._current_device_serial or not package_name: return
            w, h, d = self._get_display_params(self._current_device_serial, self._launch_mode)
            success = self._scrcpy.launch_app(
                self._current_device_serial,
                package_name,
                width=w,
                height=h,
                dpi=d,
                turn_screen_off=self._launch_with_screen_off,
                forward_audio=self._audio_forwarding,
                extra_flags=get_profile_flags(self._current_profile),
            )
            if not success:
                self.statusMessage.emit(f"App launch failed: {self._scrcpy.last_error or 'Unable to start scrcpy'}")
        except Exception as e: self.statusMessage.emit(f"App launch failed: {e}")
    @Slot(str, str)
    @Slot(str, str, str)
    def push_file_to_device(self, s, l, r=""):
        try:
            if not s or not l: return
            r = r or f"/sdcard/Download/{os.path.basename(l)}"
            self.requestPushFile.emit(s, l, r)
        except Exception as e:
            self._emit_action_error("File push", e)
    @Slot(str, str, str)
    def pull_file_from_device(self, s, r, l):
        try:
            if s and r and l: self.requestPullFile.emit(s, r, l)
        except Exception as e:
            self._emit_action_error("File pull", e)
    @Slot(str)
    def capture_screenshot(self, serial):
        try:
            if serial: self.requestScreenshot.emit(serial)
        except Exception as e:
            self._emit_action_error("Screenshot", e)
    @Slot(str, str, int)
    def set_volume(self, s, st, l):
        try:
            self.requestSetVolume.emit(s, st, l)
        except Exception as e:
            self._emit_action_error("Set volume", e)
    @Slot(str, int)
    def set_brightness(self, s, l):
        try:
            self.requestSetBrightness.emit(s, l)
        except Exception as e:
            self._emit_action_error("Set brightness", e)
    @Slot(str, bool)
    def set_rotation_lock(self, s, l):
        try:
            self.requestSetRotationLock.emit(s, l)
        except Exception as e:
            self._emit_action_error("Set rotation lock", e)
    @Slot(str, bool)
    def set_airplane_mode(self, s, e):
        try:
            self.requestSetAirplaneMode.emit(s, e)
        except Exception as e2:
            self._emit_action_error("Set airplane mode", e2)
    @Slot(str, bool)
    def set_wifi_enabled(self, s, e):
        try:
            self.requestSetWifi.emit(s, e)
        except Exception as e2:
            self._emit_action_error("Set WiFi", e2)
    @Slot(str, bool)
    def set_bluetooth_enabled(self, s, e):
        try:
            self.requestSetBluetooth.emit(s, e)
        except Exception as e2:
            self._emit_action_error("Set Bluetooth", e2)
    @Slot(str, bool)
    def set_clipboard_sync(self, s, e): self._clipboard_sync_enabled[s] = e
    @Slot(str, result=bool)
    def get_clipboard_sync(self, s): return self._clipboard_sync_enabled.get(s, False)
    @Slot(result=list)
    def get_clipboard_history(self): return self._clipboard_history.copy()
    @Slot(str)
    def request_file_selection(self, s):
        try:
            path, _ = QFileDialog.getOpenFileName(None, "Select file", os.path.expanduser("~"), "All Files (*)")
            if path: self.push_file_to_device(s, path)
        except Exception as e:
            self._emit_action_error("File selection", e)
    @Slot(str)
    def fetch_icon_for_package(self, p):
        try:
            self.requestIcon.emit(self._current_device_serial, p)
        except Exception as e:
            self._emit_action_error("Icon fetch", e)
    @Slot(str, result="QVariantMap")
    def connect_wireless_device(self, a):
        try:
            if ":" not in a: a = f"{a}:5555"
            self.requestConnectWireless.emit(a)
            return {"success": True, "message": "Connection attempt started"}
        except Exception as e:
            return {"success": False, "message": f"Failed to start connection: {e}"}
    @Slot(str, str, result="QVariantMap")
    def pair_wireless_device(self, a, c):
        try:
            self.requestPairWireless.emit(a, c)
            return {"success": True, "message": "Pairing attempt started"}
        except Exception as e:
            return {"success": False, "message": f"Pairing failed: {e}"}
    @Slot(str, result="QVariantMap")
    def disconnect_wireless_device(self, a):
        try:
            self.requestDisconnectWireless.emit(a)
            return {"success": True, "message": "Disconnect attempt started"}
        except Exception as e:
            return {"success": False, "message": f"Disconnect failed: {e}"}
    @Slot(str, int, result="QVariantMap")
    def enable_tcpip_mode(self, serial, port=5555):
        try:
            if not serial:
                return {"success": False, "message": "No device selected"}
            self.requestEnableTcpip.emit(serial, port)
            return {"success": True, "message": f"Enabling TCP/IP on port {port}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to enable TCP/IP mode: {e}"}
    @Slot(str, list)
    def launch_app_on_multiple_devices(self, package_name, serials):
        try:
            if not package_name:
                return
            launched = 0
            for serial in serials:
                if not serial:
                    continue
                w, h, d = self._get_display_params(serial, self._launch_mode)
                if self._scrcpy.launch_app(
                    serial,
                    package_name,
                    width=w,
                    height=h,
                    dpi=d,
                    turn_screen_off=self._launch_with_screen_off,
                    forward_audio=self._audio_forwarding,
                    extra_flags=get_profile_flags(self._current_profile),
                ):
                    launched += 1
                elif self._scrcpy.last_error:
                    self.statusMessage.emit(f"Launch failed on {serial}: {self._scrcpy.last_error}")
            if launched:
                self.statusMessage.emit(f"Launched {package_name} on {launched} device(s)")
            else:
                self.statusMessage.emit(f"Failed to launch {package_name}: {self._scrcpy.last_error or 'Unable to start scrcpy'}")
        except Exception as e:
            self.statusMessage.emit(f"Multi-device launch failed: {e}")
    @Slot(str, str)
    def set_device_name(self, s, n):
        if s: self._device_names[s] = n; self._settings.setValue("device_names", json.dumps(self._device_names))
        for d in self._devices:
            if d.get("serial") == s: d["custom_name"] = n
        self.devicesChanged.emit(self._devices)

    # --- Sync Getters ---
    @Slot(str, str, result=int)
    def get_volume(self, s, st): return self._device_status.get(s, {}).get(f"volume_{st}", 0)
    @Slot(str, result=int)
    def get_brightness(self, s): return self._device_status.get(s, {}).get("brightness", 128)
    @Slot(str, result=bool)
    def get_rotation_lock(self, s): return self._device_status.get(s, {}).get("rotation_locked", False)
    @Slot(str, result=bool)
    def get_airplane_mode(self, s): return self._device_status.get(s, {}).get("airplane_mode", False)
    @Slot(str, result=bool)
    def get_wifi_enabled(self, s): return self._device_status.get(s, {}).get("wifi_enabled", True)
    @Slot(str, result=bool)
    def get_bluetooth_enabled(self, s): return self._device_status.get(s, {}).get("bluetooth_enabled", False)

    # --- Internal Handlers ---
    @Slot(list)
    def _on_devices_ready(self, devices):
        try:
            serials = [d['serial'] for d in devices]
            if self._current_device_serial and self._current_device_serial not in serials:
                self._current_device_serial = ""; self.currentDeviceChanged.emit("")
                self._package_model.clear(); self.statusMessage.emit("Device disconnected")
            for d in devices:
                s = d['serial']
                if s in self._device_names: d["custom_name"] = self._device_names[s]
                if s in self._device_status: d["status_data"] = self._device_status[s]
                self.requestDeviceStatus.emit(s)
            if devices != self._devices: self._devices = devices; self.devicesChanged.emit(self._devices)
        except Exception as e: print(f"Error in _on_devices_ready: {e}", file=sys.stderr)
        
    @Slot(str, dict)
    def _on_device_status_ready(self, s, st):
        try:
            previous_status = self._device_status.get(s)
            self._device_status[s] = st
            status_changed = previous_status != st
            for device in self._devices:
                if device['serial'] == s:
                    if device.get("status_data") != st:
                        device["status_data"] = st
                        status_changed = True
                    break
            if status_changed:
                self.devicesChanged.emit(self._devices)
            self.deviceStatusChanged.emit(s, st)
            if self._clipboard_sync_enabled.get(s, False): self.requestGetClipboard.emit(s)
        except Exception as e: print(f"Error in _on_device_status_ready: {e}", file=sys.stderr)

    @Slot(str, list)
    def _on_packages_ready(self, serial, packages):
        if serial == self._current_device_serial:
            self._package_model.setPackages(packages)
            self._is_loading = False; self.loadingChanged.emit(False)

    @Slot(str, str)
    def _on_icon_ready(self, pkg, path): self._package_model.updateIcon(pkg, path)
    @Slot(str, str, int)
    def _on_file_transfer_progress(self, s, o, p): self.fileTransferProgress.emit(s, o, p)
    @Slot(str, str, bool)
    def _on_file_transfer_complete(self, s, o, sc): 
        msg = "completed" if sc else "failed"
        self.statusMessage.emit(f"File {o} {msg} for {s}")
        self.fileTransferComplete.emit(s, o, sc)
    @Slot(str, str)
    def _on_screenshot_ready(self, s, p): 
        self.screenshotReady.emit(s, p)
        self.statusMessage.emit(f"Screenshot saved: {os.path.basename(p)}")
    @Slot(str, str)
    def _on_device_control_changed(self, s, c): self.deviceControlChanged.emit(s, c)
    @Slot(str)
    def _on_worker_error(self, m): 
        self.statusMessage.emit(f"Error: {m}")
        self._is_loading = False; self.loadingChanged.emit(False)
    @Slot(str, bool, str)
    def _on_wireless_pairing_finished(self, address, success, message):
        prefix = "Paired" if success else "Pairing failed"
        self.statusMessage.emit(f"{prefix} for {address}: {message}")
        if success:
            self.requestDevices.emit()
    @Slot(str, bool, str)
    def _on_wireless_disconnect_finished(self, address, success, message):
        prefix = "Disconnected" if success else "Disconnect failed"
        self.statusMessage.emit(f"{prefix} for {address}: {message}")
        if success:
            self.requestDevices.emit()
    @Slot(str, int, bool, str)
    def _on_tcpip_mode_finished(self, serial, port, success, message):
        prefix = "TCP/IP enabled" if success else "TCP/IP enable failed"
        self.statusMessage.emit(f"{prefix} for {serial}:{port} - {message}")
    @Slot()
    def _on_desktop_clipboard_data_changed(self):
        try:
            txt = self._clipboard.text()
            if txt and txt != self._last_clipboard_text:
                self._last_clipboard_text = txt
                for s, e in self._clipboard_sync_enabled.items():
                    if e: self.requestSetClipboard.emit(s, txt)
                self._add_to_clipboard_history(txt)
        except Exception as e:
            self.statusMessage.emit(f"Clipboard sync failed: {e}")
    @Slot(str, str)
    def _on_device_clipboard_changed(self, s, t):
        if self._clipboard_sync_enabled.get(s, False) and self._clipboard and t:
            if t != self._clipboard.text():
                self._clipboard.setText(t); self._last_clipboard_text = t; self._add_to_clipboard_history(t)

    def _get_display_params(self, s, m):
        w, h, d = 1280, 800, 240
        if m == "Desktop": w, h, d = 1920, 1080, 240
        elif m == "Phone":
            st = self._device_status.get(s, {})
            w, h, d = st.get("width", 1080), st.get("height", 2400), st.get("density", 400)
        return w, h, d
    def _load_device_names(self):
        j = self._settings.value("device_names", "{}")
        try:
            return json.loads(j) if j else {}
        except (TypeError, json.JSONDecodeError):
            return {}
    def _add_to_clipboard_history(self, t):
        if t and t not in self._clipboard_history:
            self._clipboard_history.insert(0, t)
            if len(self._clipboard_history) > self._max_clipboard_history: self._clipboard_history = self._clipboard_history[:self._max_clipboard_history]
    def cleanup(self):
        self._scrcpy.stop_all()
        if self._worker: self._worker.stop()
        if self._timer: self._timer.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            if not self._thread.wait(5000):
                print("Warning: worker thread did not stop cleanly before shutdown", file=sys.stderr)
