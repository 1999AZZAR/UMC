# Unified Mobile Controller (UMC)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://pypi.org/project/PySide6/)
[![Version](https://img.shields.io/badge/version-v1.0.6-indigo.svg)](https://github.com/1999AZZAR/UMC/releases/tag/v1.0.6)

A high-performance desktop application for managing Android devices and launching applications in isolated virtual displays using scrcpy and ADB.

---

## Technical Overview

The Unified Mobile Controller (UMC) is a professional-grade Linux desktop application designed to provide a centralized interface for multi-device Android orchestration. It focuses on zero-latency interaction, robust resource management, and a clean, tool-oriented user experience.

### Architectural Core

UMC implements a strictly decoupled multi-threaded architecture to ensure maximum stability and responsiveness.

- **Asynchronous Execution Layer**: All blocking ADB operations are delegated to a dedicated background worker thread. This prevents UI thread starvation and ensures the interface remains fluid even during intensive device communication or network timeouts.
- **Signal-Slot Orchestration**: Thread communication is managed via PySide6's signal-slot mechanism, enforcing strict data boundaries and preventing race conditions.
- **Reactive Model System**: The application uses a custom PackageModel (inheriting from QAbstractListModel). This allows for efficient, granular updates to the UI, such as dynamic icon fetching, without the performance overhead of full list re-renders.

### Performance and Stability

- **Resource Management**: Implements proactive cleanup for scrcpy processes and background workers to prevent memory leaks and zombie processes.
- **ADB Reliability**: All shell operations include failsafe timeouts and robust parsing logic to handle intermittent connectivity and varied device responses.
- **Efficient Synchronization**: Clipboard synchronization and device status monitoring are event-driven, minimizing polling overhead while maintaining near-instant state updates.

---

## Key Features

- **Advanced Device Control**:
    - High-fidelity mirroring with zero-latency input.
    - Isolated virtual displays for multi-tasking (Tablet, Phone, and Desktop modes).
    - Remote volume, brightness, and power management.
- **Application Orchestration**:
    - Automated discovery of launchable activities.
    - Asynchronous icon caching and metadata retrieval.
    - Batch launching capabilities across multiple connected devices.
- **System Monitoring**:
    - Real-time telemetry for battery level, thermal state, and storage utilization.
    - Support for both USB and wireless (TCP/IP) connectivity.

---

## Implementation Details

### Configuration Profiles

The system supports specialized performance profiles to adapt to different network conditions:
- **Low Latency**: Optimized for interactive speed (4Mbps, 60fps, 0ms buffer).
- **High Quality**: Optimized for visual fidelity (16Mbps, h265, 50ms buffer).
- **Standard**: Balanced profile for daily utilization.

### Technical Requirements

- **Linux Environment**: Tested on Debian/Ubuntu based distributions.
- **Python**: Version 3.10 or higher.
- **Dependencies**: PySide6, scrcpy (v2.0+), and adb.

---

## Installation and Deployment

### Standard Installation (Debian/Ubuntu)

```bash
# Download and install via dpkg
wget https://github.com/1999AZZAR/UMC/releases/download/v1.0.6/umc_1.0.6_all.deb
sudo dpkg -i umc_1.0.6_all.deb
sudo apt install -f
```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/1999AZZAR/UMC.git
cd UMC

# Install dependencies
pip install -r requirements.txt

# Execute application
python3 main.py
```

---

## Project Status

UMC v1.0.6 represents a significant milestone in code quality and architectural reliability. The transition to a model-driven UI and asynchronous backend ensures that the application is ready for complex, professional workflows.

Created by **Azzar Budiyanto**. Refined by **MEMA** (Multi-Euristic Mind Automaton).
