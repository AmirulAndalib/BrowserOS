"""Platform-specific packaging module for BrowserOS"""

from ...common.utils import IS_MACOS, IS_WINDOWS, IS_LINUX

# Import module classes
if IS_MACOS():
    from .macos import MacOSPackageModule
elif IS_WINDOWS():
    from .windows import WindowsPackageModule
elif IS_LINUX():
    from .linux import LinuxPackageModule

# Import platform-specific functions
if IS_MACOS():
    from .macos import (
        package,
        package_universal,
        create_dmg,
    )
elif IS_WINDOWS():
    from .windows import (
        package,
        package_universal,
        create_installer,
        create_portable_zip,
        build_mini_installer,
    )
elif IS_LINUX():
    from .linux import (
        package,
        package_universal,
        package_appimage,
        package_deb,
    )
else:
    # Fallback for unknown platforms
    def package(ctx):
        from ...common.utils import log_warning
        log_warning(f"Packaging not implemented for this platform")
        return True

    def package_universal(contexts):
        from ...common.utils import log_warning
        log_warning(f"Universal packaging not implemented for this platform")
        return True

# Export module classes and functions
__all__ = [
    'package',
    'package_universal',
]

# Platform-specific module class and function exports
if IS_MACOS():
    __all__.extend(['MacOSPackageModule', 'create_dmg'])
elif IS_WINDOWS():
    __all__.extend(['WindowsPackageModule', 'create_installer', 'create_portable_zip', 'build_mini_installer'])
elif IS_LINUX():
    __all__.extend(['LinuxPackageModule', 'package_appimage', 'package_deb'])