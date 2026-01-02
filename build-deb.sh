#!/bin/bash
# Build script for UMC Debian package
# This script can be used for local testing of the build process

set -e

echo "Installing build dependencies..."
sudo apt update
sudo apt install -y build-essential debhelper devscripts python3 python3-setuptools dh-python python3-all debhelper-compat

echo "Installing PySide6 dependencies..."
echo "Note: PySide6 packages are available in Debian testing/unstable repositories."
echo "If you're on an older Debian/Ubuntu version, PySide6 will be installed via pip."

# Update package lists first
sudo apt update

# Try to install PySide6 packages from apt (available in Debian testing/unstable)
if apt-cache show python3-pyside6.qtcore >/dev/null 2>&1; then
  echo "Installing PySide6 from apt repositories..."
  sudo apt install -y python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtwidgets python3-pyside6.qtqml python3-pyside6.qtquick python3-pyside6.qtnetwork python3-pyside6.qtopengl
else
  echo "PySide6 packages not available in apt repositories, installing via pip..."
  echo "This is normal on older Debian/Ubuntu versions."
  pip3 install PySide6
fi

echo "Installing Android tools..."
sudo apt install -y android-tools-adb

echo "Building Debian package..."
dpkg-buildpackage -us -uc -b

echo "Build completed! Files created:"
ls -la ../umc_*.deb ../umc_*.buildinfo ../umc_*.changes

echo ""
echo "To install the package locally:"
echo "sudo dpkg -i ../umc_*.deb"
echo "sudo apt install -f"