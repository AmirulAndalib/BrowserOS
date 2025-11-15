#!/usr/bin/env python3
"""
Build argument resolution with strict precedence ordering.

Provides resolvers that consolidate configuration from multiple sources:
- CLI arguments (highest precedence)
- YAML configuration files
- Environment variables
- System defaults (lowest precedence)

This centralizes precedence logic to prevent errors and inconsistencies.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from .context import Context
from .utils import get_platform_arch, log_info, log_warning


class BuildArgsResolver:
    """Resolves build configuration from multiple sources with defined precedence.

    Precedence Order (strictly enforced):
    1. CLI arguments (highest)
    2. YAML configuration
    3. Environment variables
    4. System defaults (lowest)
    """

    def __init__(
        self,
        cli_args: Dict[str, Any],
        yaml_config: Optional[Dict[str, Any]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        root_dir: Optional[Path] = None,
    ):
        """Initialize resolver with configuration sources.

        Args:
            cli_args: Dictionary of CLI arguments (keys match Typer option names)
            yaml_config: Optional YAML configuration (loaded via load_config)
            env_vars: Optional environment variables (defaults to os.environ)
            root_dir: Optional root directory (defaults to package root)
        """
        self.cli_args = cli_args
        self.yaml_config = yaml_config or {}
        self.env_vars = env_vars or os.environ
        self.root_dir = root_dir

    def resolve(self) -> Context:
        """Apply precedence rules and return validated Context.

        Returns:
            Fully resolved and validated Context object

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Resolve each field independently with explicit precedence
        resolved_root_dir = self._resolve_root_dir()
        chromium_src = self._resolve_chromium_src()
        architecture = self._resolve_architecture()
        build_type = self._resolve_build_type()

        # Validate chromium_src exists (fail fast)
        self._validate_chromium_src(chromium_src)

        # Create and return Context
        return Context(
            root_dir=resolved_root_dir,
            chromium_src=chromium_src,
            architecture=architecture,
            build_type=build_type,
        )

    def _resolve_root_dir(self) -> Path:
        """Resolve root directory: CLI > YAML > Constructor > Current directory.

        Returns:
            Path to project root directory
        """
        # Priority 1: Constructor argument (set by build.py)
        if self.root_dir is not None:
            return self.root_dir

        # Priority 2: YAML config
        yaml_root = self.yaml_config.get("paths", {}).get("root_dir")
        if yaml_root:
            return Path(yaml_root)

        # Priority 3: Current directory
        return Path(".")

    def _resolve_chromium_src(self) -> Path:
        """Resolve chromium source directory: CLI > YAML > Env var > Error.

        Returns:
            Path to Chromium source directory

        Raises:
            ValueError: If chromium_src not provided by any source
        """
        # Priority 1: CLI argument
        cli_value = self.cli_args.get("chromium_src")
        if cli_value is not None:
            return Path(cli_value)

        # Priority 2: YAML config
        yaml_value = self.yaml_config.get("build", {}).get("chromium_src")
        if yaml_value:
            return Path(yaml_value)

        # Priority 3: Environment variable
        env_value = self.env_vars.get("CHROMIUM_SRC")
        if env_value:
            return Path(env_value)

        # No source provided chromium_src
        raise ValueError(
            "Chromium source directory required!\n"
            "Provide via one of:\n"
            "  --chromium-src PATH\n"
            "  config.yaml: build.chromium_src\n"
            "  CHROMIUM_SRC environment variable"
        )

    def _resolve_architecture(self) -> str:
        """Resolve target architecture: CLI > YAML > Platform default.

        Returns:
            Architecture string (e.g., 'arm64', 'x64', 'universal')

        Note:
            Logs when platform default is applied (not silent)
        """
        # Priority 1: CLI argument
        cli_value = self.cli_args.get("arch")
        if cli_value is not None:
            return cli_value

        # Priority 2: YAML config (support both 'arch' and 'architecture')
        yaml_build = self.yaml_config.get("build", {})
        yaml_value = yaml_build.get("arch") or yaml_build.get("architecture")
        if yaml_value:
            return yaml_value

        # Priority 3: Platform-specific default
        platform_arch = get_platform_arch()
        log_info(f"Using platform default architecture: {platform_arch}")
        return platform_arch

    def _resolve_build_type(self) -> str:
        """Resolve build type: CLI > YAML > 'debug' default.

        Returns:
            Build type string ('debug' or 'release')

        Note:
            CLI default is 'debug' from Typer, so YAML can't override unless
            user explicitly passes --build-type. This is a known limitation.
        """
        # Priority 1: CLI argument (includes CLI default of 'debug')
        cli_value = self.cli_args.get("build_type")
        if cli_value is not None:
            return cli_value

        # Priority 2: YAML config
        yaml_value = self.yaml_config.get("build", {}).get("type")
        if yaml_value:
            return yaml_value

        # Priority 3: Hardcoded default
        return "debug"

    def _validate_chromium_src(self, chromium_src: Path) -> None:
        """Validate that chromium_src directory exists.

        Args:
            chromium_src: Path to validate

        Raises:
            ValueError: If directory doesn't exist
        """
        if not chromium_src.exists():
            raise ValueError(
                f"Chromium source directory does not exist: {chromium_src}\n"
                f"Expected directory with Chromium source code"
            )


