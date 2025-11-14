# Usage Examples for New Build System

## Basic Usage

### Full Pipeline Execution
```bash
# Run complete macOS release pipeline
browseros build run \
  --config build/config/pipelines/macos-release.yaml \
  --chromium-src /path/to/chromium/src \
  --arch arm64 \
  --slack

# Run Windows release build
browseros build run \
  --config build/config/pipelines/windows-release.yaml \
  --chromium-src C:/chromium/src \
  --build-type release

# Run Linux debug build
browseros build run \
  --config build/config/pipelines/linux-release.yaml \
  --chromium-src /home/user/chromium/src \
  --build-type debug
```

### Using Verb Flags (Backward Compatible)
```bash
# Clean and sync only
browseros build run \
  --config build/config/pipelines/macos-release.yaml \
  --chromium-src /path/to/chromium/src \
  --clean --sync

# Build and package only (no upload)
browseros build run \
  --config build/config/pipelines/macos-release.yaml \
  --chromium-src /path/to/chromium/src \
  --build --package

# Patches and resources only
browseros build run \
  --config build/config/pipelines/macos-release.yaml \
  --chromium-src /path/to/chromium/src \
  --patch --resources
```

### Explicit Module Selection
```bash
# Run specific modules only
browseros build run \
  --config build/config/pipelines/macos-release.yaml \
  --chromium-src /path/to/chromium/src \
  --only clean git-sync patch-chromium

# Skip certain modules
browseros build run \
  --config build/config/pipelines/macos-release.yaml \
  --chromium-src /path/to/chromium/src \
  --skip upload-gcs
```

### Dry Run Mode
```bash
# Test what would be executed without making changes
browseros build run \
  --config build/config/pipelines/macos-release.yaml \
  --chromium-src /path/to/chromium/src \
  --dry-run
```

### Single Module Execution (Debugging)
```bash
# Run just one module for testing
browseros build step clean \
  --chromium-src /path/to/chromium/src \
  --arch x64

browseros build step patch-chromium \
  --chromium-src /path/to/chromium/src \
  --build-type release
```

## Using Old Config Files

The new system is backward compatible with existing configs:

```bash
# Old configs still work
browseros build run \
  --config build/config/release.macos.yaml \
  --chromium-src /path/to/chromium/src

# Boolean step flags are auto-converted to module lists
# steps: {clean: true, build: true} → ["clean", "configure", "build"]
```

## Pipeline Configuration

### New Pipeline Format
```yaml
pipelines:
  my-custom-pipeline:
    description: "Custom build pipeline"
    matrix:
      architectures: [x64]

    env:
      GN_FLAGS: build/config/gn/flags.custom.gn

    steps:
      - clean
      - setup-env:
          check_signing: false  # Don't check signing env
      - git-sync
      - patch-chromium
      - configure:
          gn_flags: "${GN_FLAGS}"
      - build
      - package-mac:
          when: "platform == 'macos'"
      - package-windows:
          when: "platform == 'windows'"
      - upload-gcs:
          when: "build_type == 'release'"
```

### Module Parameters
```yaml
steps:
  # Simple module (no parameters)
  - clean

  # Module with inline parameters
  - setup-env:
      check_signing: true

  # Module with conditional execution
  - sign-mac-universal:
      when: "arch == 'universal'"

  # Module with multiple parameters
  - package-windows:
      create_installer: true
      create_portable: true
      sign_installer: true
```

## Environment Variables

### Required for macOS Signing
```bash
export MACOS_CERTIFICATE_NAME="Developer ID Application: Your Company"
export PROD_MACOS_NOTARIZATION_APPLE_ID="your@email.com"
export PROD_MACOS_NOTARIZATION_TEAM_ID="TEAMID123"
export PROD_MACOS_NOTARIZATION_PWD="app-specific-password"
```

### Required for Windows Signing (SSL.com eSigner)
```bash
export CODE_SIGN_TOOL_PATH="/path/to/CodeSignTool"
export ESIGNER_USERNAME="your-username"
export ESIGNER_PASSWORD="your-password"
export ESIGNER_TOTP_SECRET="your-totp-secret"
export ESIGNER_CREDENTIAL_ID="your-credential-id"
```

### For Slack Notifications
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

## Debugging

### Verbose Output
```bash
# See which modules are being skipped and why
browseros build run \
  --config build/config/pipelines/macos-release.yaml \
  --chromium-src /path/to/chromium/src \
  --verbose
```

### Test Plan Building
```bash
# Run the orchestrator test script
python3 cli/test_orchestrator.py

# Test specific modules
python3 cli/test_modules.py
```

### Check Module Registry
```python
from cli.modules.registry import list_modules

# See all registered modules
for name, module_class in list_modules().items():
    print(f"{name}: {module_class}")
```

## Migration from Old System

### Old Command
```bash
python build/build.py \
  --config build/config/release.macos.yaml \
  --chromium-src /path/to/chromium/src \
  --clean --sync --patch --build --sign --package
```

### New Command (Same Result)
```bash
browseros build run \
  --config build/config/release.macos.yaml \
  --chromium-src /path/to/chromium/src \
  --clean --sync --patch --build --sign --package
```

Or use the new pipeline config:
```bash
browseros build run \
  --config build/config/pipelines/macos-release.yaml \
  --chromium-src /path/to/chromium/src
```