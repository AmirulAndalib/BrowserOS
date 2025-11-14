"""Environment setup module - configures build environment variables."""

import os
import platform
from pathlib import Path
from typing import Dict, Any
from cli.orchestrator.module import BuildModule, StepResult, Phase
from cli.orchestrator.context import BuildContext


class SetupEnvModule(BuildModule):
    """Module for setting up the build environment."""

    def __init__(self):
        super().__init__()
        self.name = "setup-env"
        self.phase = Phase.PREPARE
        self.default_order = 1
        self.supports_dry_run = True

    def should_run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Environment setup should always run."""
        return True

    def run(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> StepResult:
        """Set up environment variables for the build."""

        env_vars = {}

        # Platform-specific environment setup
        if ctx.platform == "windows":
            env_vars["DEPOT_TOOLS_WIN_TOOLCHAIN"] = "0"
            print("  Set DEPOT_TOOLS_WIN_TOOLCHAIN=0")

            # Check for Windows signing environment if needed
            if self._should_check_signing(ctx, step_cfg):
                signing_check = self._check_windows_signing_environment()
                if not signing_check["success"]:
                    return StepResult(
                        success=False,
                        message=signing_check["message"]
                    )

        elif ctx.platform == "macos":
            # Check for macOS signing environment if needed
            if self._should_check_signing(ctx, step_cfg):
                signing_check = self._check_macos_signing_environment()
                if not signing_check["success"]:
                    return StepResult(
                        success=False,
                        message=signing_check["message"]
                    )

        elif ctx.platform == "linux":
            # Linux-specific environment setup if needed
            pass

        # Set up depot_tools path if available
        depot_tools_path = self._find_depot_tools(ctx)
        if depot_tools_path:
            current_path = os.environ.get("PATH", "")
            if str(depot_tools_path) not in current_path:
                env_vars["PATH"] = f"{depot_tools_path}{os.pathsep}{current_path}"
                print(f"  Added depot_tools to PATH: {depot_tools_path}")

        # Apply environment variables
        if not ctx.pipeline_ctx.dry_run:
            for key, value in env_vars.items():
                os.environ[key] = value
                ctx.env_overrides[key] = value

        return StepResult(
            success=True,
            message="Environment setup completed",
            metadata={"env_vars": env_vars}
        )

    def _should_check_signing(self, ctx: BuildContext, step_cfg: Dict[str, Any]) -> bool:
        """Determine if signing environment should be checked."""
        # Check if any signing modules are in the pipeline
        return step_cfg.get("check_signing", False)

    def _check_macos_signing_environment(self) -> Dict[str, Any]:
        """Check if signing environment is properly configured for macOS."""
        required_vars = [
            "MACOS_CERTIFICATE_NAME",
            "PROD_MACOS_NOTARIZATION_APPLE_ID",
            "PROD_MACOS_NOTARIZATION_TEAM_ID",
            "PROD_MACOS_NOTARIZATION_PWD"
        ]

        missing = []
        for var in required_vars:
            if not os.environ.get(var):
                missing.append(var)

        if missing:
            return {
                "success": False,
                "message": f"Missing macOS signing environment variables: {', '.join(missing)}"
            }

        return {
            "success": True,
            "message": "macOS signing environment configured"
        }

    def _check_windows_signing_environment(self) -> Dict[str, Any]:
        """Check if signing environment is properly configured for Windows."""
        # Windows signing uses SSL.com eSigner
        required_vars = [
            "CODE_SIGN_TOOL_PATH",
            "ESIGNER_USERNAME",
            "ESIGNER_PASSWORD",
            "ESIGNER_TOTP_SECRET",
            "ESIGNER_CREDENTIAL_ID"
        ]

        missing = []
        for var in required_vars:
            if not os.environ.get(var):
                missing.append(var)

        if missing:
            return {
                "success": False,
                "message": f"Missing Windows signing environment variables: {', '.join(missing)}"
            }

        return {
            "success": True,
            "message": "Windows signing environment configured"
        }

    def _find_depot_tools(self, ctx: BuildContext) -> Path:
        """Find depot_tools directory."""
        # Check common locations
        possible_paths = [
            ctx.pipeline_ctx.root_path / "depot_tools",
            ctx.chromium_path.parent / "depot_tools",
            Path.home() / "depot_tools",
            Path("/usr/local/depot_tools"),
        ]

        # Check if DEPOT_TOOLS_PATH is set
        if depot_path := os.environ.get("DEPOT_TOOLS_PATH"):
            possible_paths.insert(0, Path(depot_path))

        for path in possible_paths:
            if path.exists() and (path / "gclient").exists():
                return path

        return None