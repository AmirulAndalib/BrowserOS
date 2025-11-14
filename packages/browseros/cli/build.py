"""Build orchestration CLI commands."""

import typer
from pathlib import Path
from typing import Optional, List
from cli.orchestrator.context import PipelineContext, BuildContext
from cli.orchestrator.loader import ConfigLoader
from cli.orchestrator.plan import PlanBuilder
from cli.orchestrator.runner import PipelineRunner


app = typer.Typer(no_args_is_help=True)


@app.command("run")
def run(
    config: Path = typer.Option(..., "--config", help="Path to pipeline YAML config"),
    chromium_src: Optional[Path] = typer.Option(None, "--chromium-src", "-S", help="Path to Chromium source directory"),
    arch: Optional[str] = typer.Option(None, "--arch", help="Architecture (x64, arm64)"),
    build_type: Optional[str] = typer.Option("release", "--build-type", help="Build type (release, debug)"),

    # Verb flags for backward compatibility
    clean: bool = typer.Option(False, "--clean", help="Run clean step"),
    sync: bool = typer.Option(False, "--sync", help="Run git sync"),
    patch: bool = typer.Option(False, "--patch", help="Apply patches"),
    resources: bool = typer.Option(False, "--resources", help="Copy resources"),
    build: bool = typer.Option(False, "--build", help="Run build"),
    sign: bool = typer.Option(False, "--sign", help="Sign binaries"),
    package: bool = typer.Option(False, "--package", help="Create packages"),
    upload: bool = typer.Option(False, "--upload", help="Upload artifacts"),

    # Advanced options
    steps: Optional[List[str]] = typer.Option(None, "--steps", help="Explicit module names to run"),
    skip: Optional[List[str]] = typer.Option(None, "--skip", help="Module names to skip"),
    only: Optional[List[str]] = typer.Option(None, "--only", help="Only run these modules"),

    # Environment
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without changes"),
    slack: bool = typer.Option(False, "--slack", help="Enable Slack notifications"),
):
    """Run a build pipeline from configuration."""

    # Load configuration first to check for chromium_src
    loader = ConfigLoader()
    pipeline_config = loader.load_config(config)

    # Get chromium_src from config if not provided via CLI
    if not chromium_src and "paths" in pipeline_config and "chromium_src" in pipeline_config["paths"]:
        chromium_src = Path(pipeline_config["paths"]["chromium_src"])
        typer.echo(f"Using chromium_src from config: {chromium_src}")

    # Enforce chromium_src requirement
    if not chromium_src:
        typer.echo("Error: Chromium source directory is required!", err=True)
        typer.echo("Provide it via --chromium-src CLI option or paths.chromium_src in config YAML", err=True)
        typer.echo("Example: browseros-cli build run --config config.yaml --chromium-src /path/to/chromium/src", err=True)
        raise typer.Exit(1)

    # Validate chromium_src path exists
    if not chromium_src.exists():
        typer.echo(f"Error: Chromium source directory does not exist: {chromium_src}", err=True)
        typer.echo("Please provide a valid chromium source path", err=True)
        raise typer.Exit(1)

    # Create pipeline context
    pipeline_ctx = PipelineContext(
        root_path=Path.cwd(),
        config_path=config,
        slack_enabled=slack,
        dry_run=dry_run
    )

    # Apply verb flags to determine which modules to run
    selected_modules = []
    if clean:
        selected_modules.append("clean")
    if sync:
        selected_modules.append("git-sync")
    if patch:
        selected_modules.extend(["patch-chromium", "patch-strings", "patch-sparkle", "patch-apply"])
    if resources:
        selected_modules.append("copy-resources")
    if build:
        selected_modules.extend(["configure", "build"])
    if sign:
        # Platform-specific signing will be handled by plan builder
        selected_modules.append("sign")
    if package:
        selected_modules.append("package")
    if upload:
        selected_modules.append("upload-gcs")

    # Override with explicit steps if provided
    if steps:
        selected_modules = steps

    # Create build context
    build_ctx = BuildContext(
        pipeline_ctx=pipeline_ctx,
        architecture=arch or "x64",
        build_type=build_type,
        platform=_detect_platform(),
        skip_modules=skip or [],
        only_modules=only or selected_modules,
        chromium_path=chromium_src  # Set the chromium source path
    )

    # Build execution plan
    plan_builder = PlanBuilder()
    plan = plan_builder.build_plan(pipeline_config, build_ctx)

    # Execute plan
    runner = PipelineRunner(pipeline_ctx)
    result = runner.execute(plan, build_ctx)

    if not result.success:
        typer.echo(f"Build failed: {result.message}", err=True)
        raise typer.Exit(1)

    typer.echo("Build completed successfully")


@app.command("step")
def step(
    module: str = typer.Argument(..., help="Module name to execute"),
    chromium_src: Path = typer.Option(..., "--chromium-src", "-S", help="Path to Chromium source directory"),
    arch: Optional[str] = typer.Option("x64", "--arch", help="Architecture"),
    build_type: Optional[str] = typer.Option("release", "--build-type", help="Build type"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution"),
):
    """Execute a single build module for debugging."""

    # Validate chromium_src path exists
    if not chromium_src.exists():
        typer.echo(f"Error: Chromium source directory does not exist: {chromium_src}", err=True)
        raise typer.Exit(1)

    pipeline_ctx = PipelineContext(
        root_path=Path.cwd(),
        config_path=Path("build/config/default.yaml"),
        dry_run=dry_run
    )

    build_ctx = BuildContext(
        pipeline_ctx=pipeline_ctx,
        architecture=arch,
        build_type=build_type,
        platform=_detect_platform(),
        chromium_path=chromium_src
    )

    # Get module from registry and execute
    from cli.modules.registry import get_module

    module_instance = get_module(module)
    if not module_instance:
        typer.echo(f"Unknown module: {module}", err=True)
        raise typer.Exit(1)

    result = module_instance.run(build_ctx, {})
    if not result.success:
        typer.echo(f"Module failed: {result.message}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Module {module} completed successfully")


@app.command("merge")
def merge():
    """Utility for merging builds."""
    typer.echo("Merge command not yet implemented")


@app.command("add-replace")
def add_replace():
    """Add file replacement."""
    typer.echo("Add-replace command not yet implemented")


@app.command("string-replace")
def string_replace():
    """String replacement utility."""
    typer.echo("String-replace command not yet implemented")


@app.command("upload-dist")
def upload_dist():
    """Upload distribution files."""
    typer.echo("Upload-dist command not yet implemented")


def _detect_platform() -> str:
    """Detect current platform."""
    import platform
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        return system