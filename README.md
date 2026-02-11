# Unified Mobile Controller (UMC)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://pypi.org/project/PySide6/)
[![Version](https://img.shields.io/badge/version-v1.0.6-indigo.svg)](https://github.com/1999AZZAR/UMC/releases/tag/v1.0.6)

A high-performance desktop application for managing Android devices and launching applications in isolated virtual displays using `scrcpy` and `adb`.

---

## 💎 v1.0.6: The Hybrid Evolution

This version introduces a complete architectural overhaul and a new design language, moving UMC towards a professional, enterprise-grade tool.

### 🦾 Architectural Breakthroughs (Thread-Safety)
- **Asynchronous Core**: All blocking ADB operations (status fetching, toggle screen, settings) moved to a dedicated background worker. No more UI freezes.
- **Signal-Slot Orchestration**: Implemented strict Signal/Slot communication between Main Thread and Worker Thread to prevent race conditions.
- **Bulletproof Imports**: Enhanced module discovery with explicit path resolution in `main.py`.

### ⚡ Performance Optimizations
- **PackageModel (QAbstractListModel)**: Replaced static list binding with a reactive C++-style model. This enables granular UI updates (e.g., fetching a single icon) without re-rendering the entire app grid.
- **Resource Efficiency**: Removed hundreds of individual `Connections` objects, drastically reducing memory overhead and CPU usage on devices with many apps.
- **Event-Driven Clipboard**: Replaced 500ms polling with a reactive `dataChanged` signal for near-instant, efficient synchronization.

### 🎨 Design: Neo-M3 Hybrid (v2.1)
Inspired by tech-journalism aesthetics (**Wired** & **The Verge**), the UI now features:
- **Industrial Typography**: Bold, high-contrast labels like `UPLINK_STATUS` and `SONIC_FORWARDING`.
- **Soft Brutalism**: 3px solid black borders paired with massive 24px rounded corners and hard 8px shadows.
- **Tonal Pastel Accents**: A refined color palette (Lavender, Sky Blue, Rose) for better accessibility and visual hierarchy.
- **Adaptive Grid**: A smart, fluid layout that automatically fills the screen, eliminating wasted space on wide monitors.

---

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

UMC is a Linux desktop application providing a graphical interface for managing Android devices. It transforms your desktop into a persistent mobile workspace.

- **Device Management**: Connect and manage Android devices via USB or network.
- **App Launching**: Browse and launch Android applications in isolated virtual displays.
- **Device Monitoring**: Real-time battery, storage, and thermal metrics.

## Architecture

UMC uses a strictly decoupled multi-threaded architecture:

- **Main UI Thread**: PySide6/QML interface optimized for high-FPS interactions.
- **ADB Worker Thread**: Handles all CLI communication to ensure zero-latency UI performance.
- **Reactive Models**: Python-based `QAbstractListModel` for handling large datasets (app lists) with minimal re-renders.

## Features

### Core Functionality
- **Device Discovery**: Automatic detection of connected Android devices via ADB.
- **App Launching**: Fast activity-based discovery of launchable applications.
- **Multi-Screen Control**:
    - **Mirroring**: Zero-latency control of the physical screen.
    - **Virtual Displays**: Independent desktop windows for specific apps or generic tablet/phone modes.
- **Launch Modes**: 
    - **Tablet**: 1280x800 @ 240 DPI
    - **Phone**: Device Native resolution
    - **Desktop**: 1920x1080 @ 240 DPI

### Performance Profiles
- **Low Latency**: Optimized for speed (4Mbps, 60fps, 0ms buffer).
- **High Quality**: Visual fidelity focus (16Mbps, h265, 50ms buffer).
- **Streaming Mode**: Smooth playback (12Mbps, 100ms buffer).

---

## Installation

### Quick Install (Debian/Ubuntu)
```bash
# Download latest v1.0.6 .deb
wget https://github.com/1999AZZAR/UMC/releases/download/v1.0.6/umc_1.0.6_all.deb
sudo dpkg -i umc_1.0.6_all.deb
sudo apt install -f
```

## Development

```bash
# Setup
git clone https://github.com/1999AZZAR/UMC.git
cd UMC
pip install -r requirements.txt

# Run
python3 main.py
```

---

## License
MIT License. Created by **Azzar Budiyanto** (Wong Edan). Refined by **MEMA** (Multi-Euristic Mind Automaton).
