"""Copy Resources module - handles copying resource files based on configuration."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class CopyResourcesModule(BuildModule):
    """Module for copying resource files into the build."""

    def __init__(self):
        super().__init__()
        self.name = "copy-resources"
        self.phase = Phase.PREPARE
        self.default_order = 24
        self.supports_dry_run = True

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Check if resources should be copied."""
        # Skip if no chromium path configured
        if not ctx.chromium_path:
            return False
        return True

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute resource copying."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would copy resource files"
            )

        try:
            # Import the existing function
            from build.modules.resources import copy_resources
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
            commit_each = step_cfg.get("commit_each", False)

            # Call existing implementation
            print("📋 Copying resource files...")
            copy_resources(old_ctx, commit_each=commit_each)

            return StepResult(
                success=True,
                message="Resources copied successfully"
            )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Resource copy failed: {str(e)}"
            )