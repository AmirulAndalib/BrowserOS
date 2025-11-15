#!/usr/bin/env python3
"""Build CLI - Modular build system for BrowserOS"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

import typer

# Import common modules
from ..common.context import Context
from ..common.config import load_config, validate_required_envs
from ..common.pipeline import validate_pipeline, show_available_modules
from ..common.notify import (
    notify_pipeline_start,
    notify_pipeline_end,
    notify_pipeline_error,
    notify_module_start,
    notify_module_completion,
)
from ..common.module import ValidationError
from ..common.utils import (
    log_error,
    log_info,
    log_success,
    IS_MACOS,
    IS_WINDOWS,
    IS_LINUX,
    get_platform_arch,
)

# Import all module classes
from ..modules.setup.clean import CleanModule
from ..modules.setup.git import GitSetupModule, SparkleSetupModule
from ..modules.setup.configure import ConfigureModule
from ..modules.compile import CompileModule
from ..modules.patches.patches import PatchesModule
from ..modules.resources.chromium_replace import ChromiumReplaceModule
from ..modules.resources.string_replaces import StringReplacesModule
from ..modules.resources.resources import ResourcesModule
from ..modules.upload import GCSUploadModule

# Platform-specific modules (imported unconditionally - validation handles platform checks)
from ..modules.sign.macos import MacOSSignModule
from ..modules.sign.windows import WindowsSignModule
from ..modules.sign.linux import LinuxSignModule
from ..modules.package.macos import MacOSPackageModule
from ..modules.package.windows import WindowsPackageModule
from ..modules.package.linux import LinuxPackageModule

AVAILABLE_MODULES = {
    # Setup & Environment
    "clean": CleanModule,
    "git_setup": GitSetupModule,
    "sparkle_setup": SparkleSetupModule,
    "configure": ConfigureModule,
    # Patches & Resources
    "patches": PatchesModule,
    "chromium_replace": ChromiumReplaceModule,
    "string_replaces": StringReplacesModule,
    "resources": ResourcesModule,
    # Build
    "compile": CompileModule,
    # Sign (platform-specific, validated at runtime)
    "sign_macos": MacOSSignModule,
    "sign_windows": WindowsSignModule,
    "sign_linux": LinuxSignModule,
    # Package (platform-specific, validated at runtime)
    "package_macos": MacOSPackageModule,
    "package_windows": WindowsPackageModule,
    "package_linux": LinuxPackageModule,
    # Upload
    "upload_gcs": GCSUploadModule,
}


def _get_sign_module():
    """Get platform-specific sign module name"""
    if IS_MACOS():
        return "sign_macos"
    elif IS_WINDOWS():
        return "sign_windows"
    elif IS_LINUX():
        return "sign_linux"
    else:
        log_error("Unsupported platform for packaging")
        sys.exit(1)


def _get_package_module():
    """Get platform-specific package module name"""
    if IS_MACOS():
        return "package_macos"
    elif IS_WINDOWS():
        return "package_windows"
    elif IS_LINUX():
        return "package_linux"
    else:
        log_error("Unsupported platform for packaging")
        sys.exit(1)


# Fixed execution order - flags enable/disable phases, order is always the same
EXECUTION_ORDER = [
    # Phase 1: Setup & Clean
    ("setup", ["clean", "git_setup", "sparkle_setup"]),
    # Phase 2: Patches & Resources
    (
        "prep",
        ["resources", "chromium_replace", "string_replaces", "patches"],
    ),  # Phase 3: Configure & Build
    ("build", ["configure", "compile"]),
    # Phase 4: Code Signing (platform-aware)
    ("sign", [_get_sign_module()]),
    # Phase 5: Packaging (platform-aware)
    ("package", [_get_package_module()]),
    # Phase 6: Upload
    ("upload", ["upload_gcs"]),
]


def build_pipeline_from_flags(
    setup: bool = False,
    prep: bool = False,
    build: bool = False,
    sign: bool = False,
    package: bool = False,
    upload: bool = False,
) -> list[str]:
    """Build module pipeline from boolean flags

    Flags enable/disable phases, execution order is fixed.
    User can specify flags in any order - system enforces correct sequence.
    """
    pipeline = []
    enabled_phases = {
        "setup": setup,
        "prep": prep,
        "build": build,
        "sign": sign,
        "package": package,
        "upload": upload,
    }

    # Execute in predetermined order
    for phase_name, modules in EXECUTION_ORDER:
        if enabled_phases.get(phase_name, False):
            pipeline.extend(modules)

    return pipeline


def main(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Load configuration from YAML file",
        exists=True,
    ),
    modules: Optional[str] = typer.Option(
        None,
        "--modules",
        "-m",
        help="Comma-separated list of modules to run",
    ),
    list_modules: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List all available modules and exit",
    ),
    # Pipeline phase flags (auto-ordered execution)
    setup: bool = typer.Option(
        False,
        "--setup",
        help="Run setup phase (clean, git_setup, sparkle_setup)",
    ),
    prep: bool = typer.Option(
        False,
        "--prep",
        help="Run prep phase (patches, chromium_replace, string_replaces, resources)",
    ),
    build: bool = typer.Option(
        False,
        "--build",
        help="Run build phase (configure, compile)",
    ),
    sign: bool = typer.Option(
        False,
        "--sign",
        help="Run sign phase (platform-specific: sign_macos/windows/linux)",
    ),
    package: bool = typer.Option(
        False,
        "--package",
        help="Run package phase (platform-specific: package_macos/windows/linux)",
    ),
    upload: bool = typer.Option(
        False,
        "--upload",
        help="Run upload phase (upload_gcs)",
    ),
    # Global options that override config
    arch: Optional[str] = typer.Option(
        None,
        "--arch",
        "-a",
        help="Architecture (arm64, x64, universal)",
    ),
    build_type: str = typer.Option(
        "debug",
        "--build-type",
        "-t",
        help="Build type (debug or release)",
    ),
    chromium_src: Optional[Path] = typer.Option(
        None,
        "--chromium-src",
        "-S",
        help="Path to Chromium source directory",
    ),
):
    """BrowserOS Build System - Modular pipeline executor

    Build BrowserOS using phase flags (auto-ordered), explicit modules, or configs.

    \b
    Phase Flags (Recommended - Auto-Ordered):
      browseros build --setup --build --sign --package
      browseros build --build --sign           # Skip setup
      browseros build --package --sign         # Flags work in any order!

    \b
    Explicit Modules (Power Users):
      browseros build --modules clean,compile,sign_macos

    \b
    Config Files (CI/CD):
      browseros build --config release.yaml --arch arm64

    \b
    List Available:
      browseros build --list                   # Show all modules and phases

    Note: Phase flags always execute in correct order regardless of how you write them.
          --sign and --package auto-select platform (macos/windows/linux)
    """

    # Handle --list flag
    if list_modules:
        show_available_modules(AVAILABLE_MODULES)
        return

    # Check for mutually exclusive options
    has_config = config is not None
    has_modules = modules is not None
    has_flags = any([setup, prep, build, sign, package, upload])

    options_provided = sum([has_config, has_modules, has_flags])

    if options_provided == 0:
        typer.echo(
            "Error: Specify --config, --modules, or phase flags (--setup, --build, etc.)\n"
        )
        typer.echo("Use --help for usage information")
        typer.echo("Use --list to see available modules")
        raise typer.Exit(1)

    if options_provided > 1:
        log_error("Specify only ONE of: --config, --modules, or phase flags")
        log_error("Examples:")
        log_error("  browseros build --setup --build --sign")
        log_error("  browseros build --modules clean,compile")
        log_error("  browseros build --config release.yaml")
        raise typer.Exit(1)

    log_info("🚀 BrowserOS Build System")
    log_info("=" * 70)

    root_dir = Path(__file__).parent.parent.parent
    pipeline = []
    required_envs = []
    chromium_src_path = chromium_src
    architecture = arch

    if config:
        # Load from YAML config
        config_data = load_config(config)

        # Extract pipeline
        if "modules" not in config_data:
            log_error("Config file must contain 'modules' key")
            raise typer.Exit(1)

        pipeline = config_data["modules"]

        # Extract required environment variables
        required_envs = config_data.get("required_envs", [])

        # Extract build settings (CLI args override)
        if "build" in config_data:
            if not architecture:
                architecture = config_data["build"].get("arch") or config_data[
                    "build"
                ].get("architecture")
            if not chromium_src_path and "chromium_src" in config_data["build"]:
                chromium_src_path = Path(config_data["build"]["chromium_src"])
            if "type" in config_data["build"]:
                build_type = config_data["build"]["type"]

    elif modules:
        # Parse module list from CLI
        pipeline = [m.strip() for m in modules.split(",")]

    elif has_flags:
        # Build pipeline from phase flags (auto-ordered)
        pipeline = build_pipeline_from_flags(
            setup=setup,
            prep=prep,
            build=build,
            sign=sign,
            package=package,
            upload=upload,
        )

        # Show what will execute
        log_info("\n📋 Execution Plan (auto-ordered):")
        log_info("-" * 70)
        phase_names = []
        if setup:
            phase_names.append("setup")
        if prep:
            phase_names.append("prep")
        if build:
            phase_names.append("build")
        if sign:
            phase_names.append(f"sign (→ {_get_sign_module()})")
        if package:
            phase_names.append(f"package (→ {_get_package_module()})")
        if upload:
            phase_names.append("upload")

        for phase_name in phase_names:
            log_info(f"  ✓ {phase_name}")

        log_info(f"\n  Pipeline: {' → '.join(pipeline)}")
        log_info("-" * 70)

    # Validate required environment variables
    if required_envs:
        validate_required_envs(required_envs)

    # Validate pipeline
    validate_pipeline(pipeline, AVAILABLE_MODULES)

    # Set defaults
    if not architecture:
        architecture = get_platform_arch()
        log_info(f"Using platform default architecture: {architecture}")

    # Validate chromium_src
    if not chromium_src_path:
        # Try environment variable
        chromium_src_env = os.environ.get("CHROMIUM_SRC")
        if chromium_src_env:
            chromium_src_path = Path(chromium_src_env)
        else:
            log_error("Chromium source directory required!")
            log_error(
                "Provide via --chromium-src, config file, or CHROMIUM_SRC environment variable"
            )
            raise typer.Exit(1)

    if not chromium_src_path.exists():
        log_error(f"Chromium source directory does not exist: {chromium_src_path}")
        raise typer.Exit(1)

    # Set Windows-specific environment
    if IS_WINDOWS():
        os.environ["DEPOT_TOOLS_WIN_TOOLCHAIN"] = "0"
        log_info("Set DEPOT_TOOLS_WIN_TOOLCHAIN=0 for Windows build")

    ctx = Context(
        root_dir=root_dir,
        chromium_src=chromium_src_path,
        architecture=architecture,
        build_type=build_type,
    )

    log_info(f"📍 Root: {root_dir}")
    log_info(f"📍 Chromium: {ctx.chromium_src}")
    log_info(f"📍 Architecture: {ctx.architecture}")
    log_info(f"📍 Build type: {ctx.build_type}")
    log_info(f"📍 Output: {ctx.out_dir}")
    log_info(f"📍 Pipeline: {' → '.join(pipeline)}")
    log_info("=" * 70)

    start_time = time.time()
    notify_pipeline_start("build", pipeline)

    try:
        for module_name in pipeline:
            log_info(f"\n{'='*70}")
            log_info(f"🔧 Running module: {module_name}")
            log_info(f"{'='*70}")

            module_class = AVAILABLE_MODULES[module_name]
            module = module_class()

            # Notify module start
            notify_module_start(module_name)
            module_start = time.time()

            # Validate right before executing
            try:
                module.validate(ctx)
            except ValidationError as e:
                log_error(f"Validation failed for {module_name}: {e}")
                notify_pipeline_error("build", f"{module_name} validation failed: {e}")
                raise typer.Exit(1)

            # Execute
            try:
                module.execute(ctx)
                module_duration = time.time() - module_start
                notify_module_completion(module_name, module_duration)
                log_success(f"Module {module_name} completed in {module_duration:.1f}s")
            except Exception as e:
                log_error(f"Module {module_name} failed: {e}")
                notify_pipeline_error("build", f"{module_name} failed: {e}")
                raise typer.Exit(1)

        # Pipeline complete
        duration = time.time() - start_time
        mins = int(duration / 60)
        secs = int(duration % 60)

        log_info("\n" + "=" * 70)
        log_success(f"✅ Pipeline completed successfully in {mins}m {secs}s")
        log_info("=" * 70)

        notify_pipeline_end("build", duration)

    except KeyboardInterrupt:
        log_error("\n❌ Pipeline interrupted")
        notify_pipeline_error("build", "Interrupted by user")
        raise typer.Exit(130)
    except Exception as e:
        log_error(f"\n❌ Pipeline failed: {e}")
        notify_pipeline_error("build", str(e))
        raise typer.Exit(1)
