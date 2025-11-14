"""Build plan creation and validation."""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from cli.orchestrator.context import BuildContext
from cli.orchestrator.module import BuildModule


@dataclass
class BuildStep:
    """A single step in the build plan."""
    module_name: str
    module: BuildModule
    config: Dict[str, Any]
    order: int


@dataclass
class BuildPlan:
    """Complete build execution plan."""
    steps: List[BuildStep]
    context: BuildContext
    pipeline_name: str = ""

    def validate(self) -> bool:
        """Validate that all dependencies are satisfied."""
        available_artifacts = set()

        for step in self.steps:
            # Check requirements are met
            missing = step.module.requires - available_artifacts
            if missing:
                print(f"Module {step.module_name} missing requirements: {missing}")
                return False

            # Add provided artifacts
            available_artifacts.update(step.module.provides)

        return True


class PlanBuilder:
    """Build execution plans from configuration."""

    def build_plan(self, config: Dict[str, Any], ctx: BuildContext) -> BuildPlan:
        """Build execution plan from pipeline config and context."""
        from cli.modules.registry import get_module

        # Get the actual pipeline config if it's nested
        pipeline_config = self._extract_pipeline_config(config, ctx)

        # Apply environment variables to context
        if "env" in pipeline_config:
            for key, value in pipeline_config["env"].items():
                # Expand ${VAR} references
                if isinstance(value, str) and "${" in value:
                    import re
                    pattern = re.compile(r'\$\{(\w+)\}')
                    value = pattern.sub(lambda m: ctx.env_overrides.get(m.group(1), m.group(0)), value)
                ctx.env_overrides[key] = value

        steps = []
        step_configs = self._get_steps_from_config(pipeline_config, ctx)

        for idx, step_config in enumerate(step_configs):
            if isinstance(step_config, str):
                module_name = step_config
                module_config = {}
            elif isinstance(step_config, dict):
                # Step can be {"module_name": {config}} or {"name": "module_name", ...config}
                if "name" in step_config:
                    module_name = step_config.pop("name")
                    module_config = step_config
                else:
                    # Single key dict like {"sign-mac": {...}}
                    module_name = list(step_config.keys())[0]
                    module_config = step_config[module_name] if isinstance(step_config[module_name], dict) else {}
            else:
                continue

            # Handle platform-specific module resolution
            module_name = self._resolve_platform_module(module_name, ctx.platform)

            # Skip if module should not run
            if ctx.should_skip(module_name):
                continue

            # Get module instance
            try:
                module = get_module(module_name)
            except ValueError:
                print(f"Warning: Unknown module '{module_name}', skipping")
                continue

            # Check if module should run
            if not module.should_run(ctx, module_config):
                continue

            # Check when conditions
            if not self._evaluate_when(module_config.get("when"), ctx):
                continue

            steps.append(BuildStep(
                module_name=module_name,
                module=module,
                config=module_config,
                order=idx
            ))

        plan = BuildPlan(
            steps=steps,
            context=ctx,
            pipeline_name=pipeline_config.get("description", config.get("name", "unnamed"))
        )

        return plan

    def _extract_pipeline_config(self, config: Dict[str, Any], ctx: BuildContext) -> Dict[str, Any]:
        """Extract the actual pipeline configuration."""
        # If config has 'pipelines' key, extract the specific pipeline
        if "pipelines" in config:
            pipelines = config["pipelines"]
            # Get the first pipeline if not specified
            if pipelines:
                pipeline_name = list(pipelines.keys())[0]
                return pipelines[pipeline_name]

        # Otherwise return the config as-is
        return config

    def _get_steps_from_config(self, config: Dict[str, Any], ctx: BuildContext) -> List[Any]:
        """Extract steps from configuration."""
        # Only support new format: steps must be a list
        if "steps" in config and isinstance(config["steps"], list):
            return config["steps"]

        # No steps defined
        return []

    def _resolve_platform_module(self, module_name: str, platform: str) -> str:
        """Resolve generic module names to platform-specific ones."""
        platform_map = {
            "sign": {
                "macos": "sign-mac",
                "windows": "sign-windows",
                "linux": "sign-linux"
            },
            "package": {
                "macos": "package-mac",
                "windows": "package-windows",
                "linux": "package-linux"
            }
        }

        if module_name in platform_map and platform in platform_map[module_name]:
            return platform_map[module_name][platform]

        return module_name

    def _evaluate_when(self, when_expr: Optional[str], ctx: BuildContext) -> bool:
        """Evaluate simple when expressions."""
        if not when_expr:
            return True

        # Simple equality check for now
        # Format: "arch == 'universal'" or "build_type == 'release'"
        if "==" in when_expr:
            left, right = when_expr.split("==")
            left = left.strip()
            right = right.strip().strip("'\"")

            if left == "arch":
                return ctx.architecture == right
            elif left == "build_type":
                return ctx.build_type == right
            elif left == "platform" or left == "os":
                return ctx.platform == right

        # in/not in checks
        if " in " in when_expr:
            var, values = when_expr.split(" in ")
            var = var.strip()
            values = eval(values.strip())  # Simple eval for lists

            if var == "arch":
                return ctx.architecture in values
            elif var == "build_type":
                return ctx.build_type in values
            elif var == "platform" or var == "os":
                return ctx.platform in values

        if " not in " in when_expr:
            var, values = when_expr.split(" not in ")
            var = var.strip()
            values = eval(values.strip())

            if var == "arch":
                return ctx.architecture not in values
            elif var == "build_type":
                return ctx.build_type not in values
            elif var == "platform" or var == "os":
                return ctx.platform not in values

        # Default to true if we can't evaluate
        return True