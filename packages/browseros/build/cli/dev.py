#!/usr/bin/env python3
"""
Dev CLI - Chromium patch management tool

A git-like patch management system for maintaining patches against Chromium.
Enables extracting, applying, and managing patches across Chromium upgrades.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import typer
from typer import Typer, Option, Argument

# Import from common and utils
from ..common.context import BuildContext
from ..utils import log_info, log_error, log_success, log_warning, join_paths


@dataclass
class DevCliConfig:
    """Configuration for Dev CLI from various sources"""

    chromium_src: Optional[Path] = None
    auto_commit: bool = False
    interactive: bool = True

    @classmethod
    def load(cls, cli_chromium_src: Optional[Path] = None) -> "DevCliConfig":
        """Load configuration from various sources with precedence:
        1. CLI arguments (highest priority)
        2. Environment variables
        3. Config file
        4. Defaults (lowest priority)
        """
        config = cls()

        # Load from config file if exists
        config_file = Path.cwd() / ".dev-cli.yaml"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    file_config = yaml.safe_load(f)
                    if file_config and "defaults" in file_config:
                        defaults = file_config["defaults"]
                        if "chromium_src" in defaults:
                            config.chromium_src = Path(defaults["chromium_src"])
                        config.auto_commit = defaults.get("auto_commit", False)
                        config.interactive = defaults.get("interactive", True)
            except Exception as e:
                log_warning(f"Failed to load config file: {e}")

        # Override with environment variables
        env_chromium_src = os.environ.get("CHROMIUM_SRC")
        if env_chromium_src:
            config.chromium_src = Path(env_chromium_src)

        # Override with CLI arguments (highest priority)
        if cli_chromium_src:
            config.chromium_src = cli_chromium_src

        # Set default if still not set
        if not config.chromium_src:
            # Try to detect from current directory structure
            possible_src = Path.cwd() / "chromium_src"
            if possible_src.exists() and (possible_src / "chrome").exists():
                config.chromium_src = possible_src

        return config


def create_build_context(chromium_src: Optional[Path] = None) -> Optional[BuildContext]:
    """Create BuildContext for dev CLI operations"""
    try:
        config = DevCliConfig.load(chromium_src)

        if not config.chromium_src:
            log_error("Chromium source directory not specified")
            log_info("Use --chromium-src option or set CHROMIUM_SRC environment variable")
            return None

        if not config.chromium_src.exists():
            log_error(f"Chromium source directory does not exist: {config.chromium_src}")
            return None

        ctx = BuildContext(
            root_dir=Path.cwd(),
            chromium_src=config.chromium_src,
            architecture="",  # Not needed for patch operations
            build_type="debug",  # Not needed for patch operations
        )

        # Store config in context for access by commands
        ctx.dev_config = config

        return ctx
    except Exception as e:
        log_error(f"Failed to create build context: {e}")
        return None


# Create the Typer app
app = Typer(
    name="dev",
    help="Chromium patch management tool",
    no_args_is_help=True,
)

# State class to hold global options
class State:
    def __init__(self):
        self.chromium_src: Optional[Path] = None
        self.verbose: bool = False
        self.quiet: bool = False

state = State()


@app.callback()
def main(
    chromium_src: Optional[Path] = Option(
        None,
        "--chromium-src",
        "-S",
        help="Path to Chromium source directory",
        exists=True,
    ),
    verbose: bool = Option(False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = Option(False, "--quiet", "-q", help="Suppress non-essential output"),
):
    """
    Dev CLI - Chromium patch management tool

    This tool provides git-like commands for managing patches against Chromium:

    Extract patches from commits:
      browseros dev extract commit HEAD
      browseros dev extract range HEAD~5 HEAD

    Apply patches:
      browseros dev apply all
      browseros dev apply feature llm-chat

    Manage features:
      browseros dev feature list
      browseros dev feature add my-feature HEAD
      browseros dev feature show my-feature
    """
    state.chromium_src = chromium_src
    state.verbose = verbose
    state.quiet = quiet


@app.command()
def status():
    """Show dev CLI status"""
    log_info("Dev CLI Status")
    log_info("-" * 40)

    build_ctx = create_build_context(state.chromium_src)
    if build_ctx:
        log_success(f"Chromium source: {build_ctx.chromium_src}")

        # Check for patches directory
        patches_dir = build_ctx.root_dir / "chromium_patches"
        if patches_dir.exists():
            patch_count = len(list(patches_dir.rglob("*.patch")))
            log_info(f"Individual patches: {patch_count}")
        else:
            log_warning("No patches directory found")

        # Check for features.yaml
        features_file = build_ctx.root_dir / "features.yaml"
        if features_file.exists():
            with open(features_file) as f:
                features = yaml.safe_load(f)
                feature_count = len(features.get("features", {}))
                log_info(f"Features defined: {feature_count}")
        else:
            log_warning("No features.yaml found")
    else:
        log_error("Failed to create build context")


# Create sub-apps for extract, apply, and feature commands
extract_app = Typer(name="extract", help="Extract patches from commits")
apply_app = Typer(name="apply", help="Apply patches to Chromium")
feature_app = Typer(name="feature", help="Manage features")

# Add sub-apps to main app
app.add_typer(extract_app, name="extract")
app.add_typer(apply_app, name="apply")
app.add_typer(feature_app, name="feature")


# Extract commands
@extract_app.command(name="commit")
def extract_commit(
    commit: str = Argument(..., help="Git commit reference (e.g., HEAD)"),
    output: Optional[Path] = Option(None, "--output", "-o", help="Output directory"),
    interactive: bool = Option(True, "--interactive/--no-interactive", "-i/-n", help="Interactive mode"),
):
    """Extract patches from a single commit"""
    ctx = create_build_context(state.chromium_src)
    if not ctx:
        raise typer.Exit(1)

    from ..modules.extract import extract_commit as extract_commit_impl
    success = extract_commit_impl(ctx, commit, output, interactive)
    if not success:
        raise typer.Exit(1)


@extract_app.command(name="range")
def extract_range(
    start: str = Argument(..., help="Start commit (exclusive)"),
    end: str = Argument(..., help="End commit (inclusive)"),
    output: Optional[Path] = Option(None, "--output", "-o", help="Output directory"),
    interactive: bool = Option(True, "--interactive/--no-interactive", "-i/-n", help="Interactive mode"),
):
    """Extract patches from a range of commits"""
    ctx = create_build_context(state.chromium_src)
    if not ctx:
        raise typer.Exit(1)

    from ..modules.extract import extract_range as extract_range_impl
    success = extract_range_impl(ctx, start, end, output, interactive)
    if not success:
        raise typer.Exit(1)


# Apply commands
@apply_app.command(name="all")
def apply_all(
    interactive: bool = Option(True, "--interactive/--no-interactive", "-i/-n", help="Interactive mode"),
    commit: bool = Option(False, "--commit", "-c", help="Commit after each patch"),
):
    """Apply all patches from chromium_patches/"""
    ctx = create_build_context(state.chromium_src)
    if not ctx:
        raise typer.Exit(1)

    from ..modules.apply import apply_all as apply_all_impl
    success = apply_all_impl(ctx, interactive, commit)
    if not success:
        raise typer.Exit(1)


@apply_app.command(name="feature")
def apply_feature(
    feature_name: str = Argument(..., help="Feature name to apply"),
    interactive: bool = Option(True, "--interactive/--no-interactive", "-i/-n", help="Interactive mode"),
    commit: bool = Option(False, "--commit", "-c", help="Commit after applying"),
):
    """Apply patches for a specific feature"""
    ctx = create_build_context(state.chromium_src)
    if not ctx:
        raise typer.Exit(1)

    from ..modules.apply import apply_feature as apply_feature_impl
    success = apply_feature_impl(ctx, feature_name, interactive, commit)
    if not success:
        raise typer.Exit(1)


# Feature commands
@feature_app.command(name="list")
def feature_list():
    """List all defined features"""
    ctx = create_build_context(state.chromium_src)
    if not ctx:
        raise typer.Exit(1)

    from ..modules.feature import list_features
    list_features(ctx)


@feature_app.command(name="show")
def feature_show(
    feature_name: str = Argument(..., help="Feature name to show"),
):
    """Show details of a specific feature"""
    ctx = create_build_context(state.chromium_src)
    if not ctx:
        raise typer.Exit(1)

    from ..modules.feature import show_feature
    show_feature(ctx, feature_name)


@feature_app.command(name="add")
def feature_add(
    feature_name: str = Argument(..., help="Feature name to add"),
    commit: str = Argument(..., help="Git commit reference"),
    description: Optional[str] = Option(None, "--description", "-d", help="Feature description"),
):
    """Add a new feature from a commit"""
    ctx = create_build_context(state.chromium_src)
    if not ctx:
        raise typer.Exit(1)

    from ..modules.feature import add_feature
    success = add_feature(ctx, feature_name, commit, description)
    if not success:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()