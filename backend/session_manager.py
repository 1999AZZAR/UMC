import json
import os
import shutil
import subprocess
import uuid
import re
from typing import List, Dict, Optional

class SessionManager:
    def __init__(self, storage_path="sessions.json"):
        self.storage_path = storage_path
        self.sessions = []
        self.load_sessions()

    def load_sessions(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.sessions = json.load(f)
            except Exception as e:
                print(f"Error loading sessions: {e}")
                self.sessions = []
        else:
            self.sessions = []

    def save_sessions(self):
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.sessions, f, indent=4)
        except Exception as e:
            print(f"Error saving sessions: {e}")

    def create_session(self, name: str, serial: str, type: str, package: str = None, 
                       launch_mode: str = "Tablet", profile: str = "Default", 
                       screen_off: bool = False, audio: bool = False) -> str:
        
        # Try to capture current window geometry for this device if running
        geometry = self._capture_geometry(serial)
        
        session = {
            "id": str(uuid.uuid4()),
            "name": name,
            "serial": serial,
            "type": type, # "app" or "mirror"
            "package": package,
            "launch_mode": launch_mode,
            "profile": profile,
            "screen_off": screen_off,
            "audio": audio,
            "geometry": geometry # {x, y, width, height} or None
        }
        
        self.sessions.append(session)
        self.save_sessions()
        return session["id"]

    def delete_session(self, session_id: str):
        self.sessions = [s for s in self.sessions if s["id"] != session_id]
        self.save_sessions()

    def get_sessions(self) -> List[Dict]:
        return self.sessions

    def get_session(self, session_id: str) -> Optional[Dict]:
        for s in self.sessions:
            if s["id"] == session_id:
                return s
        return None

    def _capture_geometry(self, serial: str) -> Optional[Dict]:
        """
        Uses xdotool to find window geometry for 'UMC - {serial}'
        """
        if not shutil.which("xdotool"):
            return None
            
        window_name = f"UMC - {serial}"
        try:
            # 1. Find window ID
            # xdotool search --name "UMC - SERIAL"
            cmd_search = ["xdotool", "search", "--name", window_name]
            result = subprocess.run(cmd_search, capture_output=True, text=True)
            if result.returncode != 0 or not result.stdout.strip():
                return None
            
            # Take the last one if multiple (most recent?)
            wid = result.stdout.strip().split('\n')[-1]
            
            # 2. Get Geometry
            # xdotool getwindowgeometry {wid}
            # Output example:
            # Window 123456
            #   Position: 100,200 (screen: 0)
            #   Geometry: 800x600
            cmd_geo = ["xdotool", "getwindowgeometry", wid]
            geo_res = subprocess.run(cmd_geo, capture_output=True, text=True)
            output = geo_res.stdout
            
            x, y, w, h = 0, 0, 0, 0
            
            pos_match = re.search(r'Position:\s*(\d+),(\d+)', output)
            geo_match = re.search(r'Geometry:\s*(\d+)x(\d+)', output)
            
            if pos_match:
                x, y = map(int, pos_match.groups())
            if geo_match:
                w, h = map(int, geo_match.groups())
                
            if w > 0 and h > 0:
                return {"x": x, "y": y, "width": w, "height": h}
                
        except Exception as e:
            print(f"Error capturing geometry: {e}")
            
        return None
