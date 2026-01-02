# Unified Mobile Controller (UMC)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://pypi.org/project/PySide6/)

A modern desktop application for managing Android devices and launching applications in isolated virtual displays using `scrcpy` and `adb`.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Technical Details](#technical-details)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Overview

UMC is a cross-platform desktop application that provides a modern graphical interface for managing Android devices. It enables users to:

- **Device Management**: Connect and manage Android devices via USB or network
- **App Launching**: Browse and launch Android applications in isolated virtual displays
- **Virtual Displays**: Run Android apps in native desktop windows using scrcpy
- **Device Monitoring**: Real-time device status and application management

### Tech Stack

- **Frontend**: QML (Qt Quick) for modern, responsive UI
- **Backend**: Python with PySide6 for cross-platform compatibility
- **Tools**: `adb` for device communication, `scrcpy` for virtual displays

## Architecture

UMC uses a robust multi-threaded architecture for optimal performance:

### Core Components

- **Main UI Thread**: QML-based interface handling user interactions
- **Worker Thread**: Background processing for device communication and app management
- **Virtual Displays**: Independent scrcpy subprocesses for each launched application

### Key Features

- **Responsive UI**: Non-blocking interface during device operations
- **Real-time Updates**: Live device status monitoring
- **Isolated Sessions**: Each app runs in its own virtual display
- **Cross-platform**: Works on Linux, Windows, and macOS

## Features

### Core Functionality
- **Device Discovery**: Automatic detection of connected Android devices
- **App Management**: Browse, search, and launch installed applications
- **Virtual Displays**: Run Android apps in desktop windows
- **Launch Modes**: Tablet and Phone modes for different use cases

### Advanced Features
- **Multi-threading**: Responsive UI with background device communication
- **Network Support**: Wireless ADB connections
- **Modern UI**: Clean, intuitive QML-based interface
- **Performance**: Optimized for smooth virtual display rendering

### Developer Tools
- **Debug Mode**: Verbose logging for troubleshooting
- **Mock Mode**: Testing without physical Android devices
- **Device Metrics**: Real-time performance monitoring

## Prerequisites

### System Requirements

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **OS** | Linux, Windows, macOS | Linux recommended for best experience |
| **Python** | 3.10 or higher | Required for application runtime |
| **Display** | X11 or Wayland | Linux display server |
| **ADB** | Android Debug Bridge | Device communication |
| **Scrcpy** | v2.0+ (v3.0+ recommended) | Virtual display rendering |

### Required Tools

#### Android Development Tools
```bash
# Install ADB (Android Debug Bridge)
sudo apt install android-tools-adb  # Ubuntu/Debian
# OR download from: https://developer.android.com/tools/releases/platform-tools

# Install Scrcpy (Screen Copy)
sudo apt install scrcpy  # Ubuntu/Debian
# OR build from source: https://github.com/Genymobile/scrcpy
```

#### Python Dependencies
```bash
pip install PySide6
```

### Hardware Requirements

- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space
- **Android Device**: USB debugging enabled (Settings → Developer Options)

## Installation

### Quick Install (Recommended)

#### Debian/Ubuntu Package
```bash
# Download latest .deb from Releases page
wget https://github.com/YOUR_USERNAME/YOUR_REPO/releases/latest/download/umc_*.deb

# Install package
sudo dpkg -i umc_*.deb
sudo apt install -f  # Fix any dependencies
```

**Package Contents:**
- Pre-compiled application
- PySide6 GUI framework
- Desktop integration
- System shortcuts and icons

### Manual Installation

#### From Source Code
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# Install Python dependencies
pip install -r requirements.txt

# Run application
python main.py
```

#### Build Debian Package Locally
```bash
# Install build dependencies
sudo apt install build-essential debhelper devscripts

# Build package
./build-deb.sh

# Install locally
sudo dpkg -i ../umc_*.deb
```

### PySide6 Compatibility

- **Debian testing/unstable**: PySide6 available in repositories
- **Older distributions**: Install via pip: `pip install PySide6`
- **Windows/macOS**: PySide6 included in requirements.txt

## Usage

### Getting Started

1. **Launch the application**:
   ```bash
   umc  # If installed from package
   # OR
   python main.py  # If running from source
   ```

2. **Connect your Android device**:
   - Enable USB debugging in Developer Options
   - Connect via USB or network (adb connect IP:PORT)

3. **Select device**: Choose from the sidebar when detected

### Interface Overview

#### Main Components
- **Device Sidebar**: Lists connected Android devices
- **App Grid**: Shows installed applications on selected device
- **Search Bar**: Filter applications by name
- **Settings Panel**: Launch mode and display options

#### Launch Modes

| Mode | Resolution | Density | Best For |
|------|------------|---------|----------|
| **Tablet** (Default) | 1280×800 | 160 DPI | Desktop-like experience |
| **Phone** | Device native | Device native | Mobile app compatibility |

**Tablet Mode**: Optimized for desktop usage with larger touch targets
**Phone Mode**: Mirrors exact device specifications for accurate testing

## Technical Details

### Device Communication

- **ADB Integration**: Parses `adb devices -l` with regex for reliable device detection
- **Real-time Monitoring**: Continuous device status polling
- **Network Support**: TCP/IP connections for wireless debugging

### Display Management

**Phone Mode Resolution Logic:**
1. Check `adb shell wm size` for override settings
2. Fall back to physical display size
3. Apply corresponding density from `adb shell wm density`
4. Ensure pixel-perfect virtual display rendering

**Tablet Mode:** Fixed 1280×800 resolution optimized for desktop interaction

## Troubleshooting

### Common Issues

#### Device Connection Problems

**"No devices detected"**
- Enable USB debugging: Settings → Developer Options → USB Debugging
- Authorize computer on device popup
- Try different USB cable/port
- Check device drivers (Windows)

**"Device unauthorized"**
```bash
# Revoke and re-authorize
adb kill-server
adb start-server
# Then reconnect device and authorize
```

#### Application Launch Issues

**"Scrcpy not found"**
```bash
# Install scrcpy
sudo apt install scrcpy  # Ubuntu/Debian
# OR build from source
```

**App closes immediately**
- Try switching launch modes (Tablet ↔ Phone)
- Some apps don't support certain resolutions
- Check device compatibility

**Virtual display issues**
- Ensure X11/Wayland display server is running
- Try different resolution/density settings
- Update scrcpy to latest version

#### General Problems

**Permission denied errors**
```bash
# Add user to plugdev group (Linux)
sudo usermod -a -G plugdev $USER
# Logout and login again
```

**Slow performance**
- Close other applications
- Reduce virtual display resolution
- Use wired connection instead of wireless

### Getting Help

- Check [scrcpy documentation](https://github.com/Genymobile/scrcpy)
- Report issues on [GitHub Issues](https://github.com/YOUR_USERNAME/YOUR_REPO/issues)
- Community discussions available

### Debug Mode

Run with verbose logging:
```bash
python main.py --debug
```

## Development

### Building from Source

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing

# Run tests
python -m pytest

# Build Debian package
./build-deb.sh
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests: `python -m pytest`
5. Commit changes: `git commit -am 'Add feature'`
6. Push to branch: `git push origin feature-name`
7. Submit a Pull Request

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints for function parameters
- Add docstrings to public functions
- Write tests for new features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [scrcpy](https://github.com/Genymobile/scrcpy) - Screen copy tool
- [PySide6](https://wiki.qt.io/Qt_for_Python) - Qt for Python bindings
- [Qt](https://www.qt.io/) - GUI framework