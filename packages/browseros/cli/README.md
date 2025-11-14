# BrowserOS Build System CLI

A modern, modular build system for BrowserOS/Chromium builds using a clean pipeline architecture.

## Installation

This project uses `uv` for dependency management. From the project root (`packages/browseros/`):

```bash
# Install dependencies
uv sync

# Run the CLI
uv run browseros-cli --help
```

## Usage

The CLI provides three main command groups:

### Build Commands

```bash
# Show all build commands
uv run browseros-cli build --help

# Run a complete build pipeline from config
uv run browseros-cli build run --config cli/config/example-pipeline.yaml --clean --build --package

# Execute a single module (for debugging)
uv run browseros-cli build step clean --dry-run
uv run browseros-cli build step setup-env --arch x64

# Run with specific flags
uv run browseros-cli build run --config path/to/config.yaml \
    --clean \
    --sync \
    --patch \
    --build \
    --sign \
    --package \
    --arch arm64 \
    --build-type release
```

### Development Commands

```bash
# Show dev commands
uv run browseros-cli dev --help

# Apply patches
uv run browseros-cli dev apply all
uv run browseros-cli dev apply feature <feature-name>
uv run browseros-cli dev apply selective patch1 patch2

# List available patches
uv run browseros-cli dev list

# Reset patch state
uv run browseros-cli dev reset
uv run browseros-cli dev reset --hard
```

### Release Commands

```bash
# Release automation (not yet implemented)
uv run browseros-cli release --help
```

## Architecture

```
cli/
├── orchestrator/        # Core orchestration logic
│   ├── module.py       # Base BuildModule interface
│   ├── context.py      # Build and Pipeline contexts
│   ├── loader.py       # YAML config loader
│   ├── plan.py         # Build plan creation
│   └── runner.py       # Pipeline execution
├── modules/            # Build modules
│   ├── common/         # clean, git operations
│   ├── setup/          # environment setup
│   ├── patches/        # patch application
│   ├── build/          # configure, compile
│   ├── sign/           # platform-specific signing
│   ├── package/        # packaging modules
│   ├── publish/        # upload modules
│   └── dev/            # development tools
└── config/             # Pipeline configurations
```

## Key Features

- **Modular Design**: Each build step is a self-contained module
- **YAML Configuration**: Define build pipelines in YAML
- **Platform Support**: Automatic platform-specific module resolution
- **Dry Run Mode**: Test pipelines without making changes
- **Event System**: Hook into build events for notifications
- **Environment Variables**: Support for `.env` files and variable expansion

## Pipeline Configuration Example

```yaml
pipelines:
  macos-release:
    matrix:
      architectures: [arm64, x64]
    env:
      GN_FLAGS: build/config/gn/flags.macos.release.gn
    steps:
      - clean
      - setup-env
      - git-sync
      - patch-chromium
      - configure: {gn_flags: "${GN_FLAGS}"}
      - build
      - sign-mac
      - package-mac
      - upload-gcs
```

## Module Development

To add a new module:

1. Create a module class inheriting from `BuildModule`
2. Implement `should_run()` and `run()` methods
3. Register it in `modules/registry.py`

Example:
```python
from cli.orchestrator.module import BuildModule, StepResult, Phase

class MyModule(BuildModule):
    def __init__(self):
        super().__init__()
        self.name = "my-module"
        self.phase = Phase.BUILD

    def should_run(self, ctx, step_cfg):
        return True

    def run(self, ctx, step_cfg):
        # Implementation
        return StepResult(success=True)
```

## Testing

```bash
# Test with dry-run
uv run browseros-cli build run --config example.yaml --dry-run

# Test individual modules
uv run browseros-cli build step <module-name> --dry-run
```

## Migration Notes

This is a new CLI system designed to replace the existing `build/build.py`. During migration:
- Both systems will coexist
- New modules wrap existing functionality
- Gradual migration preserves behavior
- No breaking changes to existing workflows