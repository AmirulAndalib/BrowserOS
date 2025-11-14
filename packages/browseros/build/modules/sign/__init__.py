"""
Platform-specific signing module for BrowserOS
Automatically imports the correct signing functions based on the platform
"""

from ...common.utils import IS_MACOS, IS_WINDOWS, IS_LINUX

# Import platform-specific functions
if IS_MACOS:
    from .macos import (
        sign,
        sign_universal,
        check_signing_environment,
        sign_app,
        notarize_app,
        verify_signature,
    )
elif IS_WINDOWS:
    from .windows import (
        sign,
        sign_binaries,
        sign_universal,
        check_signing_environment,
    )
elif IS_LINUX:
    from .linux import (
        sign,
        sign_binaries,
        sign_universal,
        check_signing_environment,
    )
else:
    # Fallback for unknown platforms
    def sign(ctx):
        from ...common.utils import log_warning
        log_warning(f"Signing not implemented for this platform")
        return True

    def sign_universal(contexts):
        from ...common.utils import log_warning
        log_warning(f"Universal signing not implemented for this platform")
        return True

    def check_signing_environment():
        return True

# Export the appropriate functions
__all__ = [
    'sign',
    'sign_universal',
    'check_signing_environment',
]

# Platform-specific exports
if IS_MACOS:
    __all__.extend(['sign_app', 'notarize_app', 'verify_signature'])
if IS_WINDOWS:
    __all__.append('sign_binaries')