class PipelineResolver:
    """Resolves build pipeline from CLI flags, explicit modules, or YAML config.

    Three Pipeline Resolution Modes (mutually exclusive):
    1. YAML config file (--config FILE)
    2. Explicit module list (--modules clean,compile,sign)
    3. Phase flags (--setup --build --sign) with auto-ordering

    Phase Flag Design:
    - Flags are enable/disable toggles (not ordering instructions)
    - System enforces predetermined execution order regardless of flag order
    - Example: --sign --setup → always executes setup THEN sign

    Example:
        >>> cli_args = {"setup": True, "build": True, "sign": False}
        >>> pipeline = PipelineResolver.resolve(cli_args, execution_order=EXECUTION_ORDER)
        >>> # Returns: ["clean", "git_setup", "sparkle_setup", "configure", "compile"]
    """

    @staticmethod
    def resolve(
        cli_args: Dict[str, Any],
        yaml_config: Optional[Dict[str, Any]] = None,
        execution_order: Optional[List[Tuple[str, List[str]]]] = None,
    ) -> List[str]:
        """Resolve pipeline based on input mode.

        Args:
            cli_args: CLI arguments dictionary
            yaml_config: Optional YAML configuration
            execution_order: Required for flag-based resolution
                           List of (phase_name, module_list) tuples

        Returns:
            List of module names in execution order

        Raises:
            ValueError: If no pipeline specified, multiple modes used,
                       or flag mode used without execution_order
        """
        # Determine which resolution mode is active
        has_config = yaml_config is not None and "modules" in yaml_config
        has_modules = cli_args.get("modules") is not None
        has_flags = PipelineResolver._has_phase_flags(cli_args)

        # Enforce mutual exclusivity
        active_modes = sum([has_config, has_modules, has_flags])

        if active_modes == 0:
            raise ValueError(
                "No pipeline specified. Choose ONE of:\n"
                "  --config FILE          (YAML with modules list)\n"
                "  --modules clean,compile,...  (explicit module list)\n"
                "  --setup --build --sign       (phase flags, auto-ordered)"
            )

        if active_modes > 1:
            raise ValueError(
                "Multiple pipeline modes specified!\n"
                "Use only ONE of: --config, --modules, or phase flags"
            )

        # Resolve based on active mode
        if has_config:
            return PipelineResolver._resolve_from_config(yaml_config)

        if has_modules:
            return PipelineResolver._resolve_from_modules(cli_args)

        if has_flags:
            return PipelineResolver._resolve_from_flags(cli_args, execution_order)

        # Should never reach here due to active_modes check
        raise ValueError("Internal error: No pipeline resolution mode matched")

    @staticmethod
    def _has_phase_flags(cli_args: Dict[str, Any]) -> bool:
        """Check if any phase flags are set.

        Args:
            cli_args: CLI arguments dictionary

        Returns:
            True if any phase flag is True
        """
        phase_flags = ["setup", "prep", "build", "sign", "package", "upload"]
        return any(cli_args.get(flag, False) for flag in phase_flags)

    @staticmethod
    def _resolve_from_config(yaml_config: Dict[str, Any]) -> List[str]:
        """Resolve pipeline from YAML config.

        Args:
            yaml_config: YAML configuration with 'modules' key

        Returns:
            Module list from config
        """
        return yaml_config["modules"]

    @staticmethod
    def _resolve_from_modules(cli_args: Dict[str, Any]) -> List[str]:
        """Resolve pipeline from explicit --modules list.

        Args:
            cli_args: CLI arguments with 'modules' key

        Returns:
            Parsed and trimmed module list
        """
        modules_str = cli_args["modules"]
        return [m.strip() for m in modules_str.split(",")]

    @staticmethod
    def _resolve_from_flags(
        cli_args: Dict[str, Any],
        execution_order: Optional[List[Tuple[str, List[str]]]],
    ) -> List[str]:
        """Resolve pipeline from phase flags with fixed execution order.

        Args:
            cli_args: CLI arguments with phase flag keys
            execution_order: List of (phase_name, modules) defining order

        Returns:
            Module list in predetermined order

        Raises:
            ValueError: If execution_order not provided
        """
        if execution_order is None:
            raise ValueError(
                "execution_order required for flag-based pipeline resolution"
            )

        # Build enabled phases map
        enabled_phases = {
            "setup": cli_args.get("setup", False),
            "prep": cli_args.get("prep", False),
            "build": cli_args.get("build", False),
            "sign": cli_args.get("sign", False),
            "package": cli_args.get("package", False),
            "upload": cli_args.get("upload", False),
        }

        # Assemble pipeline in predetermined order
        pipeline = []
        for phase_name, phase_modules in execution_order:
            if enabled_phases.get(phase_name, False):
                # Extend with all modules in this phase
                pipeline.extend(phase_modules)

        return pipeline
