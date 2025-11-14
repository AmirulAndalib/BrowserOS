"""Windows signing module - signs binaries using SSL.com eSigner."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class SignWindowsModule(BuildModule):
    """Module for signing Windows binaries."""

    def __init__(self):
        super().__init__()
        self.name = "sign-windows"
        self.phase = Phase.PACKAGE
        self.default_order = 40
        self.supported_platforms = {"windows"}
        self.requires = {"app:browseros"}
        self.provides = {"signed:windows"}

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Only run on Windows."""
        return ctx.platform == "windows"

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute Windows binary signing."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would sign Windows binaries"
            )

        try:
            # Import the existing signing function
            from build.modules.package_windows import sign_binaries
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

            # Get certificate name from config
            certificate_name = step_cfg.get("certificate_name")

            # Call existing implementation
            print("🔏 Signing Windows binaries...")
            result = sign_binaries(old_ctx, certificate_name)

            if result:
                return StepResult(
                    success=True,
                    message="Windows binaries signed successfully",
                    artifacts={"signed:windows": True}
                )
            else:
                return StepResult(
                    success=False,
                    message="Windows signing failed"
                )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Windows signing failed: {str(e)}"
            )


class SignWindowsInstallerModule(BuildModule):
    """Module for signing Windows installer after packaging."""

    def __init__(self):
        super().__init__()
        self.name = "sign-windows-installer"
        self.phase = Phase.PACKAGE
        self.default_order = 42
        self.supported_platforms = {"windows"}
        self.requires = {"package:installer"}
        self.provides = {"signed:installer"}

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Only run on Windows."""
        return ctx.platform == "windows"

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Sign the Windows installer package."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would sign Windows installer"
            )

        try:
            # Import the signing function
            from build.modules.package_windows import sign_with_codesigntool
            from pathlib import Path

            # Get installer path from artifacts
            installer_path = ctx.artifacts.get("package:installer")
            if not installer_path:
                return StepResult(
                    success=False,
                    message="No installer found to sign"
                )

            # Sign the installer
            print("🔏 Signing Windows installer...")
            result = sign_with_codesigntool([Path(installer_path)])

            if result:
                return StepResult(
                    success=True,
                    message="Windows installer signed successfully",
                    artifacts={"signed:installer": installer_path}
                )
            else:
                return StepResult(
                    success=False,
                    message="Installer signing failed"
                )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Installer signing failed: {str(e)}"
            )