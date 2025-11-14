"""Build/Compile module - handles the actual compilation of the browser."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class CompileModule(BuildModule):
    """Module for compiling the browser."""

    def __init__(self):
        super().__init__()
        self.name = "build"  # Use "build" as the name to match existing convention
        self.phase = Phase.BUILD
        self.default_order = 31
        self.supports_dry_run = True
        self.requires = {"configured"}  # Must be configured first
        self.provides = {"app:browseros"}

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Check if build should run."""
        # Skip if no chromium path configured
        if not ctx.chromium_path:
            return False
        return True

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute the build."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would compile the browser"
            )

        try:
            # Import the existing function
            from build.modules.compile import build
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

            # Call existing implementation
            print("🔨 Building the browser...")
            build(old_ctx)

            # Get the app path
            app_path = old_ctx.get_app_path()

            return StepResult(
                success=True,
                message="Build completed successfully",
                artifacts={"app:browseros": str(app_path)}
            )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Build failed: {str(e)}"
            )