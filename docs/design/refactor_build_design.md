# Build System Refactor Design

## Goals
- Decouple orchestration from platform logic so we can describe platform/OS‑specific pipelines in data (YAML) instead of hard‑coded `if` trees inside `build/build.py`.
- Standardize module interfaces (sign, package, upload…) so future steps (SSH, artifact fetch, custom signing chains) can plug into the same framework and override behavior per OS.
- Keep the system invokable both from CLI and from configs/GitHub Actions, sharing the same plan builder.
- Improve testability with unit coverage for individual modules plus integration tests for plan assembly/dry runs.
- Preserve today’s capabilities (clean, git setup, patches, signing, packaging, uploads, utility subcommands) while making it easier to reorder/duplicate steps (e.g., Windows sign→package→sign flow vs macOS package→sign).
- Enforce single-responsibility modules: instead of bolting more flags into `sign`, create focused modules (e.g., `sign-browseros-server-win`) that can be composed in the plan.

## Current Pain Points
- `build/build.py` mixes config parsing, CLI handling, Slack/GCS notifications, and every build step, making it brittle to change and hard to test.
- Modules are plain functions with no metadata: the orchestrator cannot reason about required artifacts, supported platforms, or whether a module can be repeated or dry-run.
- Signing and packaging order is hard-coded per OS, preventing new sequences like “sign binaries before packaging, re-sign installer after packaging”.
- CLI-only commands (merge, upload-dist, add-replace, string-replace) sit inside the same file and share global flags, blurring dev/build concerns.
- No systematic tests or dry-run mode; regressions show up only when a full build is attempted.

## Proposed Architecture

```
build/
├── cli/
│   ├── build.py         # Typer CLI -> plan builder -> runner
│   ├── dev.py           # Dev CLI (existing) plugged into shared helpers
│   └── release.py       # Placeholder for future automation
├── orchestrator/
│   ├── context.py       # BuildContext + PipelineContext (shared)
│   ├── module.py        # BuildModule base class + registry
│   ├── plan.py          # Plan builder from YAML/CLI, dependency checks
│   ├── loader.py        # Config parsing, environment overrides
│   └── runner.py        # Executes ordered steps, handles notifications
└── modules/
    ├── common/          # clean, git, resources, copy files
    ├── setup/           # setup-env (centralized environment configuration)
    ├── patches/         # patch-chromium, patch-strings, patch-sparkle, patch-apply
    ├── build/           # configure, compile, postbuild
    ├── sign/            # sign-mac, sign-windows, sign-linux + specialized modules
    ├── package/         # package-mac, package-windows, package-linux (+ universal variants)
    ├── publish/         # upload-gcs today, future upload targets (AWS, SSH, etc.)
    └── dev/             # dev CLI helpers with sub-modules for complex operations
        └── apply/       # feature.py, selective.py, overwrite.py when needed
```

### CLI Layout (Typer)

Expose a single executable named `browseros` with three sub-apps using Typer's hierarchical command structure:

```python
# build/cli/__init__.py
app = typer.Typer(help="BrowserOS Build System")
app.add_typer(build_app, name="build", help="Production build orchestration")
app.add_typer(dev_app, name="dev", help="Development tools and patch management")
app.add_typer(release_app, name="release", help="Release automation")

# build/cli/dev.py - nested sub-apps for complex commands
dev_app = typer.Typer()
apply_app = typer.Typer(help="Apply patches and modifications")
dev_app.add_typer(apply_app, name="apply")

@apply_app.command("feature")
def apply_feature(
    name: str = typer.Argument(..., help="Feature name from features.yaml"),
    commit: bool = typer.Option(False, "--commit", help="Auto-commit after applying")
):
    """Apply patches for a specific feature defined in features.yaml"""
    ...

@apply_app.command("selective")
def apply_selective(
    patches: List[str] = typer.Argument(..., help="Specific patch IDs to apply")
):
    """Apply only selected patches by ID"""
    ...
```

