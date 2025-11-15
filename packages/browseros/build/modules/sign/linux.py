#!/usr/bin/env python3
"""Linux signing module for BrowserOS"""

from typing import List
from ...common.module import BuildModule
from ...common.context import BuildContext
from ...common.utils import log_info, log_warning


class LinuxSignModule(BuildModule):
    produces = []
    requires = []
    description = "Linux code signing (no-op)"

    def validate(self, ctx: BuildContext) -> None:
        pass

    def execute(self, ctx: BuildContext) -> None:
        log_info("Code signing is not required for Linux packages")


def sign(ctx: BuildContext) -> bool:
    """Legacy function interface"""
    module = LinuxSignModule()
    module.validate(ctx)
    module.execute(ctx)
    return True


def sign_binaries(ctx: BuildContext) -> bool:
    """Legacy function interface"""
    return sign(ctx)


def sign_universal(contexts: List[BuildContext]) -> bool:
    """Linux doesn't support universal binaries"""
    log_warning("Universal signing is not supported on Linux")
    return True


def check_signing_environment() -> bool:
    """Linux doesn't require signing environment"""
    return True