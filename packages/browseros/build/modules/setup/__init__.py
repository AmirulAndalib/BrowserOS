"""Setup modules for BrowserOS build system"""

from .clean import CleanModule, clean, clean_sparkle, git_reset
from .git import GitSetupModule, SparkleSetupModule, setup_git, setup_sparkle
from .configure import ConfigureModule, configure

__all__ = [
    "CleanModule",
    "GitSetupModule",
    "SparkleSetupModule",
    "ConfigureModule",
    "clean",
    "clean_sparkle",
    "git_reset",
    "setup_git",
    "setup_sparkle",
    "configure",
]