Command hierarchy:
```
browseros
├── build        # production build orchestration
│   ├── run      # main pipeline runner
│   ├── step     # single module execution
│   ├── merge    # utility commands
│   ├── add-replace
│   └── string-replace
├── dev          # development tools
│   ├── apply    # patch application (sub-app)
│   │   ├── all      # apply all patches (default)
│   │   ├── feature  # apply by feature name
│   │   ├── selective # apply specific patches
│   │   └── overwrite # force overwrite existing
│   ├── list     # list available patches
│   └── reset    # reset patch state
└── release      # release automation
```

Examples:

- `browseros build run --config build/config/pipelines/macos-release.yaml --clean --sync --patch --resources --build --sign --package --upload --arch arm64 --build-type release --slack`
- `browseros build run --config … --build --package --skip upload-gcs`
- `browseros build step clean --arch x64` (execute one module for debugging)
- `browseros build merge …`, `browseros build add-replace …`, `browseros build string-replace …`, `browseros build upload-dist …` stay as dedicated commands under the same Typer app.

Key points:
- Boolean verb flags (`--clean`, `--sync`, `--patch`, `--resources`, `--build`, `--sign`, `--package`, `--upload`) match today's UX; internally they map to module names for the plan builder. `--patch` covers replacements + Sparkle + patch application, while `--resources` lets us run copy-only workflows.
- Advanced users can still specify `--steps`, `--only`, or `--skip` using module names, but they are optional.
- CLI loads `.env` (same as current `build/build.py:14-33`) so secrets injected via env Just Work™.
- **No auto-detection**: Always require explicit `--config` to specify pipeline YAML. No magic resolution based on OS/arch.
- Legacy `build/build.py` becomes a shim that invokes `browseros build run` until we delete it.

### BuildModule Interface

```python
class BuildModule(ABC):
    name: str
    phase: str                      # e.g. prepare/build/sign/package/publish
    default_order: int
    requires: set[str]              # artifact ids (e.g. {"app:browseros"})
    provides: set[str]              # artifact ids this step produces
    supported_platforms: set[str]   # {"macos", "linux", "win"}
    supports_dry_run: bool = False

    def should_run(self, ctx: BuildContext, step_cfg: dict) -> bool: ...
    def run(self, ctx: BuildContext, step_cfg: dict) -> StepResult: ...
```

### Module Organization

Simple explicit module mapping:

```python
# modules/registry.py - just a simple dict
from modules.common.clean import CleanModule
from modules.setup.env import SetupEnvModule
from modules.patches.chromium import PatchChromiumModule
from modules.patches.strings import PatchStringsModule
from modules.sign.mac import SignMacModule
from modules.sign.windows import SignWindowsModule

# Explicit mapping - clear and debuggable
MODULES = {
    "clean": CleanModule,
    "setup-env": SetupEnvModule,
    "patch-chromium": PatchChromiumModule,
    "patch-strings": PatchStringsModule,
    "sign-mac": SignMacModule,
    "sign-mac-browseros-resources": SignMacBrowserOSResourcesModule,
    "sign-windows": SignWindowsModule,
    "sign-windows-browseros-resources": SignWindowsBrowserOSResourcesModule,
    # ... etc
}

def get_module(name: str) -> BuildModule:
    """Get module by name"""
    if name not in MODULES:
        raise ValueError(f"Unknown module: {name}")
    return MODULES[name]()
```

For dev modules with sub-commands, keep it simple:

```python
# modules/dev/apply.py - different functions for different behaviors
def apply_all(ctx: BuildContext) -> StepResult:
    """Apply all patches"""
    ...

def apply_feature(ctx: BuildContext, feature_name: str) -> StepResult:
    """Apply patches for specific feature"""
    ...

def apply_selective(ctx: BuildContext, patch_ids: List[str]) -> StepResult:
    """Apply only selected patches"""
    ...

# CLI just calls the right function based on command
@dev_app.command("apply")
def apply_patches(
    feature: Optional[str] = typer.Option(None, "--feature"),
    patches: Optional[List[str]] = typer.Option(None, "--patches"),
):
    if feature:
        result = apply_feature(ctx, feature)
    elif patches:
        result = apply_selective(ctx, patches)
    else:
        result = apply_all(ctx)
```

