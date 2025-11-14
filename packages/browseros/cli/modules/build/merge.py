"""Merge module - creates universal binaries by merging architectures (macOS only)."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class MergeUniversalModule(BuildModule):
    """Module for creating macOS universal binaries by merging architectures."""

    def __init__(self):
        super().__init__()
        self.name = "merge-universal"
        self.phase = Phase.BUILD
        self.default_order = 35  # After build, before signing
        self.supported_platforms = {"macos"}
        self.requires = {"app:browseros:arm64", "app:browseros:x64"}
        self.provides = {"universal:mac", "app:browseros:universal"}

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Only run on macOS when building universal binary."""
        return ctx.platform == "macos" and ctx.architecture == "universal"

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute universal binary creation."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would create universal binary"
            )

        try:
            # Import the existing merge function
            from build.modules.merge import merge_architectures
            from build.context import BuildContext as OldBuildContext

            # Get the source architecture paths from step config
            arm64_app = Path(step_cfg.get("arm64_app", ""))
            x64_app = Path(step_cfg.get("x64_app", ""))

            if not arm64_app or not x64_app:
                # Try to construct paths from context
                # This is simplified - real implementation would need the actual paths
                return StepResult(
                    success=False,
                    message="Architecture paths not provided for universal merge"
                )

            # Call existing implementation
            print("🔄 Creating universal binary...")
            universal_app = ctx.chromium_path / "out/Default_universal" / "BrowserOS.app"

            result = merge_architectures(
                arm64_path=arm64_app,
                x86_64_path=x64_app,
                output_path=universal_app,
                verbose=True
            )

            if result:
                return StepResult(
                    success=True,
                    message="Universal binary created successfully",
                    artifacts={
                        "universal:mac": str(universal_app),
                        "app:browseros:universal": str(universal_app)
                    }
                )
            else:
                return StepResult(
                    success=False,
                    message="Universal binary creation failed"
                )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Universal merge failed: {str(e)}"
            )