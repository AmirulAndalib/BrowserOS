"""Configuration loader for pipeline YAML files."""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional


class ConfigLoader:
    """Load and parse pipeline configuration files."""

    def __init__(self):
        self.env_vars = os.environ.copy()
        self._load_env_file()

    def _load_env_file(self):
        """Load .env file if it exists."""
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, _, value = line.partition("=")
                        if key and value:
                            self.env_vars[key.strip()] = value.strip()

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