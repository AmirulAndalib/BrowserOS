"""Build and pipeline context objects."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, List
import os


@dataclass
class PipelineContext:
    """Root context shared across all builds in a pipeline."""

    root_path: Path
    config_path: Path
    config_hash: str = ""
    slack_enabled: bool = False
    slack_client: Optional[Any] = None
    env_overrides: Dict[str, str] = field(default_factory=dict)
    dry_run: bool = False

    def __post_init__(self):
        """Ensure paths are Path objects."""
        self.root_path = Path(self.root_path)
        self.config_path = Path(self.config_path)


@dataclass
class BuildContext:
    """Per-architecture/per-plan execution context."""

    pipeline_ctx: PipelineContext
    architecture: str
    build_type: str  # release, debug
    platform: str  # macos, linux, windows

    # Build paths
    chromium_path: Path = None
    output_path: Path = None

    # Runtime state
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    env_overrides: Dict[str, str] = field(default_factory=dict)

    # Flags from CLI or config
    skip_modules: List[str] = field(default_factory=list)
    only_modules: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize computed paths."""
        # Chromium path must be explicitly provided
        if self.chromium_path is not None:
            self.chromium_path = Path(self.chromium_path)

        if self.output_path is None and self.chromium_path is not None:
            self.output_path = self.chromium_path / "out" / f"{self.build_type}_{self.architecture}"

        # Merge environment overrides
        self.env_overrides = {
            **self.pipeline_ctx.env_overrides,
            **self.env_overrides
        }

    def get_env(self) -> Dict[str, str]:
        """Get the full environment with overrides applied."""
        env = os.environ.copy()
        env.update(self.env_overrides)
        return env

    def should_skip(self, module_name: str) -> bool:
        """Check if a module should be skipped."""
        if self.skip_modules and module_name in self.skip_modules:
            return True
        if self.only_modules and module_name not in self.only_modules:
            return True
        return False