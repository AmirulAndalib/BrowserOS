"""Git sync module - handles git operations and Chromium source management."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class GitSyncModule(BuildModule):
    """Module for git operations and Chromium source synchronization."""

    def __init__(self):
        super().__init__()
        self.name = "git-sync"
        self.phase = Phase.PREPARE
        self.default_order = 10
        self.supports_dry_run = True

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Check if git sync should run."""
        # Skip if no chromium path configured
        if not ctx.chromium_path:
            return False
        return True

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute git sync operations."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message=f"[DRY RUN] Would sync Chromium source to tag"
            )

        try:
            # Import the existing setup_git function
            from build.modules.git import setup_git
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
                build=False
            )

            # Call existing implementation
            print(f"🔀 Setting up git and Chromium source...")
            result = setup_git(old_ctx)

            if result:
                return StepResult(
                    success=True,
                    message="Git sync completed successfully",
                    metadata={"chromium_version": old_ctx.chromium_version}
                )
            else:
                return StepResult(
                    success=False,
                    message="Git sync failed"
                )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Git sync failed: {str(e)}"
            )