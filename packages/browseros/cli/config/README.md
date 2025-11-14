# BrowserOS Build Pipeline Configurations

This directory contains the official pipeline configurations for building BrowserOS across different platforms and scenarios.

## Production Releases

### `release-macos.yaml`
Full production pipeline for macOS releases:
- Builds both ARM64 and x64 architectures
- Creates universal binary
- Signs and notarizes the app
- Creates DMG installer
- Uploads to GCS

```bash
browseros build run \
  --config cli/config/release-macos.yaml \
  --chromium-src /path/to/chromium/src \
  --slack
```

### `release-windows.yaml`
Full production pipeline for Windows releases:
- Builds x64 architecture
- Signs with SSL.com eSigner
- Creates both installer and portable packages
- Uploads to GCS

```bash
browseros build run \
  --config cli/config/release-windows.yaml \
  --chromium-src C:/chromium/src \
  --slack
```

### `release-linux.yaml`
Full production pipeline for Linux releases:
- Builds x64 architecture
- Creates AppImage and .deb packages
- No signing required (typical for Linux)
- Uploads to GCS

```bash
browseros build run \
  --config cli/config/release-linux.yaml \
  --chromium-src /home/user/chromium/src \
  --slack
```

## Development Builds

### `debug.yaml`
Standard debug build for development:
- Single architecture for faster builds
- Includes all patches and resources
- No signing or packaging
- No notifications

```bash
browseros build run \
  --config cli/config/debug.yaml \
  --chromium-src /path/to/chromium/src
```

### `quick-build.yaml`
Minimal incremental build for rapid iteration:
- No clean, sync, or patches
- Just configure and build
- Assumes patches already applied
- Perfect for quick recompilation

```bash
browseros build run \
  --config cli/config/quick-build.yaml \
  --chromium-src /path/to/chromium/src
```

## Configuration Structure

Each configuration file contains:

### Pipeline Metadata
```yaml
name: pipeline-name
description: "Human-readable description"
```

### Build Matrix
```yaml
matrix:
  architectures: [arm64, x64]  # List of architectures to build
  universal: true              # Create universal binary (macOS only)
```

### Environment Variables
```yaml
env:
  GN_FLAGS: build/config/gn/flags.platform.type.gn
  PYTHONPATH: scripts
  CUSTOM_VAR: value
```

Variables can use `${VAR}` syntax for expansion.

### Build Steps
```yaml
steps:
  - module-name                 # Simple module
  - module-name:                # Module with parameters
      param: value
      when: "condition"         # Conditional execution
```

### Signing Configuration
```yaml
signing:
  require_env_vars:            # Required environment variables
    - VAR_NAME
  certificate_name: "Name"     # Default certificate name
```

### Notifications
```yaml
notifications:
  slack: true                  # Enable Slack notifications
```

## Module Execution Order

The standard order for a full release build:

1. **Preparation**
   - `clean` - Remove old build artifacts
   - `setup-env` - Configure environment variables
   - `git-sync` - Update Chromium source

2. **Patches**
   - `patch-chromium` - Apply Chromium file replacements
   - `patch-strings` - Apply string replacements
   - `patch-sparkle` - Setup Sparkle (macOS only)
   - `patch-apply` - Apply Git patches
   - `copy-resources` - Copy resource files

3. **Build**
   - `configure` - Configure with GN
   - `build` - Compile the browser

4. **Package & Sign**
   - `sign-{platform}` - Platform-specific signing
   - `package-{platform}` - Create distribution package
   - `sign-{platform}-universal` - Sign universal binary (macOS)

5. **Distribution**
   - `upload-gcs` - Upload to Google Cloud Storage

## Environment Variables

### Required for macOS Signing
- `MACOS_CERTIFICATE_NAME` - Developer ID certificate name
- `PROD_MACOS_NOTARIZATION_APPLE_ID` - Apple ID for notarization
- `PROD_MACOS_NOTARIZATION_TEAM_ID` - Apple Developer Team ID
- `PROD_MACOS_NOTARIZATION_PWD` - App-specific password

### Required for Windows Signing
- `CODE_SIGN_TOOL_PATH` - Path to SSL.com CodeSignTool
- `ESIGNER_USERNAME` - SSL.com username
- `ESIGNER_PASSWORD` - SSL.com password
- `ESIGNER_TOTP_SECRET` - TOTP secret for 2FA
- `ESIGNER_CREDENTIAL_ID` - eSigner credential ID

### Optional
- `SLACK_WEBHOOK_URL` - For Slack notifications
- `DEBUG_ARCH` - Override architecture for debug builds
- `PLATFORM` - Override platform detection

## Tips

### Partial Builds
Use verb flags to run only specific stages:

```bash
# Only clean and sync
browseros build run --config cli/config/debug.yaml --clean --sync

# Only build and package
browseros build run --config cli/config/debug.yaml --build --package

# Only patches
browseros build run --config cli/config/debug.yaml --patch --resources
```

### Dry Run
Test what would be executed without making changes:

```bash
browseros build run --config cli/config/release-macos.yaml --dry-run
```

### Custom Architectures
Override the architecture from command line:

```bash
browseros build run \
  --config cli/config/debug.yaml \
  --chromium-src /path/to/chromium/src \
  --arch arm64
```

### Skip Modules
Skip specific modules:

```bash
browseros build run \
  --config cli/config/release-macos.yaml \
  --skip upload-gcs \
  --skip sign-mac-universal
```