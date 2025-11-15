"""
Common modules for the BrowserOS build system
"""

from .context import BuildContext, ArtifactRegistry, PathConfig, BuildConfig
from .config import load_config, merge_config, load_config_or_defaults, expand_env_vars
from .notify import Notifier, NullNotifier, SlackNotifier, ConsoleNotifier
from .module import BuildModule, ValidationError
from .env import EnvConfig

__all__ = [
    # Core context
    'BuildContext',
    # New sub-components
    'ArtifactRegistry',
    'PathConfig',
    'BuildConfig',
    'BuildModule',
    'ValidationError',
    'EnvConfig',
    # Config loading
    'load_config',
    'merge_config',
    'load_config_or_defaults',
    'expand_env_vars',
    # Notifications
    'Notifier',
    'NullNotifier',
    'SlackNotifier',
    'ConsoleNotifier',
]