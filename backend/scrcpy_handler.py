import subprocess
import shutil
import os

class ScrcpyHandler:
    def __init__(self):
        self.scrcpy_path = shutil.which("scrcpy") or "scrcpy"
        # Track running processes to prevent zombies and duplicates
        self._processes = {} # (serial, package) -> Popen
        self.last_error = ""

    def _launch_process(self, cmd):
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.last_error = ""
            return proc
        except (FileNotFoundError, OSError) as e:
            self.last_error = str(e)
            return None

    def _cleanup_finished(self):
        """Remove finished processes from tracking."""
        finished = [k for k, p in self._processes.items() if p.poll() is not None]
        for k in finished:
            del self._processes[k]

    def launch_app(self, serial: str, package_name: str, width: int = 1280, height: int = 720, dpi: int = 0, turn_screen_off: bool = False, forward_audio: bool = False, extra_flags: list = None):
        self._cleanup_finished()
        package_name = package_name.strip()
        
        # Prevent multiple sessions for the same app on same device
        if (serial, package_name) in self._processes:
            print(f"Session already exists for {package_name} on {serial}")
            return True

        resolution = f"{width}x{height}"
        if dpi > 0: resolution = f"{resolution}/{dpi}"
        
        window_title = f"UMC - {serial} - {package_name}"
        cmd = [
            self.scrcpy_path, "--serial", serial,
            f"--new-display={resolution}",
            f"--start-app={package_name}",
            "--window-title", window_title,
            "--force-adb-forward", "--no-cleanup",
            "--shortcut-mod=lsuper"
        ]
        
        if not forward_audio: cmd.append("--no-audio")
        if turn_screen_off: cmd.append("--turn-screen-off")
        if extra_flags: cmd.extend(extra_flags)
        
        proc = self._launch_process(cmd)
        if proc is None:
            return False
        self._processes[(serial, package_name)] = proc
        return True

    def create_display(self, serial, width=1280, height=720, dpi=0, turn_screen_off=False, forward_audio=False, extra_flags=None):
        self._cleanup_finished()
        resolution = f"{width}x{height}"
        if dpi > 0: resolution = f"{resolution}/{dpi}"
        
        window_title = f"UMC - {serial} (Virtual)"
        cmd = [
            self.scrcpy_path, "--serial", serial,
            f"--new-display={resolution}",
            "--window-title", window_title,
            "--force-adb-forward", "--no-cleanup",
            "--shortcut-mod=lsuper"
        ]
        if not forward_audio: cmd.append("--no-audio")
        if turn_screen_off: cmd.append("--turn-screen-off")
        if extra_flags: cmd.extend(extra_flags)
        
        return self._launch_process(cmd) is not None

    def mirror(self, serial, width=1280, height=720, turn_screen_off=False, forward_audio=False, extra_flags=None):
        self._cleanup_finished()
        window_title = f"UMC - {serial}"
        cmd = [
            self.scrcpy_path, "--serial", serial,
            f"--max-size={max(width, height)}",
            "--window-title", window_title,
            "--shortcut-mod=lsuper"
        ]
        if not forward_audio: cmd.append("--no-audio")
        if turn_screen_off: cmd.append("--turn-screen-off")
        if extra_flags: cmd.extend(extra_flags)
        
        return self._launch_process(cmd) is not None

    def stop_all(self):
        """Kill all managed scrcpy sessions safely."""
        for proc in self._processes.values():
            try:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=1)
            except (OSError, subprocess.SubprocessError):
                try:
                    proc.kill()
                except (OSError, subprocess.SubprocessError):
                    pass
        self._processes.clear()
