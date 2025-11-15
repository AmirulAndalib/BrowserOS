"""Build system modules"""

from .compile import CompileModule, build
from ..common.utils import IS_MACOS, IS_WINDOWS, IS_LINUX

# Import sign module classes
if IS_MACOS():
    from .sign import MacOSSignModule
elif IS_WINDOWS():
    from .sign import WindowsSignModule
elif IS_LINUX():
    from .sign import LinuxSignModule

# Import package module classes
if IS_MACOS():
    from .package import MacOSPackageModule
elif IS_WINDOWS():
    from .package import WindowsPackageModule
elif IS_LINUX():
    from .package import LinuxPackageModule

__all__ = [
    "CompileModule",
    "build",
]

# Add platform-specific module classes to exports
if IS_MACOS():
    __all__.extend(["MacOSSignModule", "MacOSPackageModule"])
elif IS_WINDOWS():
    __all__.extend(["WindowsSignModule", "WindowsPackageModule"])
elif IS_LINUX():
    __all__.extend(["LinuxSignModule", "LinuxPackageModule"])
