"""Windows packaging module - creates installer and portable packages."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class PackageWindowsModule(BuildModule):
    """Module for creating Windows installer packages."""

    def __init__(self):
        super().__init__()
        self.name = "package-windows"
        self.phase = Phase.PACKAGE
        self.default_order = 41
        self.supported_platforms = {"windows"}
        self.requires = {"app:browseros"}
        self.provides = {"package:installer", "package:portable"}

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Only run on Windows."""
        return ctx.platform == "windows"

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute Windows packaging."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would create Windows packages"
            )

        try:
            # Import the existing packaging function
            from build.modules.package_windows import package
            from build.context import BuildContext as OldBuildContext

            # Create old-style context for compatibility
            old_ctx = OldBuildContext(
                root_dir=ctx.pipeline_ctx.root_path,
                chromium_src=ctx.chromium_path,
                architecture=ctx.architecture,
                build_type=ctx.build_type,
                apply_patches=False,
                sign_package=False,  # Already signed
                package=True,
                build=False
            )

            # Get parameters from config
            create_installer = step_cfg.get("create_installer", True)
            create_portable = step_cfg.get("create_portable", False)

            # Call existing implementation
            print("📦 Creating Windows packages...")
            result = package(old_ctx)

            if result:
                artifacts = {}

                # Check for installer
                installer_path = old_ctx.chromium_src / old_ctx.out_dir / "mini_installer.exe"
                if installer_path.exists():
                    artifacts["package:installer"] = str(installer_path)

                # Check for portable ZIP
                dist_dir = old_ctx.get_dist_dir()
                zip_name = f"{old_ctx.NXTSCAPE_APP_BASE_NAME}_{old_ctx.nxtscape_chromium_version}_{old_ctx.architecture}.zip"
                zip_path = dist_dir / zip_name
                if zip_path.exists():
                    artifacts["package:portable"] = str(zip_path)

                return StepResult(
                    success=True,
                    message="Windows packages created successfully",
                    artifacts=artifacts
                )
            else:
                return StepResult(
                    success=False,
                    message="Windows packaging failed"
                )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Windows packaging failed: {str(e)}"
            )