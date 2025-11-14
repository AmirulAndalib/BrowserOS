"""Patch Sparkle module - handles Sparkle framework setup for macOS."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class PatchSparkleModule(BuildModule):
    """Module for setting up Sparkle framework on macOS."""

    def __init__(self):
        super().__init__()
        self.name = "patch-sparkle"
        self.phase = Phase.PREPARE
        self.default_order = 22
        self.supported_platforms = {"macos"}  # macOS only
        self.supports_dry_run = True

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Check if Sparkle setup should run."""
        # Only run on macOS
        if ctx.platform != "macos":
            return False
        # Skip if no chromium path configured
        if not ctx.chromium_path:
            return False
        return True

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute Sparkle framework setup."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would setup Sparkle framework"
            )

        try:
            # Import the existing function
            from build.modules.git import setup_sparkle
            from build.context import BuildContext as OldBuildContext

            # Create old-style context for compatibility
            old_ctx = OldBuildContext(
                root_dir=ctx.pipeline_ctx.root_path,
                chromium_src=ctx.chromium_path,
                architecture=ctx.architecture,
                build_type=ctx.build_type,
                apply_patches=True,
                sign_package=False,
                package=False,
                build=False
            )

            # Call existing implementation
            print("✨ Setting up Sparkle framework...")
            result = setup_sparkle(old_ctx)

            if result:
                return StepResult(
                    success=True,
                    message="Sparkle framework setup completed successfully"
                )
            else:
                return StepResult(
                    success=False,
                    message="Sparkle setup failed"
                )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Sparkle setup failed: {str(e)}"
            )