import subprocess
import shutil
import re
from typing import List, Dict

class ADBHandler:
    def __init__(self):
        self.adb_path = shutil.which("adb")
        self.mock_mode = self.adb_path is None

    def connect(self, address: str) -> bool:
        """Connects to a device via TCP/IP."""
        if self.mock_mode:
            print(f"Mock connecting to {address}")
            return True
            
        try:
            subprocess.run([self.adb_path, "connect", address], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def disconnect(self, address: str) -> bool:
        """Disconnects a device."""
        if self.mock_mode:
            print(f"Mock disconnecting {address}")
            return True
            
        try:
            subprocess.run([self.adb_path, "disconnect", address], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def get_devices(self) -> List[Dict[str, str]]:
        if self.mock_mode:
            return [
                {"serial": "MOCK_DEVICE_01", "model": "Pixel_7_Pro", "status": "device"},
                {"serial": "192.168.1.105:5555", "model": "Galaxy_Tab_S8", "status": "device"}
            ]

        try:
            result = subprocess.run(
                [self.adb_path, "devices", "-l"],
                capture_output=True, text=True, check=True
            )
            devices = []
            # Skip first line "List of devices attached"
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
            return devices
        except subprocess.CalledProcessError as e:
            print(f"ADB Error: {e}")
            return []
        except Exception as e:
            print(f"General Error: {e}")
            return []

    def get_installed_packages(self, serial: str) -> List[str]:
        if self.mock_mode or serial.startswith("MOCK"):
            return [
                "com.android.chrome", "com.google.android.youtube", 
                "com.whatsapp", "com.instagram.android", "com.twitter.android",
                "com.spotify.music", "com.netflix.mediaclient", "com.discord",
                "com.microsoft.teams", "com.slack", "org.telegram.messenger"
            ]

        try:
            # -3 to list third-party apps only, usually more relevant
            cmd = [self.adb_path, "-s", serial, "shell", "pm", "list", "packages", "-3"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            packages = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith("package:"):
                    packages.append(line.replace("package:", "").strip())
            return sorted(packages)
        except Exception as e:
            print(f"Error fetching packages for {serial}: {e}")
            return []

    def get_device_resolution(self, serial: str) -> tuple[int, int]:
        default_res = (1080, 2400)
        
        if self.mock_mode or serial.startswith("MOCK"):
            return default_res

        try:
            cmd = [self.adb_path, "-s", serial, "shell", "wm", "size"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Output format: "Physical size: 1080x2400"
            output = result.stdout.strip()
            if "Physical size:" in output:
                res_str = output.split("Physical size:")[1].strip()
                width, height = map(int, res_str.split("x"))
                return (width, height)
        except Exception as e:
            print(f"Error fetching resolution for {serial}: {e}")
        
        return default_res

    def get_device_density(self, serial: str) -> int:
        default_density = 400
        
        if self.mock_mode or serial.startswith("MOCK"):
            return default_density

        try:
            cmd = [self.adb_path, "-s", serial, "shell", "wm", "density"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            
            # Output examples:
            # "Physical density: 480"
            # "Physical density: 480\nOverride density: 420"
            
            override_val = None
            physical_val = None

            for line in output.split('\n'):
                line = line.strip()
                if "Override density:" in line:
                    try:
                        override_val = int(line.split(":")[1].strip())
                    except ValueError:
                        pass
                elif "Physical density:" in line:
                    try:
                        physical_val = int(line.split(":")[1].strip())
                    except ValueError:
                        pass
            
            # Prefer override if it exists
            if override_val is not None:
                return override_val
            if physical_val is not None:
                return physical_val
                
        except Exception as e:
            print(f"Error fetching density for {serial}: {e}")
        
        return default_density