Benefits:
- No magic - explicit imports and mappings
- Easy to debug (just follow the imports)
- Clear what modules exist (look at the dict)
- Industry standard approach (see Click apps, FastAPI, etc.)

### Context Objects
- `PipelineContext`: root path, config hash, notifications, Slack client, env overrides shared across all builds.
- `BuildContext`: per-arch/per-plan execution state (architecture, build_type, flags), plus:
  - `artifacts: dict[str, Any]` for produced outputs (paths, metadata tokens).
  - `metadata: dict[str, Any]` for cross-step data (certificate names, build numbers).
  - `env_overrides` / resolved environment for modules to consume.

### Pipeline Configuration

New YAML schema (`build/config/pipelines/*.yaml`):

```yaml
pipelines:
  macos-release:
    matrix:
      architectures: [arm64, x64]
      universal: true
    env:
      GN_FLAGS: build/config/gn/flags.macos.release.gn
    steps:
      - clean
      - setup-env
      - git-sync
      - patch-chromium
      - patch-strings
      - patch-sparkle
      - patch-apply
      - copy-resources
      - configure: {gn_flags: "${GN_FLAGS}"}
      - build
      - sign-mac
      - sign-mac-browseros-resources   # specialized module for extra binaries/resources
      - package-mac
      - sign-mac-universal: {when: arch == "universal"}
      - upload-gcs

  windows-release:
    matrix:
      architectures: [x64]
    steps:
      - clean
      - setup-env
      - git-sync
      - patch-chromium
      - patch-strings
      - patch-apply
      - configure
      - build
      - sign-windows
      - sign-windows-browseros-resources   # specialized module for extra binaries/resources
      - package-windows
      - sign-windows-installer
      - upload-gcs
```

- Each list item references a module by name; dict values pass parameters.
- Plan builder merges CLI overrides, resolves `${VAR}` placeholders from env/CLI, and treats upload stages as pluggable modules (`upload-gcs` today, `upload-aws` later) so switching providers is a YAML change, not an orchestrator change.
- Steps can repeat (`sign-mac` twice) or represent specialized modules (e.g., `sign-windows-browseros-server`).
- `when:` expressions use a minimal DSL: equality/inequality and `in`/`not in` against `{arch, os, build_type}` plus optional metadata, matching the filters already familiar from `build/config/copy_resources.yaml`. No arbitrary `eval`.

### CLI & Orchestrator Responsibilities
- `build/cli/build.py`: Typer command definitions (run, step, merge, add-replace, string-replace, upload-dist) + shared options (config, arch, build type, dry-run, slack).
- `build/orchestrator/loader.py`: parse YAML, expand matrices, resolve env vars, apply CLI overrides, filter by verb flags (`--build`, `--sign`, …).
- `build/orchestrator/plan.py`: validate dependencies via `requires`/`provides`, detect missing artifacts before execution, and emit ordered plan.
- `build/orchestrator/runner.py`: execute plan, emit lifecycle events consumed by Slack/GitHub observers, support dry-run (skip modules that don’t opt in with a log message).
- Notifications hook into runner events; modules never call Slack directly.

### Testing Strategy
1. **Unit tests for modules**: run `run()` with fake contexts, stub `run_command` to assert shell usage.
2. **Plan builder tests**: matrix expansion, CLI overrides, `when` evaluation, duplicate module handling, dependency failures.
3. **Runner dry-run tests**: ensure ordering and event hooks fire without touching real Chromium sources.
4. **Golden plan snapshots**: canonical configs (macOS, Windows, Linux) to catch accidental reordering.
5. **CLI tests**: Typer command invocation verifying flag combinations translate to the expected modules.
6. **CI wiring**: `python -m pytest build/tests` + optional `browseros build run … --dry-run` smoke job per PR.

### Detailed Migration Plan (logic-parity first)

