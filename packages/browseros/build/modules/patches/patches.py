#!/usr/bin/env python3
"""Patch management module for BrowserOS build system"""

import sys
import shutil
from pathlib import Path
from ...common.module import CommandModule, ValidationError
from ...common.context import Context
from ...common.utils import log_info, log_error


class PatchesModule(CommandModule):
    produces = []
    requires = []
    description = "Apply BrowserOS patches to Chromium"

    def validate(self, ctx: Context) -> None:
        if not shutil.which("git"):
            raise ValidationError("Git is not available in PATH - required for applying patches")

        patches_dir = ctx.get_browseros_patches_dir()
        if not patches_dir.exists():
            raise ValidationError(f"Patches directory not found: {patches_dir}")

    def execute(self, ctx: Context) -> None:
        log_info("\n🩹 Applying patches...")
        if not apply_patches_impl(ctx, interactive=False, commit_each=False):
            raise RuntimeError("Failed to apply patches")


def apply_patches_impl(
    ctx: Context, interactive: bool = False, commit_each: bool = False
) -> bool:
    """Apply patches using the dev CLI patch system"""
    log_info("\n🩹 Applying patches using dev CLI system...")

    # Check if git is available
    if not shutil.which("git"):
        log_error("Git is not available in PATH")
        log_error("Please install Git to apply patches")
        raise RuntimeError("Git not found in PATH")

    # Import dev CLI module
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from modules.dev_cli.apply import apply_all_patches

    # Call the dev CLI function directly
    _, failed = apply_all_patches(
        build_ctx=ctx,
        commit_each=commit_each,
        dry_run=False,
        interactive=interactive,
    )

    # Handle results
    if failed and not interactive:
        # In non-interactive mode, fail if any patches failed
        raise RuntimeError(f"Failed to apply {len(failed)} patches")
