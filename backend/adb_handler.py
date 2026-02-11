import subprocess
import shutil
import re
import os
import sys
from typing import List, Dict, Optional, Tuple

class ADBHandler:
    def __init__(self):
        self.adb_path = shutil.which("adb")

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
        except: return False, "Disconnect failed"

    def get_devices(self) -> List[Dict[str, str]]:
        if not self.adb_path: return []
        try:
            result = subprocess.run([self.adb_path, "devices", "-l"], capture_output=True, text=True, check=True)
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
        except: return []

    def get_device_resolution(self, serial: str) -> tuple[int, int]:
        try:
            result = subprocess.run([self.adb_path, "-s", serial, "shell", "wm", "size"], capture_output=True, text=True, timeout=5)
            match = re.search(r'Physical size: (\d+)x(\d+)', result.stdout)
            if match: return int(match.group(1)), int(match.group(2))
        except: pass
        return 1080, 2400

    def get_device_density(self, serial: str) -> int:
        try:
            result = subprocess.run([self.adb_path, "-s", serial, "shell", "wm", "density"], capture_output=True, text=True, timeout=5)
            match = re.search(r'Physical density: (\d+)', result.stdout)
            if match: return int(match.group(1))
            override = re.search(r'Override density: (\d+)', result.stdout)
            if override: return int(override.group(1))
        except: pass
        return 400

    def get_device_status_info(self, serial: str) -> Dict[str, any]:
        """Deep status gathering with robust parsing."""
        info = {
            "battery_level": None,
            "battery_status": "unknown",
            "temperature": None,
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
        
        try:
            # 1. Battery & Temp (Using precise regex)
            batt_out = subprocess.run([self.adb_path, "-s", serial, "shell", "dumpsys", "battery"], capture_output=True, text=True, timeout=5).stdout
            level, scale = 100, 100
            for line in batt_out.split('\n'):
                line = line.strip().lower()
                if line.startswith('level:'):
                    try: level = int(line.split(':')[1].strip())
                    except: pass
                elif line.startswith('scale:'):
                    try: scale = int(line.split(':')[1].strip())
                    except: pass
                elif line.startswith('temperature:'):
                    try: info["temperature"] = int(line.split(':')[1].strip()) / 10.0
                    except: pass
                elif line.startswith('status:'):
                    s_code = line.split(':')[1].strip()
                    info["battery_status"] = {"2":"charging","3":"discharging","4":"not charging","5":"full"}.get(s_code, "unknown")
            
            # Calculate actual percentage based on scale
            if scale > 0:
                info["battery_level"] = int((level * 100) / scale)
            else:
                info["battery_level"] = level

            # 2. Storage
            df_out = subprocess.run([self.adb_path, "-s", serial, "shell", "df", "/data"], capture_output=True, text=True, timeout=5).stdout.split('\n')
            if len(df_out) > 1:
                for line in df_out:
                    if '/data' in line:
                        p = line.split()
                        if len(p) >= 4: 
                            try:
                                info["storage"] = {"total": int(p[1])//1024, "used": int(p[2])//1024}
                                break
                            except: pass

            # 3. Display info
            info["width"], info["height"] = self.get_device_resolution(serial)
            info["density"] = self.get_device_density(serial)
            
            # 4. Settings (Brightness & Rotation)
            try:
                b_out = subprocess.run([self.adb_path, "-s", serial, "shell", "settings", "get", "system", "screen_brightness"], capture_output=True, text=True, timeout=2).stdout.strip()
                if b_out.isdigit(): info["brightness"] = int(b_out)
                
                r_out = subprocess.run([self.adb_path, "-s", serial, "shell", "settings", "get", "system", "accelerometer_rotation"], capture_output=True, text=True, timeout=2).stdout.strip()
                info["rotation_locked"] = (r_out == "1")
                
                a_out = subprocess.run([self.adb_path, "-s", serial, "shell", "settings", "get", "global", "airplane_mode_on"], capture_output=True, text=True, timeout=2).stdout.strip()
                info["airplane_mode"] = (a_out == "1")
            except: pass

            # 5. Volume
            vol_out = subprocess.run([self.adb_path, "-s", serial, "shell", "media", "volume", "--get", "--stream", "3"], capture_output=True, text=True, timeout=2).stdout
            v_match = re.search(r'volume is (\d+)', vol_out)
            if v_match: info["volume_music"] = int(v_match.group(1))

        except Exception as e:
            print(f"Error gathering status for {serial}: {e}", file=sys.stderr)
            
        return info

    def get_app_icon_path(self, serial: str, package_name: str, cache_dir: str, timeout: int = 30) -> Optional[str]:
        cache_file = os.path.join(cache_dir, f"{package_name}.png")
        if os.path.exists(cache_file): return cache_file
        
        try:
            path_out = subprocess.run([self.adb_path, "-s", serial, "shell", "pm", "path", package_name], capture_output=True, text=True, timeout=5).stdout
            apk_path = None
            for line in path_out.split('\n'):
                if "package:" in line:
                    apk_path = line.replace("package:", "").strip()
                    if "base.apk" in apk_path: break
            
            if not apk_path: return None
            temp_apk = os.path.join(cache_dir, f"{package_name}.apk")
            subprocess.run([self.adb_path, "-s", serial, "pull", apk_path, temp_apk], capture_output=True, timeout=timeout)
            
            import zipfile
            with zipfile.ZipFile(temp_apk, 'r') as z:
                # Wide search for icons
                icon_targets = [
                    'res/mipmap-xxxhdpi/ic_launcher.png',
                    'res/mipmap-xxhdpi/ic_launcher.png',
                    'res/mipmap-xhdpi/ic_launcher.png',
                    'res/drawable-xxhdpi/ic_launcher.png',
                    'res/drawable-xhdpi/ic_launcher.png'
                ]
                # Try specific targets first
                extracted = False
                for target in icon_targets:
                    if target in z.namelist():
                        with z.open(target) as zin, open(cache_file, 'wb') as fout: fout.write(zin.read())
                        extracted = True
                        break
                
                # Fallback to any ic_launcher
                if not extracted:
                    for name in z.namelist():
                        if 'ic_launcher' in name and name.endswith('.png'):
                            with z.open(name) as zin, open(cache_file, 'wb') as fout: fout.write(zin.read())
                            extracted = True
                            break

            if os.path.exists(temp_apk): os.remove(temp_apk)
            return cache_file if os.path.exists(cache_file) else None
        except: return None

    def push_file(self, serial, local, remote):
        try: subprocess.run([self.adb_path, "-s", serial, "push", local, remote], check=True, timeout=600); return True
        except: return False

    def pull_file(self, serial, remote, local):
        try: subprocess.run([self.adb_path, "-s", serial, "pull", remote, local], check=True, timeout=600); return True
        except: return False

    def set_clipboard(self, serial, text):
        subprocess.run([self.adb_path, "-s", serial, "shell", "am", "broadcast", "-a", "clipper.set", "-e", "text", text], capture_output=True)

    def capture_screenshot(self, serial, path):
        try:
            data = subprocess.run([self.adb_path, "-s", serial, "shell", "screencap", "-p"], capture_output=True, timeout=15).stdout
            if not data: return False
            with open(path, 'wb') as f: f.write(data)
            return True
        except: return False

    def pair_device(self, address: str, code: str) -> tuple[bool, str]:
        if not self.adb_path: return False, "ADB not found"
        try:
            process = subprocess.Popen([self.adb_path, "pair", address], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input=code + "\n", timeout=30)
            output = stdout + stderr
            if "successfully paired" in output.lower(): return True, "Successfully paired"
            return False, output.strip()
        except Exception as e: return False, str(e)

    def set_volume(self, serial, stream, level):
        st_type = {'music':'3', 'ring':'2', 'alarm':'4'}.get(stream, '3')
        return subprocess.run([self.adb_path, "-s", serial, "shell", "media", "volume", "--set", str(level), "--stream", st_type], timeout=5).returncode == 0

    def set_brightness(self, serial, level):
        return subprocess.run([self.adb_path, "-s", serial, "shell", "settings", "put", "system", "screen_brightness", str(level)], timeout=5).returncode == 0

    def set_rotation_lock(self, serial, locked):
        val = "1" if locked else "0"
        return subprocess.run([self.adb_path, "-s", serial, "shell", "settings", "put", "system", "accelerometer_rotation", val], timeout=5).returncode == 0

    def set_airplane_mode(self, serial, enabled):
        val = "1" if enabled else "0"
        subprocess.run([self.adb_path, "-s", serial, "shell", "settings", "put", "global", "airplane_mode_on", val], timeout=5)
        subprocess.run([self.adb_path, "-s", serial, "shell", "am", "broadcast", "-a", "android.intent.action.AIRPLANE_MODE", "--ez", "state", val], timeout=5)
        return True

    def set_wifi_enabled(self, serial, enabled):
        cmd = "enable" if enabled else "disable"
        return subprocess.run([self.adb_path, "-s", serial, "shell", "svc", "wifi", cmd], timeout=5).returncode == 0

    def set_bluetooth_enabled(self, serial, enabled):
        cmd = "enable" if enabled else "disable"
        return subprocess.run([self.adb_path, "-s", serial, "shell", "svc", "bluetooth", cmd], timeout=5).returncode == 0
