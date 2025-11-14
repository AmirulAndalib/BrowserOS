"""Patch Chromium module - handles Chromium file replacements."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class PatchChromiumModule(BuildModule):
    """Module for replacing Chromium files with custom implementations."""

    def __init__(self):
        super().__init__()
        self.name = "patch-chromium"
        self.phase = Phase.PREPARE
        self.default_order = 20
        self.supports_dry_run = True

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Check if chromium patching should run."""
        # Skip if no chromium path configured
        if not ctx.chromium_path:
            return False
        return True

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute Chromium file replacements."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would replace Chromium files"
            )

        try:
            # Import the existing function
            from build.modules.chromium_replace import replace_chromium_files
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
            print("🔧 Replacing Chromium files...")
            replace_chromium_files(old_ctx)

            return StepResult(
                success=True,
                message="Chromium file replacements completed successfully"
            )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Chromium patch failed: {str(e)}"
            )