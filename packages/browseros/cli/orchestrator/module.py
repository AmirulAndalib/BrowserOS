"""Base module interface for the build system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Set, Optional
from enum import Enum


class Phase(str, Enum):
    """Build phases for ordering modules."""
    PREPARE = "prepare"
    BUILD = "build"
    SIGN = "sign"
    PACKAGE = "package"
    PUBLISH = "publish"


@dataclass
class StepResult:
    """Result of a module execution."""
    success: bool
    message: str = ""
    artifacts: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = {}
        if self.metadata is None:
            self.metadata = {}


class BuildModule(ABC):
    """Base class for all build modules."""

    def __init__(self):
        self.name: str = self.__class__.__name__.replace('Module', '').lower()
        self.phase: Phase = Phase.PREPARE
        self.default_order: int = 0
        self.requires: Set[str] = set()  # artifact ids required
        self.provides: Set[str] = set()  # artifact ids provided
        self.supported_platforms: Set[str] = {"macos", "linux", "windows"}
        self.supports_dry_run: bool = False

    @abstractmethod
    def should_run(self, ctx: 'BuildContext', step_cfg: Dict[str, Any]) -> bool:
        """Determine if this module should run in the current context."""
        pass

    @abstractmethod
    def run(self, ctx: 'BuildContext', step_cfg: Dict[str, Any]) -> StepResult:
        """Execute the module."""
        pass

    def validate_requirements(self, ctx: 'BuildContext') -> bool:
        """Check if required artifacts are available."""
        for req in self.requires:
            if req not in ctx.artifacts:
                return False
        return True