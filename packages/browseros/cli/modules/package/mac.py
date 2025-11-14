"""macOS packaging module - creates DMG installers."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class PackageMacModule(BuildModule):
    """Module for creating macOS DMG packages."""

    def __init__(self):
        super().__init__()
        self.name = "package-mac"
        self.phase = Phase.PACKAGE
        self.default_order = 41
        self.supported_platforms = {"macos"}
        self.requires = {"app:browseros"}
        self.provides = {"package:dmg"}

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Only run on macOS."""
        return ctx.platform == "macos"

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute DMG creation."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would create macOS DMG"
            )

        try:
            # Import the existing packaging function
            from build.modules.package import package
            from build.context import BuildContext as OldBuildContext

            # Create old-style context for compatibility
            old_ctx = OldBuildContext(
                root_dir=ctx.pipeline_ctx.root_path,
                chromium_src=ctx.chromium_path,
                architecture=ctx.architecture,
                build_type=ctx.build_type,
                apply_patches=False,
                sign_package=False,  # We're just packaging
                package=True,
                build=False
            )

            # Call existing implementation
            print("📀 Creating macOS DMG package...")
            result = package(old_ctx)

            if result:
                dmg_name = old_ctx.get_dmg_name()
                dmg_path = old_ctx.get_dist_dir() / dmg_name

                return StepResult(
                    success=True,
                    message=f"Created DMG: {dmg_name}",
                    artifacts={
                        "package:dmg": str(dmg_path),
                        "dmg_name": dmg_name
                    }
                )
            else:
                return StepResult(
                    success=False,
                    message="DMG creation failed"
                )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"DMG creation failed: {str(e)}"
            )


class PackageMacUniversalModule(BuildModule):
    """Module for creating universal macOS DMG packages."""

    def __init__(self):
        super().__init__()
        self.name = "package-mac-universal"
        self.phase = Phase.PACKAGE
        self.default_order = 43
        self.supported_platforms = {"macos"}
        self.requires = {"universal:mac"}
        self.provides = {"package:dmg:universal"}

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Only run on macOS for universal builds."""
        return ctx.platform == "macos" and ctx.architecture == "universal"

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute universal DMG creation."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would create universal macOS DMG"
            )

        try:
            # Import the existing function
            from build.modules.package import package_universal
            from build.context import BuildContext as OldBuildContext

            # This would need the multi-arch contexts in reality
            print("📀 Creating universal macOS DMG...")

            # Placeholder for now
            return StepResult(
                success=True,
                message="Universal DMG creation placeholder",
                artifacts={"package:dmg:universal": True}
            )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Universal DMG creation failed: {str(e)}"
            )