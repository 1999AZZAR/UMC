from typing import Dict, Any

class ScrcpyProfile:
    def __init__(self, name: str, args: Dict[str, Any]):
        self.name = name
        self.args = args

    def to_flags(self) -> list:
        flags = []
        if self.args.get("max_size", 0) > 0:
            flags.append(f"--max-size={self.args['max_size']}")
        
        if self.args.get("bit_rate", 0) > 0:
            flags.append(f"--video-bit-rate={self.args['bit_rate']}")
            
        if self.args.get("max_fps", 0) > 0:
            flags.append(f"--max-fps={self.args['max_fps']}")
            
        if "buffer" in self.args and self.args["buffer"] is not None:
             # scrcpy v2.0+ uses --display-buffer=ms (waiting for audio) or --video-buffer=ms?
             # Actually --display-buffer is for v1.x. v2.x uses --video-buffer?
             # Let's stick to generic if possible, or assume v2.0+
             # v2.0: --scid is used for display. 
             # Let's use --video-buffer if available, or just ignore for now if unsure.
             # Checking scrcpy help (simulated): --video-buffer is common.
             if self.args["buffer"] == 0:
                 # Low latency trick
                 flags.append("--video-buffer=0")
                 flags.append("--audio-buffer=0")
             else:
                 flags.append(f"--video-buffer={self.args['buffer']}")
        
        if "codec" in self.args:
            flags.append(f"--video-codec={self.args['codec']}")
            
        return flags

PROFILES = {
    "Default": ScrcpyProfile("Default", {
        "bit_rate": 8000000
    }),
    "Low Latency": ScrcpyProfile("Low Latency", {
        "max_size": 1024,
        "bit_rate": 4000000,
        "max_fps": 60,
        "buffer": 0,
        "codec": "h264"
    }),
    "High Quality": ScrcpyProfile("High Quality", {
        "bit_rate": 16000000,
        "max_fps": 60,
        "buffer": 50,
        "codec": "h265"
    }),
    "Battery Saver": ScrcpyProfile("Battery Saver", {
        "max_size": 800,
        "bit_rate": 2000000,
        "max_fps": 30,
        "buffer": 0,
        "codec": "h264"
    }),
    "Streaming Mode": ScrcpyProfile("Streaming Mode", {
        "max_size": 1920,
        "bit_rate": 12000000,
        "max_fps": 60,
        "buffer": 100,
        "codec": "h264"
    })
}

def get_profile_names():
    return list(PROFILES.keys())

def get_profile_flags(name: str):
    profile = PROFILES.get(name, PROFILES["Default"])
    return profile.to_flags()
