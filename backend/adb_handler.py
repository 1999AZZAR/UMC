import subprocess
import shutil
import re
import os
import zipfile
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class ADBHandler:
    def __init__(self):
        self.adb_path = shutil.which("adb")
        self.last_error = ""

    def _set_error(self, message: str):
        self.last_error = message

    def _run_adb_shell(self, serial: str, *args: str, timeout: int = 5) -> subprocess.CompletedProcess:
        return subprocess.run(
            [self.adb_path, "-s", serial, "shell", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def _read_setting_flag(self, serial: str, namespace: str, key: str) -> Optional[bool]:
        try:
            result = self._run_adb_shell(serial, "settings", "get", namespace, key, timeout=2)
        except (subprocess.SubprocessError, OSError):
            return None

        value = (result.stdout or "").strip().lower()
        if value in {"1", "true", "enabled"}:
            return True
        if value in {"0", "false", "disabled"}:
            return False
        return None

    def connect_wireless(self, address: str) -> tuple[bool, str]:
        if not self.adb_path: return False, "ADB not found"
        try:
            result = subprocess.run([self.adb_path, "connect", address], capture_output=True, text=True, timeout=10)
            output = result.stdout + result.stderr
            if "connected" in output.lower() or "already connected" in output.lower():
                return True, f"Connected to {address}"
            return False, output.strip()
        except subprocess.TimeoutExpired:
            return False, "Connection attempt timed out"
        except Exception as e:
            return False, str(e)

    def disconnect_device(self, address: str) -> tuple[bool, str]:
        if not self.adb_path: return False, "ADB not found"
        try:
            subprocess.run([self.adb_path, "disconnect", address], capture_output=True, timeout=5)
            return True, f"Disconnected from {address}"
        except Exception as e:
            self._set_error(str(e))
            return False, f"Disconnect failed: {e}"

    def get_devices(self) -> List[Dict[str, str]]:
        if not self.adb_path: return []
        try:
            result = subprocess.run([self.adb_path, "devices", "-l"], capture_output=True, text=True, check=True, timeout=5)
            devices = []
            for line in result.stdout.strip().split('\n')[1:]:
                if not line.strip(): continue
                parts = line.split()
                if len(parts) < 2: continue
                serial = parts[0]
                status = parts[1]
                model = "Unknown"
                model_match = re.search(r'model:(\S+)', line)
                if model_match: model = model_match.group(1).replace("_", " ")
                devices.append({"serial": serial, "model": model, "status": status})
            return devices
        except (subprocess.SubprocessError, OSError) as e:
            self._set_error(str(e))
            return []

    def get_device_resolution(self, serial: str) -> tuple[int, int]:
        try:
            result = subprocess.run([self.adb_path, "-s", serial, "shell", "wm", "size"], capture_output=True, text=True, timeout=5)
            match = re.search(r'Physical size: (\d+)x(\d+)', result.stdout)
            if match: return int(match.group(1)), int(match.group(2))
        except (subprocess.SubprocessError, OSError):
            pass
        return 1080, 2400

    def get_device_density(self, serial: str) -> int:
        try:
            result = subprocess.run([self.adb_path, "-s", serial, "shell", "wm", "density"], capture_output=True, text=True, timeout=5)
            match = re.search(r'Physical density: (\d+)', result.stdout)
            if match: return int(match.group(1))
            override = re.search(r'Override density: (\d+)', result.stdout)
            if override: return int(override.group(1))
        except (subprocess.SubprocessError, OSError):
            pass
        return 400

    def get_device_status_info(self, serial: str) -> Dict[str, any]:
        """Deep status gathering with robust parsing."""
        info = {
            "battery_level": 0,
            "battery_status": "unknown",
            "temperature": 0,
            "storage": None,
            "network_type": "wifi" if ":" in serial else "usb",
            "width": 1080,
            "height": 2400,
            "density": 400,
            "brightness": 128,
            "volume_music": 0,
            "rotation_locked": False,
            "airplane_mode": False,
            "wifi_enabled": True,
            "bluetooth_enabled": False
        }
        
        if not self.adb_path: return info

        try:
            # 1. Battery Info (The primary culprit for 5% vs 100%)
            batt_res = subprocess.run([self.adb_path, "-s", serial, "shell", "dumpsys", "battery"], capture_output=True, text=True, timeout=5)
            if batt_res.returncode == 0:
                # Use multiline search to be specific
                level_match = re.search(r'level:\s+(\d+)', batt_res.stdout)
                scale_match = re.search(r'scale:\s+(\d+)', batt_res.stdout)
                temp_match = re.search(r'temperature:\s+(\d+)', batt_res.stdout)
                status_match = re.search(r'status:\s+(\d+)', batt_res.stdout)
                
                level = int(level_match.group(1)) if level_match else 0
                scale = int(scale_match.group(1)) if scale_match else 100
                if scale > 0:
                    info["battery_level"] = int((level * 100) / scale)
                
                if temp_match:
                    info["temperature"] = int(temp_match.group(1)) / 10.0
                
                if status_match:
                    s_code = status_match.group(1)
                    # 1: unknown, 2: charging, 3: discharging, 4: not charging, 5: full
                    info["battery_status"] = {"1":"unknown", "2":"charging","3":"discharging","4":"not charging","5":"full"}.get(s_code, "unknown")

            # 2. Storage Info
            df_res = subprocess.run([self.adb_path, "-s", serial, "shell", "df", "/data"], capture_output=True, text=True, timeout=5)
            if df_res.returncode == 0:
                for line in df_res.stdout.split('\n'):
                    if '/data' in line:
                        p = line.split()
                        if len(p) >= 4:
                            try:
                                # Standard df output: Filesystem Size Used Avail Use% Mounted on
                                # We try to find the index of 'data' to be safe
                                info["storage"] = {"total": int(p[1])//1024, "used": int(p[2])//1024}
                                break
                            except (TypeError, ValueError):
                                pass

            # 3. Display, Settings, etc.
            info["width"], info["height"] = self.get_device_resolution(serial)
            info["density"] = self.get_device_density(serial)
            
            # Simple settings reads
            try:
                info["brightness"] = int(subprocess.run([self.adb_path, "-s", serial, "shell", "settings", "get", "system", "screen_brightness"], capture_output=True, text=True, timeout=2).stdout.strip() or 128)
                rot = subprocess.run([self.adb_path, "-s", serial, "shell", "settings", "get", "system", "accelerometer_rotation"], capture_output=True, text=True, timeout=2).stdout.strip()
                info["rotation_locked"] = (rot == "0")
                air = subprocess.run([self.adb_path, "-s", serial, "shell", "settings", "get", "global", "airplane_mode_on"], capture_output=True, text=True, timeout=2).stdout.strip()
                info["airplane_mode"] = (air == "1")
                wifi_enabled = self._read_setting_flag(serial, "global", "wifi_on")
                if wifi_enabled is not None:
                    info["wifi_enabled"] = wifi_enabled
                bluetooth_enabled = self._read_setting_flag(serial, "global", "bluetooth_on")
                if bluetooth_enabled is not None:
                    info["bluetooth_enabled"] = bluetooth_enabled
            except (subprocess.SubprocessError, OSError, ValueError):
                pass

            # Volume
            vol_out = subprocess.run([self.adb_path, "-s", serial, "shell", "media", "volume", "--get", "--stream", "3"], capture_output=True, text=True, timeout=2).stdout
            v_match = re.search(r'volume is (\d+)', vol_out)
            if v_match: info["volume_music"] = int(v_match.group(1))

        except Exception:
            logger.exception("Error gathering status for %s", serial)
            
        return info

    def get_app_icon_path(self, serial: str, package_name: str, cache_dir: str, timeout: int = 30) -> Optional[str]:
        cache_file = os.path.join(cache_dir, f"{package_name}.png")
        if os.path.exists(cache_file): return cache_file
        temp_apk = os.path.join(cache_dir, f"{package_name}.apk")
        
        try:
            path_out = subprocess.run([self.adb_path, "-s", serial, "shell", "pm", "path", package_name], capture_output=True, text=True, timeout=5).stdout
            apk_path = None
            for line in path_out.split('\n'):
                if "package:" in line:
                    apk_path = line.replace("package:", "").strip()
                    if "base.apk" in apk_path: break
            
            if not apk_path: return None
            pull_result = subprocess.run([self.adb_path, "-s", serial, "pull", apk_path, temp_apk], capture_output=True, text=True, timeout=timeout)
            if pull_result.returncode != 0 or not os.path.exists(temp_apk):
                self._set_error((pull_result.stderr or pull_result.stdout or "APK pull failed").strip())
                return None
            
            with zipfile.ZipFile(temp_apk, 'r') as z:
                # Wide search for icons
                icon_targets = ['res/mipmap-xxhdpi/ic_launcher.png', 'res/mipmap-xhdpi/ic_launcher.png', 'res/drawable-xhdpi/ic_launcher.png']
                extracted = False
                for target in icon_targets:
                    if target in z.namelist():
                        with z.open(target) as zin, open(cache_file, 'wb') as fout: fout.write(zin.read())
                        extracted = True
                        break
                
                if not extracted:
                    for name in z.namelist():
                        if 'ic_launcher.png' in name and name.endswith('.png'):
                            with z.open(name) as zin, open(cache_file, 'wb') as fout: fout.write(zin.read())
                            extracted = True
                            break

            return cache_file if os.path.exists(cache_file) else None
        except (subprocess.SubprocessError, OSError, zipfile.BadZipFile):
            return None
        finally:
            if os.path.exists(temp_apk):
                try:
                    os.remove(temp_apk)
                except OSError:
                    pass

    def push_file(self, serial, local, remote):
        try:
            subprocess.run([self.adb_path, "-s", serial, "push", local, remote], check=True, timeout=600)
            return True
        except (subprocess.SubprocessError, OSError) as e:
            self._set_error(str(e))
            return False

    def pull_file(self, serial, remote, local):
        try:
            subprocess.run([self.adb_path, "-s", serial, "pull", remote, local], check=True, timeout=600)
            return True
        except (subprocess.SubprocessError, OSError) as e:
            self._set_error(str(e))
            return False

    def set_clipboard(self, serial, text):
        subprocess.run([self.adb_path, "-s", serial, "shell", "am", "broadcast", "-a", "clipper.set", "-e", "text", text], capture_output=True)

    def send_keyevent(self, serial: str, keycode: int) -> bool:
        if not self.adb_path:
            self._set_error("ADB not found")
            return False
        try:
            subprocess.run(
                [self.adb_path, "-s", serial, "shell", "input", "keyevent", str(keycode)],
                check=True,
                timeout=5,
            )
            self._set_error("")
            return True
        except (subprocess.SubprocessError, OSError) as e:
            self._set_error(str(e))
            return False

    def get_clipboard(self, serial: str) -> Optional[str]:
        if not self.adb_path:
            return None

        clipboard_cmds = [
            ("cmd", "clipboard", "get"),
            ("sh", "-c", "cmd clipboard read 2>/dev/null"),
        ]

        for cmd in clipboard_cmds:
            try:
                result = self._run_adb_shell(serial, *cmd, timeout=5)
            except Exception:
                continue

            output = (result.stdout or "").strip()
            error = (result.stderr or "").strip()

            if result.returncode != 0:
                continue
            if not output:
                continue
            if "not found" in output.lower() or "not found" in error.lower():
                continue
            if output.lower().startswith("error:"):
                continue

            return output

        return None

    def capture_screenshot(self, serial, path):
        try:
            data = subprocess.run([self.adb_path, "-s", serial, "shell", "screencap", "-p"], capture_output=True, timeout=15).stdout
            if not data: return False
            with open(path, 'wb') as f: f.write(data)
            return True
        except (subprocess.SubprocessError, OSError) as e:
            self._set_error(str(e))
            return False

    def pair_device(self, address: str, code: str) -> tuple[bool, str]:
        if not self.adb_path: return False, "ADB not found"
        try:
            process = subprocess.Popen([self.adb_path, "pair", address], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input=code + "\n", timeout=30)
            output = stdout + stderr
            if "successfully paired" in output.lower(): return True, "Successfully paired"
            return False, output.strip()
        except Exception as e: return False, str(e)

    def enable_tcpip_mode(self, serial: str, port: int = 5555) -> tuple[bool, str]:
        if not self.adb_path:
            return False, "ADB not found"
        try:
            result = subprocess.run(
                [self.adb_path, "-s", serial, "tcpip", str(port)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = (result.stdout + result.stderr).strip()
            if result.returncode == 0:
                return True, output or f"Device now listening on TCP/{port}"
            return False, output or "Failed to enable TCP/IP mode"
        except Exception as e:
            return False, str(e)

    def set_volume(self, serial, stream, level):
        st_type = {'music':'3', 'ring':'2', 'alarm':'4'}.get(stream, '3')
        return subprocess.run([self.adb_path, "-s", serial, "shell", "media", "volume", "--set", str(level), "--stream", st_type], timeout=5).returncode == 0

    def set_brightness(self, serial, level):
        return subprocess.run([self.adb_path, "-s", serial, "shell", "settings", "put", "system", "screen_brightness", str(level)], timeout=5).returncode == 0

    def set_rotation_lock(self, serial, locked):
        val = "0" if locked else "1"
        return subprocess.run([self.adb_path, "-s", serial, "shell", "settings", "put", "system", "accelerometer_rotation", val], timeout=5).returncode == 0

    def set_airplane_mode(self, serial, enabled):
        val = "1" if enabled else "0"
        bool_val = "true" if enabled else "false"
        subprocess.run([self.adb_path, "-s", serial, "shell", "settings", "put", "global", "airplane_mode_on", val], timeout=5)
        subprocess.run([self.adb_path, "-s", serial, "shell", "am", "broadcast", "-a", "android.intent.action.AIRPLANE_MODE", "--ez", "state", bool_val], timeout=5)
        return True

    def set_wifi_enabled(self, serial, enabled):
        cmd = "enable" if enabled else "disable"
        return subprocess.run([self.adb_path, "-s", serial, "shell", "svc", "wifi", cmd], timeout=5).returncode == 0

    def set_bluetooth_enabled(self, serial, enabled):
        cmd = "enable" if enabled else "disable"
        return subprocess.run([self.adb_path, "-s", serial, "shell", "svc", "bluetooth", cmd], timeout=5).returncode == 0

    def get_app_label(self, serial: str, package_name: str) -> Optional[str]:
        """Attempt to get a human-readable label for a package."""
        try:
            # Try pm dump first (often contains label=...)
            res = subprocess.run([self.adb_path, "-s", serial, "shell", "dumpsys", "package", package_name], capture_output=True, text=True, timeout=5)
            # Look for label=
            match = re.search(r'label=([\w\s]+)', res.stdout)
            if match: return match.group(1).strip()
            
            # Try to find the application label in a specific section
            # (varies by Android version)
            for line in res.stdout.split('\n'):
                if 'label=' in line:
                    return line.split('label=')[1].split()[0].strip()
        except Exception:
            return None
        return None
