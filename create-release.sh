#!/bin/bash
# Script to create a new release
# Usage: ./create-release.sh [version]

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.1"
    exit 1
fi

VERSION=$1
TAG="v$VERSION"

echo "Creating release $TAG..."

# Check if tag already exists
if git tag -l | grep -q "^$TAG$"; then
    echo "Tag $TAG already exists!"
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "Working directory is not clean. Please commit or stash changes."
    exit 1
fi

# Create and push tag
echo "Creating tag $TAG..."
git tag "$TAG"
git push origin "$TAG"

echo ""
echo "✅ Tagged release $TAG created!"
echo ""
echo "GitHub Actions will now:"
echo "1. Build the Debian package"
echo "2. Create an official GitHub release"
echo "3. Attach the .deb package with auto-generated release notes"
echo ""
echo "Note: Nightly releases are created automatically on every push to main/master."
echo "Check the Actions tab and Releases page to monitor progress."