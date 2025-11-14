"""
Platform-specific packaging module for BrowserOS
Automatically imports the correct packaging functions based on the platform
"""

from ...common.utils import IS_MACOS, IS_WINDOWS, IS_LINUX

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
        create_appimage,
        create_deb,
        create_tar,
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

# Export the common functions
__all__ = [
    'package',
    'package_universal',
]

# Platform-specific exports
if IS_MACOS():
    __all__.append('create_dmg')
if IS_WINDOWS():
    __all__.extend(['create_installer', 'create_portable_zip', 'build_mini_installer'])
if IS_LINUX():
    __all__.extend(['create_appimage', 'create_deb', 'create_tar'])