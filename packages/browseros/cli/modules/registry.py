"""Module registry - explicit mapping of all available modules."""

from typing import Dict, Type, Optional
from cli.orchestrator.module import BuildModule

# Import all modules
from cli.modules.common.clean import CleanModule
from cli.modules.setup.env import SetupEnvModule
from cli.modules.common.git import GitSyncModule
from cli.modules.patches.chromium import PatchChromiumModule
from cli.modules.patches.strings import PatchStringsModule
from cli.modules.patches.sparkle import PatchSparkleModule
from cli.modules.patches.apply import PatchApplyModule
from cli.modules.common.resources import CopyResourcesModule
from cli.modules.build.configure import ConfigureModule
from cli.modules.build.compile import CompileModule
from cli.modules.build.merge import MergeUniversalModule
from cli.modules.publish.gcs import UploadGcsModule

# Platform-specific modules
from cli.modules.sign.mac import SignMacModule, SignMacUniversalModule
from cli.modules.sign.windows import SignWindowsModule, SignWindowsInstallerModule
from cli.modules.sign.linux import SignLinuxModule
from cli.modules.package.mac import PackageMacModule, PackageMacUniversalModule
from cli.modules.package.windows import PackageWindowsModule
from cli.modules.package.linux import PackageLinuxModule


# Explicit module mapping - clear and debuggable
MODULES: Dict[str, Type[BuildModule]] = {
    # Common modules
    "clean": CleanModule,
    "setup-env": SetupEnvModule,
    "git-sync": GitSyncModule,
    "copy-resources": CopyResourcesModule,

    # Patch modules
    "patch-chromium": PatchChromiumModule,
    "patch-strings": PatchStringsModule,
    "patch-sparkle": PatchSparkleModule,
    "patch-apply": PatchApplyModule,

    # Build modules
    "configure": ConfigureModule,
    "build": CompileModule,
    "merge-universal": MergeUniversalModule,

    # Sign modules (platform-specific)
    "sign-mac": SignMacModule,
    "sign-mac-universal": SignMacUniversalModule,
    "sign-windows": SignWindowsModule,
    "sign-windows-installer": SignWindowsInstallerModule,
    "sign-linux": SignLinuxModule,
    # Future: "sign-mac-browseros-resources": SignMacBrowserOSResourcesModule,
    # Future: "sign-windows-browseros-resources": SignWindowsBrowserOSResourcesModule,

    # Package modules (platform-specific)
    "package-mac": PackageMacModule,
    "package-mac-universal": PackageMacUniversalModule,
    "package-windows": PackageWindowsModule,
    "package-linux": PackageLinuxModule,

    # Publish modules
    "upload-gcs": UploadGcsModule,
    # Future: "upload-aws": UploadAwsModule,
    # Future: "upload-ssh": UploadSshModule,
}


def get_module(name: str) -> BuildModule:
    """Get module instance by name.

    Args:
        name: Module name to retrieve

    Returns:
        Module instance

    Raises:
        ValueError: If module name is not found
    """
    if name not in MODULES:
        available = ", ".join(sorted(MODULES.keys()))
        raise ValueError(
            f"Unknown module: '{name}'. Available modules: {available}"
        )

    module_class = MODULES[name]
    return module_class()


def list_modules() -> Dict[str, Type[BuildModule]]:
    """Get all registered modules.

    Returns:
        Dictionary of module name to module class
    """
    return MODULES.copy()


def register_module(name: str, module_class: Type[BuildModule]) -> None:
    """Register a new module.

    Args:
        name: Module name
        module_class: Module class to register
    """
    if name in MODULES:
        print(f"Warning: Overwriting existing module '{name}'")

    MODULES[name] = module_class


def get_modules_by_phase(phase: str) -> Dict[str, Type[BuildModule]]:
    """Get all modules for a specific phase.

    Args:
        phase: Phase name (prepare, build, sign, package, publish)

    Returns:
        Dictionary of module name to module class for the phase
    """
    result = {}
    for name, module_class in MODULES.items():
        # Create temporary instance to check phase
        instance = module_class()
        if instance.phase == phase:
            result[name] = module_class
    return result


def get_modules_for_platform(platform: str) -> Dict[str, Type[BuildModule]]:
    """Get all modules that support a specific platform.

    Args:
        platform: Platform name (macos, linux, windows)

    Returns:
        Dictionary of module name to module class for the platform
    """
    result = {}
    for name, module_class in MODULES.items():
        # Create temporary instance to check supported platforms
        instance = module_class()
        if platform in instance.supported_platforms:
            result[name] = module_class
    return result