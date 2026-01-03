from typing import Optional
from .adb_handler import ADBHandler
from .scrcpy_handler import ScrcpyHandler

class Device:
    """
    Unified Device API for orchestrating ADB and Scrcpy operations.
    """
    def __init__(self, serial: str, model: str = "Unknown", status: str = "offline"):
        self.serial = serial
        self.model = model
        self.status = status
        self._adb = ADBHandler()
        self._scrcpy = ScrcpyHandler()

    def connect(self) -> bool:
        """
        Connects to the device. 
        For network addresses, it attempts `adb connect`.
        For USB devices, it mainly verifies presence.
        """
        if ":" in self.serial: # Heuristic for network address
            return self._adb.connect(self.serial)
        # For USB, we assume it's connected if we have the object, but we could re-verify
        return True

    def disconnect(self) -> bool:
        """
        Disconnects the device.
        """
        if ":" in self.serial:
            return self._adb.disconnect(self.serial)
        return True

    def launch_app(self, package_name: str, width: int = 1280, height: int = 720, dpi: int = 0, turn_screen_off: bool = False, forward_audio: bool = False) -> bool:
        """
        Launches an app in a virtual display (or standard mirror depending on implementation) on this device.
        """
        return self._scrcpy.launch_app(
            self.serial, 
            package_name, 
            width=width, 
            height=height, 
            dpi=dpi, 
            turn_screen_off=turn_screen_off, 
            forward_audio=forward_audio
        )

    def mirror(self, width: int = 1280, height: int = 720, turn_screen_off: bool = False, forward_audio: bool = False) -> bool:
        """
        Starts screen mirroring for this device.
        """
        return self._scrcpy.mirror(
            self.serial,
            width=width,
            height=height,
            turn_screen_off=turn_screen_off,
            forward_audio=forward_audio
        )

    def record(self, filename: str) -> bool:
        """
        Starts recording the screen of this device to a file.
        """
        return self._scrcpy.record(self.serial, filename)

    def get_info(self):
        """
        Returns resolution and density info.
        """
        return self._adb.get_device_resolution(self.serial), self._adb.get_device_density(self.serial)

    def __repr__(self):
        return f"<Device serial={self.serial} model={self.model} status={self.status}>"
