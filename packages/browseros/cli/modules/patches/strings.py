"""Patch Strings module - handles string replacements in source files."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class PatchStringsModule(BuildModule):
    """Module for applying string replacements in Chromium source."""

    def __init__(self):
        super().__init__()
        self.name = "patch-strings"
        self.phase = Phase.PREPARE
        self.default_order = 21
        self.supports_dry_run = True

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Check if string patching should run."""
        # Skip if no chromium path configured
        if not ctx.chromium_path:
            return False
        return True

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute string replacements."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would apply string replacements"
            )

        try:
            # Import the existing function
            from build.modules.string_replaces import apply_string_replacements
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
            print("🔤 Applying string replacements...")
            apply_string_replacements(old_ctx)

            return StepResult(
                success=True,
                message="String replacements completed successfully"
            )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"String patch failed: {str(e)}"
            )