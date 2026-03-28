# Unified Mobile Controller (UMC)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://pypi.org/project/PySide6/)

UMC is a Linux desktop app for controlling Android devices over ADB and `scrcpy` with a PySide6/QML interface.

## Current Scope

- Manage multiple connected Android devices from one desktop UI.
- Launch `scrcpy` mirrors and new-display sessions with a few display profiles.
- Discover launcher apps on the selected device and launch them in `scrcpy`.
- Control common device settings: volume, brightness, rotation lock, airplane mode, Wi-Fi, Bluetooth, screenshots, file push/pull, and selected ADB keyevents.
- Support USB devices and wireless ADB flows such as pairing, TCP/IP enable, and reconnect.

## Architecture

- `main.py` starts the Qt application and exposes `BackendBridge` to QML.
- `backend/bridge.py` owns the UI-facing state and routes queued requests to the worker.
- `backend/worker.py` runs blocking ADB operations on a background `QThread`.
- `backend/adb_handler.py` wraps ADB command execution and response parsing.
- `backend/scrcpy_handler.py` starts `scrcpy` mirror, app-launch, and virtual-display sessions.
- `ui/` contains the QML interface.

## Requirements

- Linux desktop environment
- Python 3.10+
- `adb` available on `PATH`
- `scrcpy` available on `PATH`
- Python dependencies from `requirements.txt`

## Development Setup

```bash
git clone https://github.com/1999AZZAR/UMC.git
cd UMC
pip install -r requirements.txt
python3 main.py
```

## Notes and Limitations

- Clipboard sync is best-effort. It depends on clipboard commands or broadcasts that are not available on every Android build.
- Device status polling is throttled, but package discovery still runs on the same worker thread as other ADB actions.
- File transfer progress is not byte-accurate. The UI currently receives synthetic start/end milestones only.
- `scrcpy` app-launch sessions are tracked for cleanup. Other `scrcpy` session types still need stronger lifecycle tracking.
- Wireless ADB features depend on device and Android-version support.

## Packaging

Debian packaging files are present under `debian/`. Generated `.deb`, `.changes`, `.buildinfo`, and staged packaging output are ignored by the repository.

## Status

The app is functional for day-to-day device control, but the backlog in [todo.md](./todo.md) still contains reliability and delivery work that should be finished before calling the project fully hardened.
