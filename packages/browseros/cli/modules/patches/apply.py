"""Patch Apply module - applies Git patches to the source code."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class PatchApplyModule(BuildModule):
    """Module for applying Git patches to Chromium source."""

    def __init__(self):
        super().__init__()
        self.name = "patch-apply"
        self.phase = Phase.PREPARE
        self.default_order = 23
        self.supports_dry_run = True

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Check if patch application should run."""
        # Skip if no chromium path configured
        if not ctx.chromium_path:
            return False
        return True

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute patch application."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would apply patches"
            )

        try:
            # Import the existing function
            from build.modules.patches import apply_patches
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

            # Get parameters from step config
            interactive = step_cfg.get("interactive", False)
            commit_each = step_cfg.get("commit_each", False)

            # Call existing implementation
            print("🩹 Applying patches...")
            apply_patches(old_ctx, interactive=interactive, commit_each=commit_each)

            return StepResult(
                success=True,
                message="Patches applied successfully"
            )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Patch application failed: {str(e)}"
            )