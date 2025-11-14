"""Clean module - removes build artifacts and resets state."""

import os
import shutil
from pathlib import Path
from typing import Dict, Any
from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class CleanModule(BuildModule):
    """Module for cleaning build artifacts."""

    def __init__(self):
        super().__init__()
        self.name = "clean"
        self.phase = Phase.PREPARE
        self.default_order = 0
        self.supports_dry_run = True

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Clean should always run when requested."""
        return True

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute clean operations."""
        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would clean build artifacts"
            )

        try:
            # Clean output directory
            if ctx.output_path and ctx.output_path.exists():
                print(f"  Cleaning {ctx.output_path}")
                shutil.rmtree(ctx.output_path, ignore_errors=True)

            # Git reset in chromium directory
            if ctx.chromium_path and (ctx.chromium_path / ".git").exists():
                self._git_reset(ctx)

            # Clean Sparkle artifacts on macOS
            if ctx.platform == "macos":
                self._clean_sparkle(ctx)

            return StepResult(
                success=True,
                message="Clean completed successfully"
            )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Clean failed: {str(e)}"
            )

    def _git_reset(self, ctx: BuildContext):
        """Reset git repository to clean state."""
        import subprocess

        if not ctx.chromium_path:
            print("  Warning: No chromium_path set, skipping git reset")
            return

        # Save current directory
        original_dir = os.getcwd()

        try:
            os.chdir(ctx.chromium_path)

            # Reset to HEAD
            subprocess.run(
                ["git", "reset", "--hard", "HEAD"],
                check=True,
                capture_output=True
            )

            # Clean with exclusions for important directories
            subprocess.run(
                [
                    "git", "clean", "-fdx",
                    "chrome/",
                    "components/",
                    "--exclude=third_party/",
                    "--exclude=build_tools/",
                    "--exclude=uc_staging/",
                    "--exclude=buildtools/",
                    "--exclude=tools/",
                    "--exclude=build/",
                ],
                check=True,
                capture_output=True
            )

        finally:
            os.chdir(original_dir)

    def _clean_sparkle(self, ctx: BuildContext):
        """Clean Sparkle build artifacts on macOS."""
        if not ctx.chromium_path:
            return

        sparkle_dir = ctx.chromium_path / "third_party" / "sparkle"
        if sparkle_dir.exists():
            print(f"  Cleaning Sparkle: {sparkle_dir}")
            shutil.rmtree(sparkle_dir, ignore_errors=True)