"""
Feature module - Manage feature-to-file mappings

Simple feature management with YAML persistence.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from ...common.context import BuildContext
from ..extract.utils import get_commit_changed_files, run_git_command
from ...common.utils import log_info, log_error, log_success, log_warning


def add_feature(ctx: BuildContext, feature_name: str, commit: str, description: Optional[str] = None) -> bool:
    """Add files from a commit to a feature

    Examples:
      dev feature add my-feature HEAD
      dev feature add llm-chat HEAD~3 --description "LLM chat integration"
    """
    features_file = ctx.get_features_yaml_path()

    # Get changed files from commit
    changed_files = get_commit_changed_files(ctx, commit)
    if not changed_files:
        log_error(f"No changed files found in commit {commit}")
        return False

    # Load existing features
    features: Dict = {"features": {}}
    if features_file.exists():
        with open(features_file, "r") as f:
            content = yaml.safe_load(f)
            if content and "features" in content:
                features = content

    # Add or update feature
    features["features"][feature_name] = {
        "description": description or f"Feature: {feature_name}",
        "files": sorted(changed_files),
        "commit": commit,
    }

    # Save to file
    with open(features_file, "w") as f:
        yaml.safe_dump(features, f, sort_keys=False, default_flow_style=False)

    log_success(f"✓ Added feature '{feature_name}' with {len(changed_files)} files")
    return True


def list_features(ctx: BuildContext):
    """List all defined features"""
    features_file = ctx.get_features_yaml_path()
    if not features_file.exists():
        log_warning("No features.yaml found")
        return

    with open(features_file, "r") as f:
        content = yaml.safe_load(f)
        if not content or "features" not in content:
            log_warning("No features defined")
            return

    features = content["features"]
    log_info(f"Features ({len(features)}):")
    log_info("-" * 60)

    for name, config in features.items():
        file_count = len(config.get("files", []))
        description = config.get("description", "")
        log_info(f"  {name}: {file_count} files - {description}")


def show_feature(ctx: BuildContext, feature_name: str):
    """Show details of a specific feature"""
    features_file = ctx.get_features_yaml_path()
    if not features_file.exists():
        log_error("No features.yaml found")
        return

    with open(features_file, "r") as f:
        content = yaml.safe_load(f)
        if not content or "features" not in content:
            log_error("No features defined")
            return

    features = content["features"]
    if feature_name not in features:
        log_error(f"Feature '{feature_name}' not found")
        log_info("Available features:")
        for name in features.keys():
            log_info(f"  - {name}")
        return

    feature = features[feature_name]
    log_info(f"Feature: {feature_name}")
    log_info("-" * 60)
    log_info(f"Description: {feature.get('description', '')}")
    log_info(f"Commit: {feature.get('commit', 'Unknown')}")
    log_info(f"Files ({len(feature.get('files', []))}):")
    for file_path in feature.get("files", []):
        log_info(f"  - {file_path}")