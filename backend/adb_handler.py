import subprocess
import shutil
import re
import os
from typing import List, Dict, Optional

class ADBHandler:
    def __init__(self):
        self.adb_path = shutil.which("adb")

    def connect(self, address: str) -> bool:
        """Connects to a device via TCP/IP."""
        if not self.adb_path:
            return False
            
        try:
            subprocess.run([self.adb_path, "connect", address], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def disconnect(self, address: str) -> bool:
        """Disconnects a device."""
        if not self.adb_path:
            return False
            
        try:
            subprocess.run([self.adb_path, "disconnect", address], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def get_devices(self) -> List[Dict[str, str]]:
        if not self.adb_path:
            return []

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
        if not self.adb_path:
            return []

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
        
        if not self.adb_path:
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
        
        if not self.adb_path:
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
        if not self.adb_path:
            # Fallback: use package name
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
        if not self.adb_path:
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
                # Use Popen so we can kill it if needed
                process = subprocess.Popen(pull_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    process.wait(timeout=timeout)
                    if process.returncode != 0:
                        return None
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    return None
                
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

    def get_battery_level(self, serial: str) -> Optional[int]:
        """Gets battery level percentage (0-100)."""
        if not self.adb_path:
            return None
        
        try:
            cmd = [self.adb_path, "-s", serial, "shell", "dumpsys", "battery"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
            
            for line in result.stdout.split('\n'):
                if 'level:' in line.lower():
                    try:
                        level = int(line.split(':')[1].strip())
                        return level
                    except (ValueError, IndexError):
                        pass
        except Exception as e:
            print(f"Error fetching battery for {serial}: {e}")
        
        return None

    def get_battery_status(self, serial: str) -> Optional[str]:
        """Gets battery status (charging, discharging, full, etc.)."""
        if not self.adb_path:
            return None
        
        try:
            cmd = [self.adb_path, "-s", serial, "shell", "dumpsys", "battery"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
            
            for line in result.stdout.split('\n'):
                if 'status:' in line.lower():
                    status_code = line.split(':')[1].strip()
                    # Status codes: 1=unknown, 2=charging, 3=discharging, 4=not charging, 5=full
                    status_map = {
                        "1": "unknown",
                        "2": "charging",
                        "3": "discharging",
                        "4": "not charging",
                        "5": "full"
                    }
                    return status_map.get(status_code, "unknown")
        except Exception as e:
            print(f"Error fetching battery status for {serial}: {e}")
        
        return None

    def get_device_temperature(self, serial: str) -> Optional[float]:
        """Gets device temperature in Celsius."""
        if not self.adb_path:
            return None
        
        try:
            # Try to get battery temperature first (most reliable)
            cmd = [self.adb_path, "-s", serial, "shell", "dumpsys", "battery"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
            
            for line in result.stdout.split('\n'):
                if 'temperature:' in line.lower():
                    try:
                        temp = int(line.split(':')[1].strip())
                        # Battery temperature is in tenths of a degree Celsius
                        return temp / 10.0
                    except (ValueError, IndexError):
                        pass
        except Exception as e:
            print(f"Error fetching temperature for {serial}: {e}")
        
        return None

    def get_storage_info(self, serial: str) -> Optional[Dict[str, int]]:
        """Gets storage information (total, used, free in MB)."""
        if not self.adb_path:
            return None
        
        try:
            cmd = [self.adb_path, "-s", serial, "shell", "df", "/data"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
            
            # Parse df output
            # Format: Filesystem      1K-blocks    Used Available Use% Mounted on
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 4:
                    try:
                        total_kb = int(parts[1])
                        used_kb = int(parts[2])
                        free_kb = int(parts[3])
                        
                        return {
                            "total": total_kb // 1024,  # Convert to MB
                            "used": used_kb // 1024,
                            "free": free_kb // 1024
                        }
                    except (ValueError, IndexError):
                        pass
        except Exception as e:
            print(f"Error fetching storage for {serial}: {e}")
        
        return None

    def get_network_type(self, serial: str) -> Optional[str]:
        """Gets network connection type (usb, wifi, etc.)."""
        if not self.adb_path:
            return None
        
        # Check if serial contains IP address (wifi) or not (usb)
        if ":" in serial:
            return "wifi"
        return "usb"

    def get_device_status_info(self, serial: str) -> Dict[str, any]:
        """Gets all device status information at once."""
        return {
            "battery_level": self.get_battery_level(serial),
            "battery_status": self.get_battery_status(serial),
            "temperature": self.get_device_temperature(serial),
            "storage": self.get_storage_info(serial),
            "network_type": self.get_network_type(serial)
        }

    def push_file(self, serial: str, local_path: str, remote_path: str, callback=None) -> bool:
        """
        Push a file from local to device.
        callback(progress_percent, bytes_transferred, total_bytes) can be provided for progress.
        """
        if not self.adb_path:
            return False
        
        try:
            cmd = [self.adb_path, "-s", serial, "push", local_path, remote_path]
            
            if callback:
                # Use Popen to track progress
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                # For now, just wait - progress parsing would require more complex logic
                process.wait()
                return process.returncode == 0
            else:
                result = subprocess.run(cmd, check=True, capture_output=True, timeout=300)
                return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
            print(f"Error pushing file to {serial}: {e}")
            return False

    def pull_file(self, serial: str, remote_path: str, local_path: str, callback=None) -> bool:
        """
        Pull a file from device to local.
        callback(progress_percent, bytes_transferred, total_bytes) can be provided for progress.
        """
        if not self.adb_path:
            return False
        
        try:
            cmd = [self.adb_path, "-s", serial, "pull", remote_path, local_path]
            
            if callback:
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                process.wait()
                return process.returncode == 0
            else:
                result = subprocess.run(cmd, check=True, capture_output=True, timeout=300)
                return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
            print(f"Error pulling file from {serial}: {e}")
            return False

    def list_files(self, serial: str, remote_path: str = "/sdcard") -> List[Dict[str, str]]:
        """List files in a remote directory."""
        if not self.adb_path:
            return []
        
        try:
            cmd = [self.adb_path, "-s", serial, "shell", "ls", "-lh", remote_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
            
            files = []
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 9:
                    # Format: -rw-r--r-- 1 user group size date time name
                    file_type = "directory" if parts[0].startswith("d") else "file"
                    size = parts[4] if file_type == "file" else ""
                    name = " ".join(parts[8:])  # Handle names with spaces
                    files.append({"name": name, "type": file_type, "size": size})
            
            return files
        except Exception as e:
            print(f"Error listing files on {serial}: {e}")
            return []

    def get_clipboard(self, serial: str) -> Optional[str]:
        """Get clipboard content from Android device."""
        if not self.adb_path:
            return None
        
        try:
            # Method 1: Try using service call (Android 10+)
            # This requires root or special permissions, so may not work
            # Method 2: Use a clipboard manager app like Clipper
            # Method 3: Use dumpsys (requires root)
            
            # For now, we'll use a workaround: try to get via service call
            # Note: This may not work without root or special permissions
            cmd = [self.adb_path, "-s", serial, "shell", "service", "call", "clipboard", "1"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            # Parse result - format is complex binary data
            # For simplicity, we'll return None and let the UI handle it
            # A better solution would require a clipboard manager app
            return None
        except Exception as e:
            # Silently fail - clipboard access requires special permissions
            return None

    def set_clipboard(self, serial: str, text: str) -> bool:
        """Set clipboard content on Android device."""
        if not self.adb_path:
            return False
        
        try:
            # Method 1: Use Clipper app (if installed)
            # am broadcast -a clipper.set -e text "content"
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "am", "broadcast", "-a", "clipper.set", "-e", "text", text
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True
            
            # Method 2: Try service call (may require root)
            # This is more complex and may not work
            return False
        except Exception as e:
            # Clipboard setting requires special permissions or apps
            # Return False to indicate it may not have worked
            return False
    
    def capture_screenshot(self, serial: str, save_path: str) -> bool:
        """Capture screenshot from device and save to local path."""
        if not self.adb_path:
            return False
        
        try:
            # Use screencap command and pipe to file
            cmd = [self.adb_path, "-s", serial, "shell", "screencap", "-p"]
            result = subprocess.run(cmd, capture_output=True, check=True, timeout=10)
            
            # Write the PNG data to file
            with open(save_path, 'wb') as f:
                f.write(result.stdout)
            return True
        except Exception as e:
            print(f"Error capturing screenshot from {serial}: {e}")
            return False
    
    def set_volume(self, serial: str, stream: str, level: int) -> bool:
        """
        Set volume level for a specific stream.
        stream: 'music', 'ring', 'alarm', 'notification', 'system', 'voice_call'
        level: 0-15 (typical range, may vary by device)
        """
        if not self.adb_path:
            return False
        
        try:
            # Map stream names to Android stream types
            stream_map = {
                'music': '3',
                'ring': '2',
                'alarm': '4',
                'notification': '5',
                'system': '1',
                'voice_call': '0'
            }
            
            stream_type = stream_map.get(stream.lower(), '3')  # Default to music
            
            # Method 1: Use media volume command (Android 7.0+)
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "media", "volume", "--set", str(level), "--stream", stream_type
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            # Method 2: Fallback to service call (requires root or special permissions)
            if result.returncode != 0:
                # Try using service call for audio service
                # This is more complex and may require root
                cmd = [
                    self.adb_path, "-s", serial, "shell",
                    "service", "call", "audio", "3", "i32", stream_type, "i32", str(level)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            # Method 3: Use key events as last resort (less precise)
            if result.returncode != 0:
                # Calculate how many volume up/down key events needed
                # This is approximate and not ideal
                current_vol = self.get_volume(serial, stream) or 0
                diff = level - current_vol
                if diff != 0:
                    keycode = "KEYCODE_VOLUME_UP" if diff > 0 else "KEYCODE_VOLUME_DOWN"
                    for _ in range(abs(diff)):
                        cmd = [
                            self.adb_path, "-s", serial, "shell",
                            "input", "keyevent", keycode
                        ]
                        subprocess.run(cmd, capture_output=True, timeout=2)
                    return True
            
            return result.returncode == 0
        except Exception as e:
            print(f"Error setting volume for {serial}: {e}")
            return False
    
    def get_volume(self, serial: str, stream: str) -> Optional[int]:
        """Get current volume level for a stream."""
        if not self.adb_path:
            return None
        
        try:
            # Map stream names to Android stream types
            stream_map = {
                'music': '3',
                'ring': '2',
                'alarm': '4',
                'notification': '5',
                'system': '1',
                'voice_call': '0'
            }
            
            stream_type = stream_map.get(stream.lower(), '3')  # Default to music
            
            # Method 1: Use media volume command
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "media", "volume", "--get", "--stream", stream_type
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # Parse output like "volume is 7"
                output = result.stdout.strip()
                try:
                    # Extract number from output
                    import re
                    match = re.search(r'(\d+)', output)
                    if match:
                        return int(match.group(1))
                except (ValueError, AttributeError):
                    pass
            
            # Method 2: Try dumpsys audio (requires parsing)
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "dumpsys", "audio"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Parse dumpsys output - this is complex and device-specific
                # For now, return None if we can't get it
                pass
            
            return None
        except Exception as e:
            return None
    
    def set_brightness(self, serial: str, level: int) -> bool:
        """
        Set screen brightness.
        level: 0-255 (typical range)
        """
        if not self.adb_path:
            return False
        
        try:
            # Clamp level to valid range
            level = max(0, min(255, level))
            
            # Method 1: Use settings put (requires WRITE_SETTINGS permission or root)
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "settings", "put", "system", "screen_brightness", str(level)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            # Method 2: If that fails, try direct file write (requires root)
            if result.returncode != 0:
                cmd = [
                    self.adb_path, "-s", serial, "shell",
                    "su", "-c", f"echo {level} > /sys/class/leds/lcd-backlight/brightness"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            # Method 3: Use service call (alternative method)
            if result.returncode != 0:
                # This is device-specific and may not work
                cmd = [
                    self.adb_path, "-s", serial, "shell",
                    "service", "call", "power", "28", "i32", str(level)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            return result.returncode == 0
        except Exception as e:
            print(f"Error setting brightness for {serial}: {e}")
            return False
    
    def get_brightness(self, serial: str) -> Optional[int]:
        """Get current screen brightness."""
        if not self.adb_path:
            return None
        
        try:
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "settings", "get", "system", "screen_brightness"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                try:
                    return int(result.stdout.strip())
                except ValueError:
                    return None
            return None
        except Exception as e:
            return None
    
    def set_rotation_lock(self, serial: str, locked: bool) -> bool:
        """
        Set rotation lock.
        locked: True to lock rotation, False to allow auto-rotation
        """
        if not self.adb_path:
            return False
        
        try:
            # 0 = auto-rotate enabled, 1 = locked
            value = "1" if locked else "0"
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "settings", "put", "system", "accelerometer_rotation", value
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception as e:
            print(f"Error setting rotation lock for {serial}: {e}")
            return False
    
    def get_rotation_lock(self, serial: str) -> Optional[bool]:
        """Get current rotation lock status."""
        if not self.adb_path:
            return None
        
        try:
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "settings", "get", "system", "accelerometer_rotation"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                value = result.stdout.strip()
                return value == "0"  # 0 means auto-rotate enabled (not locked)
            return None
        except Exception as e:
            return None
    
    def set_airplane_mode(self, serial: str, enabled: bool) -> bool:
        """Set airplane mode on/off."""
        if not self.adb_path:
            return False
        
        try:
            value = "1" if enabled else "0"
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "settings", "put", "global", "airplane_mode_on", value
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            # Also need to broadcast the change
            if result.returncode == 0:
                broadcast_cmd = [
                    self.adb_path, "-s", serial, "shell",
                    "am", "broadcast", "-a", "android.intent.action.AIRPLANE_MODE",
                    "--ez", "state", value
                ]
                subprocess.run(broadcast_cmd, capture_output=True, timeout=5)
            
            return result.returncode == 0
        except Exception as e:
            print(f"Error setting airplane mode for {serial}: {e}")
            return False
    
    def get_airplane_mode(self, serial: str) -> Optional[bool]:
        """Get current airplane mode status."""
        if not self.adb_path:
            return None
        
        try:
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "settings", "get", "global", "airplane_mode_on"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                value = result.stdout.strip()
                return value == "1"
            return None
        except Exception as e:
            return None
    
    def set_wifi_enabled(self, serial: str, enabled: bool) -> bool:
        """Enable/disable WiFi."""
        if not self.adb_path:
            return False
        
        try:
            # Method 1: Use svc command (most reliable, requires root on some devices)
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "svc", "wifi", "enable" if enabled else "disable"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            # Method 2: Use settings put (may require WRITE_SETTINGS permission)
            if result.returncode != 0:
                value = "1" if enabled else "0"
                cmd = [
                    self.adb_path, "-s", serial, "shell",
                    "settings", "put", "global", "wifi_on", value
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            # Method 3: Use service call (alternative)
            if result.returncode != 0:
                cmd = [
                    self.adb_path, "-s", serial, "shell",
                    "service", "call", "wifi", "13", "i32", "1" if enabled else "0"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            return result.returncode == 0
        except Exception as e:
            print(f"Error setting WiFi for {serial}: {e}")
            return False
    
    def get_wifi_enabled(self, serial: str) -> Optional[bool]:
        """Get current WiFi status."""
        if not self.adb_path:
            return None
        
        try:
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "settings", "get", "global", "wifi_on"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                value = result.stdout.strip()
                return value == "1"
            return None
        except Exception as e:
            return None
    
    def set_bluetooth_enabled(self, serial: str, enabled: bool) -> bool:
        """Enable/disable Bluetooth."""
        if not self.adb_path:
            return False
        
        try:
            # Method 1: Use svc command (most reliable, requires root on some devices)
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "svc", "bluetooth", "enable" if enabled else "disable"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            # Method 2: Use settings put (may require WRITE_SETTINGS permission)
            if result.returncode != 0:
                value = "1" if enabled else "0"
                cmd = [
                    self.adb_path, "-s", serial, "shell",
                    "settings", "put", "global", "bluetooth_on", value
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            # Method 3: Use service call (alternative)
            if result.returncode != 0:
                cmd = [
                    self.adb_path, "-s", serial, "shell",
                    "service", "call", "bluetooth_manager", "6" if enabled else "8"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            return result.returncode == 0
        except Exception as e:
            print(f"Error setting Bluetooth for {serial}: {e}")
            return False
    
    def get_bluetooth_enabled(self, serial: str) -> Optional[bool]:
        """Get current Bluetooth status."""
        if not self.adb_path:
            return None
        
        try:
            cmd = [
                self.adb_path, "-s", serial, "shell",
                "settings", "get", "global", "bluetooth_on"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                value = result.stdout.strip()
                return value == "1"
            return None
        except Exception as e:
            return None
