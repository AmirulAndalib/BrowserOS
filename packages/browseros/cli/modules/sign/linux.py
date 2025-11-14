"""Linux signing module - placeholder as Linux typically doesn't sign binaries."""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class SignLinuxModule(BuildModule):
    """Module for signing Linux binaries (typically not needed)."""

    def __init__(self):
        super().__init__()
        self.name = "sign-linux"
        self.phase = Phase.PACKAGE
        self.default_order = 40
        self.supported_platforms = {"linux"}
        self.requires = {"app:browseros"}
        self.provides = {"signed:linux"}
        self.supports_dry_run = True

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Only run on Linux if explicitly requested."""
        # Linux typically doesn't require signing
        return ctx.platform == "linux" and step_cfg.get("force", False)

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Execute Linux signing (usually a no-op)."""

        if ctx.pipeline_ctx.dry_run:
            return StepResult(
                success=True,
                message="[DRY RUN] Linux signing (no-op)"
            )

        # Linux doesn't typically sign binaries
        # This is here for completeness and future GPG signing if needed
        print("ℹ️  Linux binaries typically don't require signing")

        return StepResult(
            success=True,
            message="Linux signing skipped (not required)",
            artifacts={"signed:linux": True}
        )