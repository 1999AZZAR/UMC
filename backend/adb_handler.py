import subprocess
import shutil
import re
import os
from typing import List, Dict, Optional

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

    def get_app_label(self, serial: str, package_name: str) -> str:
        """Gets the display label (name) of an app."""
        if self.mock_mode or serial.startswith("MOCK"):
            # Extract a friendly name from package
            if "." in package_name:
                return package_name.split(".")[-1].capitalize()
            return package_name
        
        try:
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "pm", "dump", package_name
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Look for label in the dump output
            for line in result.stdout.split('\n'):
                if 'label=' in line.lower():
                    # Extract label value
                    parts = line.split('=')
                    if len(parts) > 1:
                        label = parts[1].strip()
                        # Remove quotes if present
                        label = label.strip('"\'')
                        if label:
                            return label
        except Exception as e:
            print(f"Error fetching label for {package_name}: {e}")
        
        # Fallback: use package name
        if "." in package_name:
            return package_name.split(".")[-1].capitalize()
        return package_name

    def get_app_icon_path(self, serial: str, package_name: str, cache_dir: str, timeout: int = 30) -> Optional[str]:
        """
        Fetches app icon from device and saves it to cache.
        Returns the path to the cached icon file, or None if failed.
        """
        if self.mock_mode or serial.startswith("MOCK"):
            return None
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache file path
        cache_file = os.path.join(cache_dir, f"{package_name}.png")
        
        # Return cached icon if it exists
        if os.path.exists(cache_file):
            return cache_file
        
        try:
            # Get the APK path
            apk_path_cmd = [
                self.adb_path, "-s", serial, "shell",
                "pm", "path", package_name
            ]
            apk_result = subprocess.run(apk_path_cmd, capture_output=True, text=True, check=True)
            
            if not apk_result.stdout.strip():
                return None
            
            # Extract path (format: package:/path/to/apk)
            # Modern apps use split APKs, so pm path returns multiple lines
            # We only need the base.apk file
            lines = apk_result.stdout.strip().split('\n')
            apk_path = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("package:"):
                    path = line.replace("package:", "").strip()
                    # Remove any remaining newlines, carriage returns, or extra whitespace
                    path = path.split('\n')[0].split('\r')[0].strip()
                    # Prefer base.apk, but use any if base not found
                    if "base.apk" in path:
                        apk_path = path
                        break
                    elif apk_path is None:
                        apk_path = path
            
            if not apk_path:
                return None
            
            # Final cleanup - ensure no newlines or special characters
            apk_path = apk_path.split('\n')[0].split('\r')[0].strip()
            
            # Pull the APK temporarily
            temp_apk = os.path.join(cache_dir, f"{package_name}.apk")
            try:
                pull_cmd = [self.adb_path, "-s", serial, "pull", apk_path, temp_apk]
                subprocess.run(pull_cmd, capture_output=True, check=True, timeout=timeout)
                
                # Extract icon from APK using zipfile
                import zipfile
                try:
                    with zipfile.ZipFile(temp_apk, 'r') as apk_zip:
                        # Look for common icon paths
                        icon_paths = [
                            'res/mipmap-xxxhdpi/ic_launcher.png',
                            'res/mipmap-xxhdpi/ic_launcher.png',
                            'res/mipmap-xhdpi/ic_launcher.png',
                            'res/mipmap-hdpi/ic_launcher.png',
                            'res/mipmap-mdpi/ic_launcher.png',
                            'res/drawable-xxxhdpi/ic_launcher.png',
                            'res/drawable-xxhdpi/ic_launcher.png',
                            'res/drawable-xhdpi/ic_launcher.png',
                            'res/drawable-hdpi/ic_launcher.png',
                            'res/drawable-mdpi/ic_launcher.png',
                            'res/drawable/ic_launcher.png',
                        ]
                        
                        # Try to find icon in APK
                        icon_found = False
                        for icon_path in icon_paths:
                            if icon_path in apk_zip.namelist():
                                # Extract icon
                                with apk_zip.open(icon_path) as icon_file:
                                    with open(cache_file, 'wb') as out_file:
                                        out_file.write(icon_file.read())
                                icon_found = True
                                break
                        
                        if not icon_found:
                            # Try to find any PNG with ic_launcher in name
                            for name in apk_zip.namelist():
                                if 'ic_launcher' in name.lower() and name.endswith('.png'):
                                    with apk_zip.open(name) as icon_file:
                                        with open(cache_file, 'wb') as out_file:
                                            out_file.write(icon_file.read())
                                    icon_found = True
                                    break
                
                except Exception as e:
                    print(f"Error extracting icon from APK: {e}")
                
                finally:
                    # Clean up temp APK
                    if os.path.exists(temp_apk):
                        try:
                            os.remove(temp_apk)
                        except:
                            pass
                
                if os.path.exists(cache_file):
                    return cache_file
                    
            except subprocess.TimeoutExpired:
                print(f"Timeout pulling APK for {package_name}")
            except Exception as e:
                print(f"Error pulling APK for {package_name}: {e}")
                if os.path.exists(temp_apk):
                    try:
                        os.remove(temp_apk)
                    except:
                        pass
        
        except Exception as e:
            print(f"Error fetching icon for {package_name}: {e}")
        
        return None
