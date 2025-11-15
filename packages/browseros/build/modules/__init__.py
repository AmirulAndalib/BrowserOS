"""Build system modules"""

from .compile import CompileModule, build

# Import all module classes (platform checks happen at validation time)
from .sign.macos import MacOSSignModule
from .sign.windows import WindowsSignModule
from .sign.linux import LinuxSignModule
from .package.macos import MacOSPackageModule
from .package.windows import WindowsPackageModule
from .package.linux import LinuxPackageModule

__all__ = [
    "CompileModule",
    "build",
    # Sign modules
    "MacOSSignModule",
    "WindowsSignModule",
    "LinuxSignModule",
    # Package modules
    "MacOSPackageModule",
    "WindowsPackageModule",
    "LinuxPackageModule",
]
