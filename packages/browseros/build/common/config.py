#!/usr/bin/env python3
"""
Config loading and management with environment variable expansion
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict


def load_config(config_path: Path) -> Dict:
    """Load YAML config with environment variable expansion"""
    from ..utils import log_warning

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        raw_content = f.read()

    # Expand environment variables
    expanded_content = expand_env_vars(raw_content)

    config = yaml.safe_load(expanded_content)

    # Basic validation
    if 'version' not in config:
        log_warning("Config missing version field, assuming v1")

    validate_config(config)

    return config


def expand_env_vars(content: str) -> str:
    """Expand ${VAR} and ${VAR:-default} patterns"""

    def replace_var(match):
        var_expr = match.group(1)

        # Handle ${VAR:-default}
        if ':-' in var_expr:
            var_name, default = var_expr.split(':-', 1)
            return os.environ.get(var_name.strip(), default.strip())

        # Handle ${VAR}
        var_name = var_expr.strip()
        if var_name not in os.environ:
            raise ValueError(f"Environment variable not set: {var_name}")
        return os.environ[var_name]

    return re.sub(r'\$\{([^}]+)\}', replace_var, content)


def validate_config(config: Dict):
    """Basic config validation (no Pydantic yet)"""

    # For now, minimal validation - configs vary by use case
    # Will add more validation as we understand the config structure better
    if not isinstance(config, dict):
        raise ValueError("Config must be a dictionary")

    # Specific validation can be added based on config schema requirements


def merge_config(file_config: Dict, cli_overrides: Dict) -> Dict:
    """Merge CLI arguments over file config"""

    merged = file_config.copy()

    # Simple merge logic - CLI takes precedence
    for key, value in cli_overrides.items():
        if value is not None:  # Only override if CLI value provided
            merged[key] = value

    return merged


def load_config_or_defaults(config_path: Path = None) -> Dict:
    """
    Load config from file or return sensible defaults
    Used when config is optional
    """
    if config_path and config_path.exists():
        return load_config(config_path)

    # Return minimal default config
    return {
        'version': 1,
        'build': {
            'type': 'debug'
        },
        'paths': {},
        'steps': {}
    }