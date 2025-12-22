#!/usr/bin/env python3
"""macOS Sparkle framework setup module"""

import tarfile
import urllib.request
from ...common.module import CommandModule, ValidationError
from ...common.context import Context
from ...common.utils import log_info, log_success, IS_MACOS, safe_rmtree


class MacSparkleSetupModule(CommandModule):
    """Download and setup Sparkle framework (macOS only)"""

    produces = []
    requires = []
    description = "Download and setup Sparkle framework (macOS only)"

    def validate(self, ctx: Context) -> None:
        if not IS_MACOS():
            raise ValidationError("Sparkle setup requires macOS")

    def execute(self, ctx: Context) -> None:
        log_info("\n✨ Setting up Sparkle framework...")

        sparkle_dir = ctx.get_sparkle_dir()

        if sparkle_dir.exists():
            safe_rmtree(sparkle_dir)

        sparkle_dir.mkdir(parents=True)

        sparkle_url = ctx.get_sparkle_url()
        sparkle_archive = sparkle_dir / "sparkle.tar.xz"

        log_info(f"Downloading Sparkle from {sparkle_url}...")
        urllib.request.urlretrieve(sparkle_url, sparkle_archive)

        log_info("Extracting Sparkle...")
        with tarfile.open(sparkle_archive, "r:xz") as tar:
            tar.extractall(sparkle_dir)

        sparkle_archive.unlink()

        log_success("Sparkle setup complete")
