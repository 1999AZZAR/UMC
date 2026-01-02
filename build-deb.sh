#!/bin/bash
# Build script for UMC Debian package
# This script can be used for local testing of the build process

set -e

echo "Installing build dependencies..."
sudo apt update
sudo apt install -y build-essential debhelper devscripts python3 python3-setuptools dh-python python3-all

echo "Installing PySide6 dependencies..."
sudo apt install -y libpyside6-py3-6.8 libshiboken6-py3-6.8 python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtwidgets python3-pyside6.qtqml python3-pyside6.qtquick python3-pyside6.qtnetwork python3-pyside6.qtopengl

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