1. **Scaffold orchestration layer**
   - Create `build/cli`, `build/orchestrator`, `build/modules/*` directories.
   - Add Typer-based `browseros build` CLI that still calls existing `build_main` (parity guarantee).
   - Introduce `BuildModule`, registry, `PipelineContext`, `PlanBuilder`, and skeleton tests.

2. **Wrap foundational modules** (keep implementations unchanged, just wrap):
   1. `clean`
   2. `setup-env` (centralize all environment setup from `build/build.py:400-450`)
   3. `git-sync` (`setup_git`)
   4. `patch-chromium` (wraps `replace_chromium_files`)
   5. `patch-strings` (wraps `apply_string_replacements`)
   6. `patch-sparkle` (wraps `setup_sparkle`)
   7. `patch-apply` (wraps `apply_patches`)
   8. `copy-resources`
   9. `configure`
   10. `build`
   11. `upload-gcs` (wrapper around existing uploader; lives under `modules/publish/` so future `upload-aws` slots in beside it)

3. **Bring up plan builder + runner**
   - Load YAML into module list, apply CLI verb filters, execute modules through the runner (still one architecture initially).
   - Add dry-run support and runner events (start/success/fail) feeding Slack observer.

4. **Translate configs**
   - Mirror current configs into `build/config/pipelines/*.yaml` with the same sequences and flags.
   - Provide compatibility layer that converts old `steps.*` booleans into module lists so we can keep both configs during rollout.

5. **Port platform-specific modules**
   - macOS: baseline `sign-mac` + `package-mac` (DMG + notarization), `sign-mac-browseros-resources` for extra binaries/resources, `sign-mac-universal`, `package-mac-universal`.
   - Windows: baseline `sign-windows`, `package-windows`, `sign-windows-installer`, plus `sign-windows-browseros-resources` for extra binaries/resources.
   - Linux: `sign-linux`, `package-linux` (AppImage/.deb).
   - Publish: keep `upload-gcs` as-is but house it in `modules/publish/` so additional upload targets (AWS, SCP) can be added as parallel modules without touching the runner.
   - Baseline modules accept simple parameters (e.g., `targets`, `mode`). Anything bespoke becomes its own module wrapping shared helpers (single responsibility preserved).

6. **Switch CLI to new runner**
   - Tie `browseros build run` directly into orchestrator plan execution; keep `build/build.py` as a temporary shim.
   - Update docs & scripts to call `browseros build run`.

7. **Remove legacy orchestrator**
   - Delete `build_main`, unused helpers, and `click` CLI once parity is proven across all platforms.

8. **Harden with CI**
   - Add plan-builder golden tests, runner dry-run tests, and module unit tests into GitHub Actions.
   - Optional: nightly smoke build using the new CLI.

Each migration step lands with the same behavior compared to today (e.g., run “clean only” before/after) to guarantee we’re not changing logic while refactoring.

### Key Design Decisions

- **Module ordering**: Rely on pipeline author to specify correct order in YAML. No automatic dependency resolution based on artifacts (KISS principle).
- **Error recovery**: No built-in resume/checkpoint. Failures require full rebuild or manual CLI intervention (`browseros build step <module>`).
- **Config selection**: Always explicit via `--config`. No auto-detection based on OS/arch.
- **`when` expressions**: Simple equality/inequality + `in`/`not in` against `{arch, os, build_type}` (and explicit metadata keys). Anything more complex becomes its own module.
- **Secrets**: Sourced exclusively from environment variables (CI secrets, local `.env`); YAML references `${VAR}` at load time.
- **Legacy entry**: No permanent fallback. `build/build.py` will only be a shim during migration, then removed.
- **Dev modules**: Separate module set under `modules/dev/`. Complex operations like `apply` expand into submodules (`apply/feature.py`, `apply/selective.py`) when needed.
- **VM orchestration**: Keep VM lifecycle (start/stop) in GitHub Actions YAML initially. Reserve artifact namespace (`vm:*`) for future integration if needed.
