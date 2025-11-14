"""Configure module - handles build configuration with GN."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class ConfigureModule(BuildModule):
    """Module for configuring the build with GN."""

    def __init__(self):
        super().__init__()
        self.name = "configure"
        self.phase = Phase.BUILD
        self.default_order = 30
        self.supports_dry_run = True
        self.provides = {"configured"}

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Check if configuration should run."""
        # Skip if no chromium path configured
        if not ctx.chromium_path:
            return False
        return True

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute build configuration."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would configure build with GN"
            )

        try:
            # Import the existing function
            from build.modules.configure import configure
            from build.context import BuildContext as OldBuildContext

            # Create old-style context for compatibility
            old_ctx = OldBuildContext(
                root_dir=ctx.pipeline_ctx.root_path,
                chromium_src=ctx.chromium_path,
                architecture=ctx.architecture,
                build_type=ctx.build_type,
                apply_patches=False,
                sign_package=False,
                package=False,
                build=True
            )

            # Get GN flags file from step config or metadata
            gn_flags_file = None
            if "gn_flags" in step_cfg:
                gn_flags_file = Path(step_cfg["gn_flags"])
            elif "gn_flags_file" in ctx.metadata:
                gn_flags_file = Path(ctx.metadata["gn_flags_file"])

            # Call existing implementation
            print("⚙️ Configuring build with GN...")
            configure(old_ctx, gn_flags_file)

            return StepResult(
                success=True,
                message="Build configured successfully",
                artifacts={"configured": True}
            )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Configure failed: {str(e)}"
            )