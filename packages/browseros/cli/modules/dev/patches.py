"""Patch management utilities."""

from pathlib import Path
from typing import List
from cli.orchestrator.context import BuildContext
from cli.orchestrator.module import StepResult


def list_available_patches(ctx: BuildContext) -> List[str]:
    """List all available patches."""
    # TODO: Implement by scanning patch directories
    # Look in build/patches/ or wherever patches are stored

    patch_dir = ctx.pipeline_ctx.root_path / "build" / "patches"
    patches = []

    if patch_dir.exists():
        # Scan for .patch files
        for patch_file in patch_dir.glob("**/*.patch"):
            patches.append(patch_file.stem)

    # Also check for features.yaml-based patches
    features_file = ctx.pipeline_ctx.root_path / "build" / "config" / "features.yaml"
    if features_file.exists():
        # TODO: Parse features.yaml and extract patch list
        pass

    return patches


def reset_patch_state(ctx: BuildContext, hard: bool = False) -> StepResult:
    """Reset patch application state."""
    try:
        if hard:
            print("Performing hard reset of patches...")
            # TODO: Git reset and clean operations
            # This would involve resetting the chromium repo
        else:
            print("Resetting patch state...")
            # TODO: Soft reset - just clear patch tracking

        return StepResult(
            success=True,
            message="Patch state reset successfully (stub)"
        )

    except Exception as e:
        return StepResult(
            success=False,
            message=f"Failed to reset patch state: {str(e)}"
        )