"""Linux packaging module - creates AppImage and .deb packages."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class PackageLinuxModule(BuildModule):
    """Module for creating Linux packages (AppImage, .deb)."""

    def __init__(self):
        super().__init__()
        self.name = "package-linux"
        self.phase = Phase.PACKAGE
        self.default_order = 41
        self.supported_platforms = {"linux"}
        self.requires = {"app:browseros"}
        self.provides = {"package:appimage", "package:deb"}

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Only run on Linux."""
        return ctx.platform == "linux"

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute Linux packaging."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would create Linux packages"
            )

        try:
            # Import the existing packaging function
            from build.modules.package_linux import package
            from build.context import BuildContext as OldBuildContext

            # Create old-style context for compatibility
            old_ctx = OldBuildContext(
                root_dir=ctx.pipeline_ctx.root_path,
                chromium_src=ctx.chromium_path,
                architecture=ctx.architecture,
                build_type=ctx.build_type,
                apply_patches=False,
                sign_package=False,
                package=True,
                build=False
            )

            # Get parameters from config
            create_appimage = step_cfg.get("appimage", {}).get("enabled", True)
            create_deb = step_cfg.get("create_deb", True)
            create_rpm = step_cfg.get("create_rpm", False)

            # Call existing implementation
            print("📦 Creating Linux packages...")
            result = package(old_ctx)

            if result:
                artifacts = {}
                dist_dir = old_ctx.get_dist_dir()

                # Check for AppImage
                appimage_name = f"BrowserOS-{old_ctx.nxtscape_chromium_version}-x86_64.AppImage"
                appimage_path = dist_dir / appimage_name
                if appimage_path.exists():
                    artifacts["package:appimage"] = str(appimage_path)

                # Check for .deb
                deb_name = f"browseros_{old_ctx.nxtscape_chromium_version}_{old_ctx.architecture}.deb"
                deb_path = dist_dir / deb_name
                if deb_path.exists():
                    artifacts["package:deb"] = str(deb_path)

                return StepResult(
                    success=True,
                    message="Linux packages created successfully",
                    artifacts=artifacts
                )
            else:
                return StepResult(
                    success=False,
                    message="Linux packaging failed"
                )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Linux packaging failed: {str(e)}"
            )