# Unified Mobile Controller (UMC)

A desktop application for managing Android devices and launching applications in isolated virtual displays using `scrcpy` and `adb`.

## Overview

UMC provides a graphical interface to interact with Android devices connected via USB or TCP/IP. It allows users to browse installed applications and launch them in separate, native-like windows on the desktop.

The application is built using:

* **Frontend**: QML (Qt Quick) for the user interface.
* **Backend**: Python (PySide6) for application logic and system interaction.
* **System Tools**:
  * `adb`: For device discovery, package listing, and metrics.
  * `scrcpy`: For rendering device displays and injecting input.

## Architecture

The system operates on a multi-threaded architecture to ensure UI responsiveness:

* **Main Thread (UI)**: Handles the QML rendering and user interactions.
* **Worker Thread**: A dedicated `QThread` executes blocking `adb` commands (device polling, package fetching) to prevent interface freezing.
* **Subprocesses**: `scrcpy` instances are spawned as independent non-blocking subprocesses for each virtual display.

## Prerequisites

### System Requirements

* **Operating System**: Linux (Debian/Ubuntu recommended)
* **Display Server**: X11 or Wayland
* **Android Tools**: `adb` (Android Debug Bridge) must be installed and accessible in the system PATH.
* **Scrcpy**: Version 2.0 or higher is required. Version 3.0+ is recommended for optimal virtual display support.

### Python Dependencies

* Python 3.10 or higher
* PySide6 (Qt for Python)

## Installation

### Option 1: Install from Debian Package (Recommended)

Download the latest `.deb` package from the [Releases](https://github.com/project/umc/releases) page and install it:

```bash
sudo dpkg -i umc_*.deb
# Fix any missing dependencies
sudo apt install -f
```

The Debian package includes:
- All Python dependencies (PySide6, when available in repositories)
- Desktop integration
- System integration with Android tools

**Note**: PySide6 packages are available in Debian testing/unstable. On older Debian/Ubuntu versions, you may need to install PySide6 manually:

```bash
pip3 install PySide6
```

### Building from Source

To build the Debian package locally:

```bash
./build-deb.sh
```

This will create the `.deb` package in the parent directory.

### Continuous Integration

This project uses GitHub Actions for automated building and releasing:

- **Pull Requests**: Builds and tests the package
- **Pushes to main/master**: Automatically creates a nightly release with the built `.deb` package
- **Tags (v*)**: Creates an official release with the built `.deb` package
- **Manual Trigger**: Use GitHub's "Run workflow" button for testing releases

### Release Process

#### Nightly Releases (Automatic)
Every push to `main` or `master` branch automatically:
1. Builds the `.deb` package
2. Creates a nightly release (pre-release)
3. Attaches the package files automatically

#### Official Releases
For official version releases, create a version tag:

```bash
# Option 1: Manual tag creation
git tag v1.0.1
git push origin v1.0.1

# Option 2: Use the helper script
./create-release.sh 1.0.1
```

This creates a stable release with generated release notes.

### Troubleshooting Releases

If releases fail with a 403 error:

#### **Solution 1: Fix Repository Permissions (Recommended)**
1. Go to **Settings** → **Actions** → **General**
2. Under **"Workflow permissions"**, select **"Read and write permissions"**
3. Make sure **"Allow GitHub Actions to create and approve pull requests"** is checked
4. **Save** the changes

**Test**: Push a small change to trigger the workflow and check if releases are created.

#### **Solution 2: Use Personal Access Token**
If the above doesn't work:
1. Create a PAT with `repo` scope at https://github.com/settings/tokens
2. Add it as `RELEASE_TOKEN` secret in your repository:
   - Go to **Settings** → **Secrets and variables** → **Actions**
   - Click **"New repository secret"**
   - Name: `RELEASE_TOKEN`
   - Value: Your PAT token
3. Update the workflow to use: `${{ secrets.RELEASE_TOKEN }}`

#### **Important Notes**
- **Workflow continues on release failure**: Even if releases can't be created, your packages are still built and available
- **Artifacts are always uploaded**: Check the **Actions** tab → workflow run → **Artifacts**
- **Permission fix is permanent**: Once you fix repository permissions, all future releases will work automatically

#### Manual Testing
1. Go to **Actions** tab in GitHub
2. Click **"Release Debian Package"** workflow
3. Click **"Run workflow"** button
4. This creates a test release for validation

### Option 2: Manual Installation from Source

1. Clone the repository or extract the source code.
2. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   
   ```bash
   python main.py
   ```
2. **Device Selection**: Connected devices will appear in the left sidebar. Click a device to select it.
   * If no devices are detected, the application will default to a "Mock Mode" for testing purposes.
3. **Application Launching**:
   * Select an application from the grid view.
   * Use the search bar at the top to filter the list.
   * The application will launch in a new window managed by `scrcpy`.

### Launch Modes

The application supports two launch configurations, selectable from the sidebar:

* **Tablet Mode (Default)**:
  * Resolution: 1280x800
  * Density: 160 DPI (mdpi)
  * Behavior: Forces applications into a tablet/desktop layout.
* **Phone Mode**:
  * Resolution: Native device resolution (fetched via `adb shell wm size`).
  * Density: Native device density (fetched via `adb shell wm density`).
  * Behavior: Mirrors the physical device's screen properties, suitable for apps that do not support tablet layouts.

## Technical Details

### Device Parsing

The application parses `adb devices -l` output using regular expressions to robustly identify device serials, models, and connection states.

### Resolution Handling

In "Phone Mode", the application queries the device for:

1. `Override size` (if set) or `Physical size`.
2. `Override density` (if set) or `Physical density`.

This ensures the virtual display accurately reflects the device's configuration.

## Troubleshooting

* **"Scrcpy not found"**: Ensure `scrcpy` is installed and the executable is in your system's `PATH`.
* **No Devices Detected**: Verify USB debugging is enabled on the Android device and authorized for the computer.
* **Application Closes Immediately**: Some applications may crash if they do not support the requested virtual display resolution or density. Try switching Launch Modes.