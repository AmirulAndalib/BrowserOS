#!/usr/bin/env python3
"""
Build context dataclass to hold all build state
"""

import time
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List
from .utils import (
    log_error,
    log_warning,
    get_platform,
    get_platform_arch,
    get_executable_extension,
    join_paths,
    IS_WINDOWS,
    IS_MACOS,
)


class ArtifactType(str, Enum):
    """Well-known artifact types produced during build"""

    # Signing outputs
    SIGNED_APP = "sign:app"
    SIGNED_DMG = "sign:dmg"
    SIGNED_INSTALLER = "sign:installer"
    SIGNED_APPIMAGE = "sign:appimage"
    NOTARIZATION_ZIP = "sign:notarization_zip"

    # Packaging outputs
    PACKAGE_DMG = "package:dmg"
    PACKAGE_INSTALLER = "package:installer"
    PACKAGE_APPIMAGE = "package:appimage"
    PACKAGE_UNIVERSAL = "package:universal"

    # Build outputs
    BUILD_APP = "build:app"
    BUILD_BINARY = "build:binary"


@dataclass
class BuildContext:
    """Context Object pattern - ONE place for all build state"""

    root_dir: Path
    chromium_src: Path = Path()
    out_dir: str = "out/Default"
    architecture: str = ""  # Will be set in __post_init__
    build_type: str = "debug"
    apply_patches: bool = False
    sign_package: bool = False
    package: bool = False
    build: bool = False
    chromium_version: str = ""
    browseros_version: str = ""
    browseros_chromium_version: str = ""
    start_time: float = 0.0

    # App names - will be set based on platform
    CHROMIUM_APP_NAME: str = ""
    BROWSEROS_APP_NAME: str = ""
    BROWSEROS_APP_BASE_NAME: str = "BrowserOS"  # Base name without extension

    # Third party
    SPARKLE_VERSION: str = "2.7.0"

    # Build artifacts (steps populate this)
    artifacts: Dict[str, List[Path]] = field(default_factory=dict)

    def __post_init__(self):
        """Load version files and set platform/architecture-specific configurations"""
        # Set platform-specific defaults
        if not self.architecture:
            self.architecture = get_platform_arch()

        # Set platform-specific app names
        if IS_WINDOWS():
            self.CHROMIUM_APP_NAME = f"chrome{get_executable_extension()}"
            self.BROWSEROS_APP_NAME = (
                f"{self.BROWSEROS_APP_BASE_NAME}{get_executable_extension()}"
            )
        elif IS_MACOS():
            self.CHROMIUM_APP_NAME = "Chromium.app"
            self.BROWSEROS_APP_NAME = f"{self.BROWSEROS_APP_BASE_NAME}.app"
        else:
            self.CHROMIUM_APP_NAME = "chrome"
            self.BROWSEROS_APP_NAME = self.BROWSEROS_APP_BASE_NAME.lower()

        # Set architecture-specific output directory with platform separator
        if IS_WINDOWS():
            self.out_dir = f"out\\Default_{self.architecture}"
        else:
            self.out_dir = f"out/Default_{self.architecture}"

        # Load version information using static methods
        if not self.chromium_version:
            self.chromium_version, version_dict = self._load_chromium_version(
                self.root_dir
            )
        else:
            # If chromium_version was provided, we still need to parse it for version_dict
            version_dict = {}

        if not self.browseros_version:
            self.browseros_version = self._load_browseros_version(self.root_dir)

        # Set nxtscape_chromium_version as chromium version with BUILD + nxtscape_version
        if self.chromium_version and self.browseros_version and version_dict:
            # Calculate new BUILD number by adding nxtscape_version to original BUILD
            new_build = int(version_dict["BUILD"]) + int(self.browseros_version)
            self.browseros_chromium_version = f"{version_dict['MAJOR']}.{version_dict['MINOR']}.{new_build}.{version_dict['PATCH']}"

        # Determine chromium source directory
        if self.chromium_src and self.chromium_src.exists():
            log_warning(f"📁 Using provided Chromium source: {self.chromium_src}")
        else:
            log_warning(f"⚠️  Provided path does not exist: {self.chromium_src}")
            self.chromium_src = join_paths(self.root_dir, "chromium_src")
            if not self.chromium_src.exists():
                log_error(
                    f"⚠️  Default Chromium source path does not exist: {self.chromium_src}"
                )
                raise FileNotFoundError(
                    f"Chromium source path does not exist: {self.chromium_src}"
                )

        self.start_time = time.time()

    # === Artifact Management ===

    def add_artifact(self, artifact_type: ArtifactType, path: Path):
        """Add an artifact to tracking"""
        key = artifact_type.value
        if key not in self.artifacts:
            self.artifacts[key] = []
        self.artifacts[key].append(path)

    def get_artifacts(self, artifact_type: ArtifactType) -> List[Path]:
        """Get all artifacts of a type"""
        return self.artifacts.get(artifact_type.value, [])

    def has_artifact(self, artifact_type: ArtifactType) -> bool:
        """Check if artifact type exists"""
        return artifact_type.value in self.artifacts

    # === Initialization ===

    @classmethod
    def init_context(cls, config: Dict) -> "BuildContext":
        """
        Initialize context from config
        Replaces __post_init__ logic for better testability
        """
        from typing import Any

        root_dir = Path(config.get("root_dir", Path.cwd()))
        chromium_src = (
            Path(config.get("chromium_src", ""))
            if config.get("chromium_src")
            else Path()
        )

        # Get architecture or use platform default
        arch = config.get("architecture") or get_platform_arch()

        # Create instance
        ctx = cls(
            root_dir=root_dir,
            chromium_src=chromium_src,
            architecture=arch,
            build_type=config.get("build_type", "debug"),
            apply_patches=config.get("apply_patches", False),
            sign_package=config.get("sign_package", False),
            package=config.get("package", False),
            build=config.get("build", False),
        )

        return ctx

    @staticmethod
    def _load_chromium_version(root_dir: Path):
        """
        Load chromium version from CHROMIUM_VERSION file
        Returns: (version_string, version_dict)
        """
        version_dict = {}
        version_file = join_paths(root_dir, "CHROMIUM_VERSION")

        if version_file.exists():
            # Parse VERSION file format: MAJOR=137\nMINOR=0\nBUILD=7151\nPATCH=69
            for line in version_file.read_text().strip().split("\n"):
                key, value = line.split("=")
                version_dict[key] = value

            # Construct chromium_version as MAJOR.MINOR.BUILD.PATCH
            chromium_version = f"{version_dict['MAJOR']}.{version_dict['MINOR']}.{version_dict['BUILD']}.{version_dict['PATCH']}"
            return chromium_version, version_dict

        return "", version_dict

    @staticmethod
    def _load_browseros_version(root_dir: Path) -> str:
        """Load browseros version from config/BROWSEROS_VERSION"""
        version_file = join_paths(root_dir, "build", "config", "BROWSEROS_VERSION")
        if version_file.exists():
            return version_file.read_text().strip()
        return ""

    # Path getter methods
    def get_config_dir(self) -> Path:
        """Get build config directory"""
        return join_paths(self.root_dir, "build", "config")

    def get_gn_config_dir(self) -> Path:
        """Get GN config directory"""
        return join_paths(self.get_config_dir(), "gn")

    def get_gn_flags_file(self) -> Path:
        """Get GN flags file for current build type"""
        platform = get_platform()
        return join_paths(
            self.get_gn_config_dir(), f"flags.{platform}.{self.build_type}.gn"
        )

    def get_copy_resources_config(self) -> Path:
        """Get copy resources configuration file"""
        return join_paths(self.get_config_dir(), "copy_resources.yaml")

    def get_patches_dir(self) -> Path:
        """Get patches directory"""
        return join_paths(self.root_dir, "patches")

    def get_browseros_patches_dir(self) -> Path:
        """Get browseros specific patches directory"""
        return join_paths(self.get_patches_dir(), "browseros")

    def get_sparkle_dir(self) -> Path:
        """Get Sparkle directory"""
        return join_paths(self.chromium_src, "third_party", "sparkle")

    def get_sparkle_url(self) -> str:
        """Get Sparkle download URL"""
        return f"https://github.com/sparkle-project/Sparkle/releases/download/{self.SPARKLE_VERSION}/Sparkle-{self.SPARKLE_VERSION}.tar.xz"

    def get_entitlements_dir(self) -> Path:
        """Get entitlements directory"""
        return join_paths(self.root_dir, "resources", "entitlements")

    def get_pkg_dmg_path(self) -> Path:
        """Get pkg-dmg tool path (macOS only)"""
        return join_paths(self.chromium_src, "chrome", "installer", "mac", "pkg-dmg")

    def get_app_path(self) -> Path:
        """Get built app path"""
        # For debug builds, check if the app has a different name
        if self.build_type == "debug" and IS_MACOS():
            # Check for debug-branded app name
            debug_app_name = f"{self.BROWSEROS_APP_BASE_NAME} Dev.app"
            debug_app_path = join_paths(self.chromium_src, self.out_dir, debug_app_name)
            if debug_app_path.exists():
                return debug_app_path
        return join_paths(self.chromium_src, self.out_dir, self.BROWSEROS_APP_NAME)

    def get_chromium_app_path(self) -> Path:
        """Get original Chromium app path"""
        return join_paths(self.chromium_src, self.out_dir, self.CHROMIUM_APP_NAME)

    def get_gn_args_file(self) -> Path:
        """Get GN args file path"""
        return join_paths(self.chromium_src, self.out_dir, "args.gn")

    def get_notarization_zip(self) -> Path:
        """Get notarization zip path (macOS only)"""
        return join_paths(self.chromium_src, self.out_dir, "notarize.zip")

    def get_dmg_name(self, signed=False) -> str:
        """Get DMG filename with architecture suffix"""
        if self.architecture == "universal":
            if signed:
                return f"{self.BROWSEROS_APP_BASE_NAME}_{self.browseros_chromium_version}_universal_signed.dmg"
            return f"{self.BROWSEROS_APP_BASE_NAME}_{self.browseros_chromium_version}_universal.dmg"
        else:
            if signed:
                return f"{self.BROWSEROS_APP_BASE_NAME}_{self.browseros_chromium_version}_{self.architecture}_signed.dmg"
            return f"{self.BROWSEROS_APP_BASE_NAME}_{self.browseros_chromium_version}_{self.architecture}.dmg"

    def get_browseros_chromium_version(self) -> str:
        """Get browseros chromium version string"""
        return self.browseros_chromium_version

    def get_browseros_version(self) -> str:
        """Get browseros version string"""
        return self.browseros_version

    def get_app_base_name(self) -> str:
        """Get app base name without extension"""
        return self.BROWSEROS_APP_BASE_NAME

    def get_dist_dir(self) -> Path:
        """Get distribution output directory with version"""
        return join_paths(self.root_dir, "dist", self.browseros_version)

    # Dev CLI specific methods
    def get_dev_patches_dir(self) -> Path:
        """Get individual patches directory"""
        return join_paths(self.root_dir, "chromium_patches")

    def get_chromium_replace_files_dir(self) -> Path:
        """Get chromium files replacement directory"""
        return join_paths(self.root_dir, "chromium_files")

    def get_features_yaml_path(self) -> Path:
        """Get features.yaml file path"""
        return join_paths(self.root_dir, "features.yaml")

    def get_patch_path_for_file(self, file_path: str) -> Path:
        """Convert a chromium file path to patch file path"""
        return join_paths(self.get_dev_patches_dir(), file_path)
