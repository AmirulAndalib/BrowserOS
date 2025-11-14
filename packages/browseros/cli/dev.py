"""Development tools and patch management CLI."""

import typer
from typing import Optional, List
from pathlib import Path
from cli.orchestrator.context import PipelineContext, BuildContext


app = typer.Typer(no_args_is_help=True)

# Sub-app for apply commands
apply_app = typer.Typer(help="Apply patches and modifications")
app.add_typer(apply_app, name="apply")


@apply_app.command("all")
def apply_all(
    chromium_src: Path = typer.Option(..., "--chromium-src", "-S", help="Path to Chromium source directory"),
    commit: bool = typer.Option(False, "--commit", help="Auto-commit after applying")
):
    """Apply all patches (default behavior)."""
    ctx = _create_dev_context(chromium_src)

    from cli.modules.dev.apply import apply_all_patches
    result = apply_all_patches(ctx)

    if result.success:
        typer.echo("All patches applied successfully")
        if commit:
            typer.echo("Auto-commit not yet implemented")
    else:
        typer.echo(f"Failed to apply patches: {result.message}", err=True)
        raise typer.Exit(1)


@apply_app.command("feature")
def apply_feature(
    name: str = typer.Argument(..., help="Feature name from features.yaml"),
    chromium_src: Path = typer.Option(..., "--chromium-src", "-S", help="Path to Chromium source directory"),
    commit: bool = typer.Option(False, "--commit", help="Auto-commit after applying")
):
    """Apply patches for a specific feature defined in features.yaml."""
    ctx = _create_dev_context(chromium_src)

    from cli.modules.dev.apply import apply_feature_patches
    result = apply_feature_patches(ctx, name)

    if result.success:
        typer.echo(f"Feature '{name}' patches applied successfully")
        if commit:
            typer.echo("Auto-commit not yet implemented")
    else:
        typer.echo(f"Failed to apply feature patches: {result.message}", err=True)
        raise typer.Exit(1)


@apply_app.command("selective")
def apply_selective(
    patches: List[str] = typer.Argument(..., help="Specific patch IDs to apply"),
    chromium_src: Path = typer.Option(..., "--chromium-src", "-S", help="Path to Chromium source directory")
):
    """Apply only selected patches by ID."""
    ctx = _create_dev_context(chromium_src)

    from cli.modules.dev.apply import apply_selective_patches
    result = apply_selective_patches(ctx, patches)

    if result.success:
        typer.echo(f"Selected patches applied successfully: {', '.join(patches)}")
    else:
        typer.echo(f"Failed to apply patches: {result.message}", err=True)
        raise typer.Exit(1)


@apply_app.command("overwrite")
def apply_overwrite(
    chromium_src: Path = typer.Option(..., "--chromium-src", "-S", help="Path to Chromium source directory"),
    force: bool = typer.Option(False, "--force", help="Force overwrite without confirmation")
):
    """Force overwrite existing patches."""
    ctx = _create_dev_context(chromium_src)

    if not force:
        confirm = typer.confirm("This will overwrite existing patches. Continue?")
        if not confirm:
            raise typer.Abort()

    from cli.modules.dev.apply import apply_overwrite_patches
    result = apply_overwrite_patches(ctx)

    if result.success:
        typer.echo("Patches overwritten successfully")
    else:
        typer.echo(f"Failed to overwrite patches: {result.message}", err=True)
        raise typer.Exit(1)


@app.command("list")
def list_patches(
    chromium_src: Path = typer.Option(..., "--chromium-src", "-S", help="Path to Chromium source directory")
):
    """List available patches."""
    ctx = _create_dev_context(chromium_src)

    from cli.modules.dev.patches import list_available_patches
    patches = list_available_patches(ctx)

    if not patches:
        typer.echo("No patches available")
        return

    typer.echo("Available patches:")
    for patch in patches:
        typer.echo(f"  - {patch}")


@app.command("reset")
def reset_patches(
    chromium_src: Path = typer.Option(..., "--chromium-src", "-S", help="Path to Chromium source directory"),
    hard: bool = typer.Option(False, "--hard", help="Hard reset, removing all changes")
):
    """Reset patch state."""
    ctx = _create_dev_context(chromium_src)

    if hard:
        confirm = typer.confirm("This will remove all patch changes. Continue?")
        if not confirm:
            raise typer.Abort()

    from cli.modules.dev.patches import reset_patch_state
    result = reset_patch_state(ctx, hard=hard)

    if result.success:
        typer.echo("Patch state reset successfully")
    else:
        typer.echo(f"Failed to reset: {result.message}", err=True)
        raise typer.Exit(1)


def _create_dev_context(chromium_src: Path) -> BuildContext:
    """Create a development context for patch operations."""
    # Validate chromium_src path exists
    if not chromium_src.exists():
        typer.echo(f"Error: Chromium source directory does not exist: {chromium_src}", err=True)
        raise typer.Exit(1)

    pipeline_ctx = PipelineContext(
        root_path=Path.cwd(),
        config_path=Path("build/config/default.yaml"),
        dry_run=False
    )

    return BuildContext(
        pipeline_ctx=pipeline_ctx,
        architecture="x64",  # Not relevant for patches
        build_type="debug",   # Default for dev
        platform=_detect_platform(),
        chromium_path=chromium_src
    )


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