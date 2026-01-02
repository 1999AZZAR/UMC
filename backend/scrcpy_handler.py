import subprocess
import shutil

class ScrcpyHandler:
    def __init__(self):
        self.scrcpy_path = shutil.which("scrcpy") or "scrcpy"

    def launch_app(self, serial: str, package_name: str, width: int = 1280, height: int = 720, dpi: int = 0, turn_screen_off: bool = False, forward_audio: bool = False):
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
