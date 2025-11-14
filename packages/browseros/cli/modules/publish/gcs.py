"""GCS Upload module - handles uploading artifacts to Google Cloud Storage."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class UploadGcsModule(BuildModule):
    """Module for uploading artifacts to Google Cloud Storage."""

    def __init__(self):
        super().__init__()
        self.name = "upload-gcs"
        self.phase = Phase.PUBLISH
        self.default_order = 50
        self.supports_dry_run = True
        self.requires = {"app:browseros"}  # Needs something to upload

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Check if upload should run."""
        # Check if upload is disabled
        if step_cfg.get("skip_upload", False):
            return False
        return True

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute GCS upload."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Would upload artifacts to GCS"
            )

        try:
            # Import the existing function
            from build.modules.gcs import upload_package_artifacts
            from build.context import BuildContext as OldBuildContext

            # Create old-style context for compatibility
            old_ctx = OldBuildContext(
                root_dir=ctx.pipeline_ctx.root_path,
                chromium_src=ctx.chromium_path,
                architecture=ctx.architecture,
                build_type=ctx.build_type,
                apply_patches=False,
                sign_package=False,
                package=True,  # Assume we're uploading packages
                build=False
            )

            # Call existing implementation
            print("☁️ Uploading artifacts to GCS...")
            success, gcs_uris = upload_package_artifacts(old_ctx)

            if success:
                return StepResult(
                    success=True,
                    message=f"Uploaded to GCS successfully",
                    metadata={"gcs_uris": gcs_uris}
                )
            else:
                return StepResult(
                    success=False,
                    message="GCS upload failed"
                )

        except Exception as e:
            return StepResult(
                success=False,
                message=f"GCS upload failed: {str(e)}"
            )