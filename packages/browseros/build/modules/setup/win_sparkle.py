#!/usr/bin/env python3
"""Windows WinSparkle setup module"""

import shutil
import urllib.request
import zipfile
from pathlib import Path
from ...common.module import CommandModule, ValidationError
from ...common.context import Context
from ...common.utils import log_info, log_success, IS_WINDOWS, safe_rmtree


class WinSparkleSetupModule(CommandModule):
    """Download and setup WinSparkle (Windows only)"""

    produces = []
    requires = []
    description = "Download and setup WinSparkle (Windows only)"

    def validate(self, ctx: Context) -> None:
        if not IS_WINDOWS():
            raise ValidationError("WinSparkle setup requires Windows")

    def execute(self, ctx: Context) -> None:
        log_info("\n✨ Setting up WinSparkle...")

        winsparkle_dir = ctx.get_winsparkle_dir()

        if winsparkle_dir.exists():
            safe_rmtree(winsparkle_dir)

        winsparkle_dir.mkdir(parents=True)

        winsparkle_url = ctx.get_winsparkle_url()
        winsparkle_archive = winsparkle_dir / "winsparkle.zip"

        log_info(f"Downloading WinSparkle from {winsparkle_url}...")
        urllib.request.urlretrieve(winsparkle_url, winsparkle_archive)

        log_info("Extracting WinSparkle...")
        with zipfile.ZipFile(winsparkle_archive, "r") as zf:
            zf.extractall(winsparkle_dir)

        winsparkle_archive.unlink()

        # Flatten: move contents of WinSparkle-X.Y.Z/ up to winsparkle/
        self._flatten_extracted_dir(winsparkle_dir, ctx.WINSPARKLE_VERSION)

        log_success("WinSparkle setup complete")

    def _flatten_extracted_dir(self, winsparkle_dir: Path, version: str) -> None:
        """Move contents of versioned subdirectory up to parent"""
        versioned_dir = winsparkle_dir / f"WinSparkle-{version}"

        if not versioned_dir.exists():
            log_info(f"No versioned subdirectory found at {versioned_dir}, skipping flatten")
            return

        log_info(f"Flattening {versioned_dir.name}/ directory...")

        for item in versioned_dir.iterdir():
            dest = winsparkle_dir / item.name
            if dest.exists():
                if dest.is_dir():
                    safe_rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(item), str(dest))

        versioned_dir.rmdir()
