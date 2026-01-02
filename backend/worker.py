import subprocess
import shutil
import re
from typing import List, Dict, Optional, Tuple
from PySide6.QtCore import QObject, Signal, Slot, QThread

class ADBWorker(QObject):
    """
    Worker thread for handling blocking ADB operations.
    """
    devicesReady = Signal(list)
    packagesReady = Signal(str, list)
    errorOccurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.adb_path = shutil.which("adb")
        self.mock_mode = self.adb_path is None

    @Slot()
    def fetch_devices(self):
        """Fetches the list of connected devices."""
        if self.mock_mode:
            self.devicesReady.emit([
                {"serial": "MOCK_DEVICE_01", "model": "Pixel_7_Pro", "status": "device"},
                {"serial": "192.168.1.105:5555", "model": "Galaxy_Tab_S8", "status": "device"}
            ])
            return

        try:
            result = subprocess.run(
                [self.adb_path, "devices", "-l"],
                capture_output=True, text=True, check=True
            )
            devices = []
            # Regex to parse "serial status ... model:X ..."
            # Example: "serial_123 device product:x model:Pixel_6 device:x"
            for line in result.stdout.strip().split('\n')[1:]:
                if not line.strip():
                    continue
                
                parts = line.split()
                serial = parts[0]
                status = parts[1]
                model = "Unknown"
                
                # Robust model extraction
                model_match = re.search(r'model:(\S+)', line)
                if model_match:
                    model = model_match.group(1).replace("_", " ")
                
                devices.append({
                    "serial": serial,
                    "model": model,
                    "status": status
                })
            
            self.devicesReady.emit(devices)
            
        except subprocess.CalledProcessError as e:
            self.errorOccurred.emit(f"ADB Error: {e}")
        except Exception as e:
            self.errorOccurred.emit(f"General Error: {str(e)}")

    @Slot(str)
    def fetch_packages(self, serial: str):
        """Fetches installed 3rd party packages for a specific device."""
        if self.mock_mode or serial.startswith("MOCK"):
            self.packagesReady.emit(serial, [
                "com.android.chrome", "com.google.android.youtube", 
                "com.whatsapp", "com.instagram.android"
            ])
            return

        try:
            cmd = [self.adb_path, "-s", serial, "shell", "pm", "list", "packages", "-3"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            packages = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith("package:"):
                    packages.append(line.replace("package:", "").strip())
            
            self.packagesReady.emit(serial, sorted(packages))
            
        except Exception as e:
            self.errorOccurred.emit(f"Failed to fetch packages: {str(e)}")

    def get_device_info(self, serial: str) -> Tuple[int, int, int]:
        """
        Synchronous helper to get resolution and density.
        Since this is called only when launching an app (user action),
        it is acceptable to be blocking, or we can make it async if needed.
        For now, we keep it synchronous but robust.
        Returns: (width, height, density)
        """
        width, height = 1080, 2400 # Defaults
        density = 400
        
        if self.mock_mode or serial.startswith("MOCK"):
            return width, height, density

        try:
            # 1. Get Resolution
            res_cmd = [self.adb_path, "-s", serial, "shell", "wm", "size"]
            res_out = subprocess.run(res_cmd, capture_output=True, text=True).stdout.strip()
            # Match "Physical size: 1080x2400" or "Override size: ..."
            # Prioritize Override
            res_match = re.search(r'Override size:\s*(\d+)x(\d+)', res_out)
            if not res_match:
                res_match = re.search(r'Physical size:\s*(\d+)x(\d+)', res_out)
            
            if res_match:
                width, height = map(int, res_match.groups())

            # 2. Get Density
            den_cmd = [self.adb_path, "-s", serial, "shell", "wm", "density"]
            den_out = subprocess.run(den_cmd, capture_output=True, text=True).stdout.strip()
            # Match "Override density: 420" or "Physical density: 480"
            den_match = re.search(r'Override density:\s*(\d+)', den_out)
            if not den_match:
                den_match = re.search(r'Physical density:\s*(\d+)', den_out)
            
            if den_match:
                density = int(den_match.group(1))

        except Exception as e:
            print(f"Warning: Could not fetch device info: {e}")
            
        return width, height, density
