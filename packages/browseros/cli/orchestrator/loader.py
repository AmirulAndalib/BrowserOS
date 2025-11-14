"""Configuration loader for pipeline YAML files."""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml
from dotenv import dotenv_values, find_dotenv


class ConfigLoader:
    """Load and parse pipeline configuration files."""

    def __init__(self, env_file: Optional[Path] = None):
        self.env_vars = os.environ.copy()
        self._load_env_file(env_file)

    def _load_env_file(self, env_file: Optional[Path]):
        """Load environment variables from a .env file using python-dotenv."""
        env_path = env_file or find_dotenv(usecwd=True)
        if not env_path:
            return

        for key, value in dotenv_values(env_path).items():
            if value is not None:
                self.env_vars[key] = value

    def load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load pipeline configuration from YAML file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Resolve environment variables in config
        config = self._resolve_env_vars(config)

        return config

    def _resolve_env_vars(self, obj: Any) -> Any:
        """Recursively resolve ${VAR} placeholders in config."""
        if isinstance(obj, str):
            return self._expand_vars(obj)
        elif isinstance(obj, dict):
            return {k: self._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars(item) for item in obj]
        else:
            return obj

    def _expand_vars(self, text: str) -> str:
        """Expand ${VAR} placeholders with environment values."""
        pattern = re.compile(r'\$\{(\w+)\}')

        def replacer(match):
            var_name = match.group(1)
            return self.env_vars.get(var_name, match.group(0))

        return pattern.sub(replacer, text)

    def get_pipeline_config(self, config: Dict[str, Any], pipeline_name: str) -> Dict[str, Any]:
        """Extract specific pipeline configuration."""
        pipelines = config.get("pipelines", {})
        if pipeline_name not in pipelines:
            available = ", ".join(pipelines.keys())
            raise ValueError(f"Pipeline '{pipeline_name}' not found. Available: {available}")

        return pipelines[pipeline_name]

    def expand_matrix(self, pipeline_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Expand matrix configuration into individual build configs."""
        matrix = pipeline_config.get("matrix", {})
        architectures = matrix.get("architectures", ["x64"])

        configs = []
        for arch in architectures:
            config = pipeline_config.copy()
            config["architecture"] = arch
            configs.append(config)

        # Add universal build if specified
        if matrix.get("universal") and len(architectures) > 1:
            universal_config = pipeline_config.copy()
            universal_config["architecture"] = "universal"
            universal_config["source_architectures"] = architectures
            configs.append(universal_config)

        return configs
