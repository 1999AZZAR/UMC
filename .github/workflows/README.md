# CI/CD Workflows

This directory contains GitHub Actions workflows for automated building, testing, and releasing of Debian packages.

## Workflows

### Release Debian Package (`release.yml`)

Automatically builds and releases Debian packages for the Unified Mobile Controller (UMC).

#### Triggers

- **Push to main/master**: Creates nightly releases automatically
- **Version tags (v*)**: Creates official releases
- **Pull Requests**: Builds and tests packages

#### What it does

1. **Build Process**:
   - Installs build dependencies (debhelper, python3, etc.)
   - Installs PySide6 (from apt if available, pip fallback)
   - Installs Android tools (adb)
   - Builds `.deb` package using `dpkg-buildpackage`

2. **Release Creation**:
   - **Nightly releases**: Created automatically on every push to main/master
   - **Official releases**: Created when version tags are pushed
   - Packages attached as release assets

3. **Artifact Upload**:
   - All build artifacts uploaded to GitHub Actions
   - Available for download even if release creation fails

#### Release Types

| Trigger | Release Type | Tag Format | Notes |
|---------|-------------|------------|-------|
| Push to main/master | Nightly (pre-release) | `nightly-{run}-{attempt}` | Automatic |
| Version tag | Official (stable) | Uses tag name | Manual trigger |
| Pull Request | Build Only | None | Testing only |

#### Configuration

**Required Repository Settings**:
1. Go to **Settings** → **Actions** → **General**
2. Set **"Workflow permissions"** to **"Read and write permissions"**
3. Check **"Allow GitHub Actions to create and approve pull requests"**

**Optional: Personal Access Token**
- If default permissions don't work, create a PAT with `repo` scope
- Add as `RELEASE_TOKEN` secret in repository settings
- Workflow will automatically use it

#### Troubleshooting

**No Releases Being Created**:

1. **Check Branch Name**:
   - Releases only create on `main` or `master` branch pushes
   - Verify you're pushing to the correct branch
   - Check workflow logs for: `🎯 Branch: refs/heads/main`

2. **Verify Repository Permissions**:
   - Go to **Settings** → **Actions** → **General**
   - **Workflow permissions**: Must be **"Read and write permissions"**
   - **Check**: "Allow GitHub Actions to create and approve pull requests"
   - **Save** and test with a new push

3. **Check Workflow Status**:
   - Go to **Actions** tab
   - Find the latest workflow run
   - Look for the "Create Release" step
   - Check if it says "Skipped" or ran successfully

**403 Forbidden Error**:
- Same as repository permissions above
- Or use `RELEASE_TOKEN` secret (see below)

**Alternative: Personal Access Token**
If repository permissions can't be changed:
1. Create PAT at https://github.com/settings/tokens (classic)
2. Select `repo` scope
3. Add as `RELEASE_TOKEN` secret:
   - Settings → Secrets and variables → Actions
   - Name: `RELEASE_TOKEN`
   - Value: Your PAT token
4. Workflow will automatically use it

**Build Failures**:
- Check build logs in Actions tab
- Verify all dependencies are available
- Test locally with `./build-deb.sh`

**Missing Artifacts**:
- Even if releases fail, artifacts are always uploaded
- Download from Actions → Workflow run → Artifacts
- Look for `debian-package` artifact

**Debug Steps**:
1. Push a commit to main/master
2. Check Actions tab for workflow run
3. Look for "Debug Branch Info" step output
4. Verify "Create Release" step doesn't say "skipped"

#### Manual Testing

To test the workflow manually:
1. Go to **Actions** tab
2. Select **"Release Debian Package"** workflow
3. Click **"Run workflow"**
4. Choose branch and run

#### Local Development

For local testing of the build process:
```bash
# Test the build script
./build-deb.sh

# Check created packages
ls -la ../*.deb
```

#### File Structure

```
.github/workflows/
├── release.yml          # Main CI/CD workflow
└── README.md           # This documentation
```

## Scripts

- `build-deb.sh`: Local build script for testing
- `create-release.sh`: Helper script for creating version tags

## Support

If workflows fail:
1. Check the Actions tab for detailed logs
2. Verify repository permissions
3. Test locally with build scripts
4. Check this documentation for common issues