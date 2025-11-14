#!/usr/bin/env python3
"""
Linux signing module for BrowserOS
Linux doesn't require code signing like macOS/Windows
"""

from typing import List
from ...common.context import BuildContext
from ...utils import log_info, log_warning


def sign(ctx: BuildContext) -> bool:
    """Wrapper for compatibility - calls sign_binaries"""
    return sign_binaries(ctx)


def sign_binaries(ctx: BuildContext) -> bool:
    """Linux doesn't require code signing like macOS/Windows"""
    log_info("Code signing is not required for Linux packages")
    return True


def sign_universal(contexts: List[BuildContext]) -> bool:
    """Linux doesn't support universal binaries"""
    log_warning("Universal signing is not supported on Linux")
    return True


def check_signing_environment() -> bool:
    """Linux doesn't require signing environment"""
    return True