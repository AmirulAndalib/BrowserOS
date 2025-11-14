"""
Build CLI - Main build command

This module uses relative imports and must be run as a module:
    python -m build.cli.build

Or via the installed entry point:
    browseros build
"""
from pathlib import Path
from typing import Optional, Tuple

import typer

from ..build_old import build_main
from ..utils import log_error


def main(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Load configuration from YAML file",
        exists=True,
    ),
    clean: bool = typer.Option(
        False,
        "--clean",
        "-C",
        help="Clean before build",
    ),
    git_setup: bool = typer.Option(
        False,
        "--git-setup",
        "-g",
        help="Git setup",
    ),
    apply_patches: bool = typer.Option(
        False,
        "--apply-patches",
        "-p",
        help="Apply patches",
    ),
    sign: bool = typer.Option(
        False,
        "--sign",
        "-s",
        help="Sign and notarize the app",
    ),
    arch: Optional[str] = typer.Option(
        None,
        "--arch",
        "-a",
        help="Architecture (arm64, x64) - defaults to platform-specific",
    ),
    build_type: str = typer.Option(
        "debug",
        "--build-type",
        "-t",
        help="Build type (debug or release)",
    ),
    package: bool = typer.Option(
        False,
        "--package",
        "-P",
        help="Create package (DMG/AppImage/Installer)",
    ),
    build: bool = typer.Option(
        False,
        "--build",
        "-b",
        help="Build",
    ),
    chromium_src: Optional[Path] = typer.Option(
        None,
        "--chromium-src",
        "-S",
        help="Path to Chromium source directory",
    ),
    slack_notifications: bool = typer.Option(
        False,
        "--slack-notifications",
        "-n",
        help="Enable Slack notifications",
    ),
    merge: Optional[Tuple[str, str]] = typer.Option(
        None,
        "--merge",
        help="Merge two architecture builds: --merge path/to/arch1.app path/to/arch2.app",
        metavar="ARCH1_APP ARCH2_APP",
    ),
    patch_interactive: bool = typer.Option(
        False,
        "--patch-interactive",
        "-i",
        help="Ask for confirmation before applying each patch",
    ),
):
    """Build BrowserOS browser

    Simple build system for BrowserOS. Can run individual steps or full pipeline.
    """

    # Validate chromium-src for commands that need it
    if merge or (not config and chromium_src is None):
        if not chromium_src:
            if merge:
                log_error("--merge requires --chromium-src to be specified")
                log_error(
                    "Example: browseros build --merge app1.app app2.app --chromium-src /path/to/chromium/src"
                )
            else:
                log_error("--chromium-src is required when not using a config file")
                log_error(
                    "Example: browseros build --chromium-src /path/to/chromium/src"
                )
            raise typer.Exit(1)

        # Validate chromium_src path exists
        if not chromium_src.exists():
            log_error(f"Chromium source directory does not exist: {chromium_src}")
            raise typer.Exit(1)

    # Handle merge command
    if merge:
        from ..modules.merge import handle_merge_command

        arch1_path, arch2_path = merge
        # Convert strings to Path objects
        arch1_path = Path(arch1_path)
        arch2_path = Path(arch2_path)

        if handle_merge_command(arch1_path, arch2_path, chromium_src, sign, package):
            raise typer.Exit(0)
        else:
            raise typer.Exit(1)

    # Validate arch and build_type choices
    if arch and arch not in ["arm64", "x64"]:
        log_error(f"Invalid architecture: {arch}. Must be 'arm64' or 'x64'")
        raise typer.Exit(1)

    if build_type not in ["debug", "release"]:
        log_error(f"Invalid build type: {build_type}. Must be 'debug' or 'release'")
        raise typer.Exit(1)

    # Regular build workflow
    build_main(
        config_file=config,
        clean_flag=clean,
        git_setup_flag=git_setup,
        apply_patches_flag=apply_patches,
        sign_flag=sign,
        package_flag=package,
        build_flag=build,
        arch=arch or "",  # Pass empty string to use platform default
        build_type=build_type,
        chromium_src_dir=chromium_src,
        slack_notifications=slack_notifications,
        patch_interactive=patch_interactive,
        patch_commit=False,  # Removed from CLI, always False
        upload_gcs=True,  # Always upload to GCS by default
    )
