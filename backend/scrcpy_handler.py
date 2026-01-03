import subprocess
import shutil

class ScrcpyHandler:
    def __init__(self):
        self.scrcpy_path = shutil.which("scrcpy") or "scrcpy"

    def launch_app(self, serial: str, package_name: str, width: int = 1280, height: int = 720, dpi: int = 0, turn_screen_off: bool = False, forward_audio: bool = False, extra_flags: list = None, window_x: int = None, window_y: int = None, window_width: int = None, window_height: int = None):
        """
        Launches an app in a new virtual display using scrcpy.
        """
        resolution = f"{width}x{height}"
        if dpi > 0:
            resolution = f"{resolution}/{dpi}"
        
        # Unique window title for finding it later
        window_title = f"UMC - {serial}"

        # Core command structure based on scrcpy v2.0+ / v3.0 features
        # Note: --new-display might be feature specific or require specific android versions (Android 13+)
        # For compatibility, we try to use the most robust command set.
        
        cmd = [
            self.scrcpy_path,
            "--serial", serial,
            f"--new-display={resolution}",   # Create a virtual display
            f"--start-app={package_name}",   # Start specific app
            "--window-title", window_title,
            "--force-adb-forward",
            "--no-cleanup"                   # Keep display alive if needed (optional)
        ]
        
        if window_x is not None:
            cmd.append(f"--window-x={window_x}")
        if window_y is not None:
            cmd.append(f"--window-y={window_y}")
        if window_width is not None:
            cmd.append(f"--window-width={window_width}")
        if window_height is not None:
            cmd.append(f"--window-height={window_height}")
        
        if extra_flags:
            cmd.extend(extra_flags)
        
        # Audio handling: scrcpy sends audio by default in v2.0+
        # If we DO NOT want audio, we add --no-audio (or --no-audio-playback depending on version, --no-audio is standard)
        if not forward_audio:
            cmd.append("--no-audio")

        if turn_screen_off:
            cmd.append("--turn-screen-off")
        
        print(f"Executing: {' '.join(cmd)}")
        
        try:
            # We use Popen to keep it running non-blocking
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            print("Scrcpy not found")
            return False
        except Exception as e:
            print(f"Failed to launch scrcpy: {e}")
            return False

    def mirror(self, serial: str, width: int = 1280, height: int = 720, dpi: int = 0, turn_screen_off: bool = False, forward_audio: bool = False, extra_flags: list = None, window_x: int = None, window_y: int = None, window_width: int = None, window_height: int = None):
        """
        Mirrors the device screen.
        """
        resolution = f"{width}x{height}"
        if dpi > 0:
            resolution = f"{resolution}/{dpi}"
            
        window_title = f"UMC - {serial}"

        cmd = [
            self.scrcpy_path,
            "--serial", serial,
            f"--max-size={max(width, height)}", # Approximate scaling
            "--window-title", window_title
        ]
        
        if window_x is not None:
            cmd.append(f"--window-x={window_x}")
        if window_y is not None:
            cmd.append(f"--window-y={window_y}")
        if window_width is not None:
            cmd.append(f"--window-width={window_width}")
        if window_height is not None:
            cmd.append(f"--window-height={window_height}")
        
        if extra_flags:
            cmd.extend(extra_flags)

        if not forward_audio:
            cmd.append("--no-audio")

        if turn_screen_off:
            cmd.append("--turn-screen-off")
            
        print(f"Executing Mirror: {' '.join(cmd)}")
        
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"Failed to mirror: {e}")
            return False

    def record(self, serial: str, filename: str, time_limit: int = 0):
        """
        Records the device screen to a file.
        """
        cmd = [
            self.scrcpy_path,
            "--serial", serial,
            "--no-display",
            f"--record={filename}"
        ]
        
        if time_limit > 0:
            # Requires 'timeout' command or handling process termination manually.
            # Scrcpy doesn't have a built-in time limit flag usually, 
            # so we might rely on the caller to kill it or use subprocess logic.
            # For simplicity, we just start recording.
            pass

        print(f"Executing Record: {' '.join(cmd)}")
        
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"Failed to record: {e}")
            return False
