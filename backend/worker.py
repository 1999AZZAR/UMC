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
        """Fetches installed 3rd party packages with their display names for a specific device."""
        if self.mock_mode or serial.startswith("MOCK"):
            self.packagesReady.emit(serial, [
                {"package": "com.android.chrome", "name": "Chrome"},
                {"package": "com.google.android.youtube", "name": "YouTube"},
                {"package": "com.whatsapp", "name": "WhatsApp"},
                {"package": "com.instagram.android", "name": "Instagram"}
            ])
            return

        try:
            # First, get just package names quickly (fallback)
            cmd = [self.adb_path, "-s", serial, "shell", "pm", "list", "packages", "-3"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            packages = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith("package:"):
                    package_name = line.replace("package:", "").strip()
                    packages.append(package_name)

            # Emit packages with package names as fallback immediately
            apps = [{"package": pkg, "name": pkg} for pkg in packages]
            self.packagesReady.emit(serial, apps)

            # Now try to get app names asynchronously
            try:
                # Get package names with APK paths
                cmd_paths = [self.adb_path, "-s", serial, "shell", "pm", "list", "packages", "-3", "-f"]
                result_paths = subprocess.run(cmd_paths, capture_output=True, text=True, check=True)
                package_data = []
                for line in result_paths.stdout.strip().split('\n'):
                    if line.startswith("package:"):
                        # Format: package:/path/to/apk=package.name
                        # Split on the last '=' since paths can contain '='
                        content = line.replace("package:", "")
                        last_eq = content.rfind('=')
                        if last_eq != -1:
                            apk_path = content[:last_eq]
                            package_name = content[last_eq + 1:]
                            package_data.append({"package": package_name, "apk_path": apk_path})

                # Update apps with real names where possible
                updated_apps = []
                for item in package_data[:50]:  # Limit to first 50 to avoid timeouts
                    try:
                        # Pull APK and get label
                        import tempfile
                        import os

                        with tempfile.NamedTemporaryFile(suffix='.apk', delete=False) as temp_file:
                            temp_apk = temp_file.name

                        try:
                            # Pull APK from device
                            pull_cmd = [self.adb_path, "-s", serial, "pull", item["apk_path"], temp_apk]
                            subprocess.run(pull_cmd, capture_output=True, timeout=10, check=True)

                            # Use aapt to get app label
                            aapt_cmd = ["aapt", "dump", "badging", temp_apk]
                            aapt_result = subprocess.run(aapt_cmd, capture_output=True, text=True, timeout=5)

                            app_name = item["package"]  # fallback
                            # Look for "application-label:" in aapt output
                            for line in aapt_result.stdout.split('\n'):
                                if line.strip().startswith("application-label:"):
                                    # Extract label value, remove quotes if present
                                    label_part = line.split(':', 1)[1].strip()
                                    if label_part.startswith("'") and label_part.endswith("'"):
                                        app_name = label_part[1:-1]
                                    elif label_part.startswith('"') and label_part.endswith('"'):
                                        app_name = label_part[1:-1]
                                    else:
                                        app_name = label_part
                                    break

                            updated_apps.append({"package": item["package"], "name": app_name})

                        finally:
                            # Clean up temp APK
                            try:
                                os.unlink(temp_apk)
                            except:
                                pass

                    except Exception:
                        # Keep original package name
                        updated_apps.append({"package": item["package"], "name": item["package"]})

                # Emit updated list
                updated_apps.sort(key=lambda x: x["name"].lower())
                self.packagesReady.emit(serial, updated_apps)

            except Exception:
                # If anything fails, keep the original package names
                pass

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
