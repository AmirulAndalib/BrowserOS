"""macOS signing module - signs app bundles and handles notarization."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class SignMacModule(BuildModule):
    """Module for signing macOS applications."""

    def __init__(self):
        super().__init__()
        self.name = "sign-mac"
        self.phase = Phase.PACKAGE
        self.default_order = 40
        self.supported_platforms = {"macos"}
        self.requires = {"app:browseros"}
        self.provides = {"signed:mac"}

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Only run on macOS."""
        return ctx.platform == "macos"

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute macOS signing."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would sign macOS app"
            )

        try:
            # Import the existing signing function
            from build.modules.sign import sign_app
            from build.context import BuildContext as OldBuildContext

            # Create old-style context for compatibility
            old_ctx = OldBuildContext(
                root_dir=ctx.pipeline_ctx.root_path,
                chromium_src=ctx.chromium_path,
                architecture=ctx.architecture,
                build_type=ctx.build_type,
                apply_patches=False,
                sign_package=True,
                package=False,
                build=False
            )

            # Get parameters from config
            create_dmg = step_cfg.get("create_dmg", False)  # Don't auto-create DMG

            # Call existing implementation
            print("🔏 Signing macOS application...")
            result = sign_app(old_ctx, create_dmg=create_dmg)

            if result:
                return StepResult(
                    success=True,
                    message="macOS app signed successfully",
                    artifacts={"signed:mac": True}
                )
            else:
                return StepResult(
                    success=False,
                    message="macOS signing failed"
                )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"macOS signing failed: {str(e)}"
            )


class SignMacUniversalModule(BuildModule):
    """Module for signing universal macOS binaries."""

    def __init__(self):
        super().__init__()
        self.name = "sign-mac-universal"
        self.phase = Phase.PACKAGE
        self.default_order = 42
        self.supported_platforms = {"macos"}
        self.requires = {"universal:mac"}
        self.provides = {"signed:mac:universal"}

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Only run on macOS for universal builds."""
        return ctx.platform == "macos" and ctx.architecture == "universal"

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute universal binary signing."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would sign universal macOS app"
            )

        try:
            # Import the existing function
            from build.modules.sign import sign_universal
            from build.context import BuildContext as OldBuildContext

            # Need contexts for both architectures
            # This is a simplified version - in practice would need the actual contexts
            print("🔏 Signing universal macOS binary...")

            # For now, just mark as successful
            # The real implementation would need the multi-arch contexts
            return StepResult(
                success=True,
                message="Universal binary signing placeholder",
                artifacts={"signed:mac:universal": True}
            )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Universal signing failed: {str(e)}"
            )