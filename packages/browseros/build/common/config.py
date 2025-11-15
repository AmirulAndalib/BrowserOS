#!/usr/bin/env python3
"""YAML configuration parser with environment variable substitution"""

import os
import re
import yaml
from pathlib import Path
from typing import Any, Dict
from .utils import log_info, log_error


def substitute_env_vars(value: Any) -> Any:
    """Recursively substitute environment variables in config values
    
    Supports ${VAR_NAME} syntax for environment variables
    """
    if isinstance(value, str):
        # Find all ${VAR} patterns
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, value)
        
        result = value
        for var_name in matches:
            env_value = os.environ.get(var_name, '')
            result = result.replace(f'${{{var_name}}}', env_value)
        
        return result
    
    elif isinstance(value, dict):
        return {k: substitute_env_vars(v) for k, v in value.items()}
    
    elif isinstance(value, list):
        return [substitute_env_vars(item) for item in value]
    
    else:
        return value


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load and parse YAML config file with environment variable substitution"""
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    log_info(f"Loading config from: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Substitute environment variables
    config = substitute_env_vars(config)
    
    return config


def validate_required_envs(required_envs: list) -> None:
    """Validate that all required environment variables are set
    
    Raises SystemExit if any are missing
    """
    missing = []
    for env_var in required_envs:
        if not os.environ.get(env_var):
            missing.append(env_var)
    
    if missing:
        log_error("Missing required environment variables:")
        for var in missing:
            log_error(f"  - {var}")
        log_error("\nSet these variables and try again")
        raise SystemExit(1)
