#!/usr/bin/env python3
"""WinSparkle signing module for Windows auto-update"""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

from ...common.module import CommandModule, ValidationError
from ...common.context import Context
from ...common.utils import (
    log_info,
    log_error,
    log_success,
    log_warning,
    IS_WINDOWS,
)


class WinSparkleSignModule(CommandModule):
    """Sign Windows installers with WinSparkle for auto-update"""

    produces = ["winsparkle_signatures"]
    requires = []
    description = "Sign Windows installer files with WinSparkle Ed25519 key for auto-update"

    def validate(self, ctx: Context) -> None:
        if not IS_WINDOWS():
            raise ValidationError("WinSparkle signing is Windows only")

        winsparkle_tool = ctx.get_winsparkle_tool_path()
        if not winsparkle_tool.exists():
            raise ValidationError(f"winsparkle-tool.exe not found: {winsparkle_tool}")

        if not ctx.env.has_winsparkle_key():
            raise ValidationError(
                "WINSPARKLE_PRIVATE_KEY (or SPARKLE_PRIVATE_KEY) environment variable not set"
            )

    def execute(self, ctx: Context) -> None:
        log_info("\n🔐 Signing installers with WinSparkle...")

        dist_dir = ctx.get_dist_dir()
        if not dist_dir.exists():
            log_warning(f"Dist directory not found: {dist_dir}")
            return

        # Find .exe installer files
        exe_files = list(dist_dir.glob("*_installer.exe"))
        if not exe_files:
            log_warning("No installer .exe files found to sign")
            return

        signatures = sign_installers_with_winsparkle(ctx, exe_files)

        for filename, (sig, length) in signatures.items():
            ctx.artifact_registry.add(f"winsparkle_sig_{filename}", Path(filename))
            log_info(f"  {filename}: sig={sig[:20]}... length={length}")

        ctx.artifacts["winsparkle_signatures"] = signatures

        log_success(f"Signed {len(signatures)} installer(s) with WinSparkle")


def sign_installers_with_winsparkle(
    ctx: Context,
    exe_files: list,
) -> Dict[str, Tuple[str, int]]:
    """Sign installer files with WinSparkle and return signatures

    Args:
        ctx: Build context
        exe_files: List of .exe file paths to sign

    Returns:
        Dict mapping filename to (signature, length) tuple
    """
    env = ctx.env
    winsparkle_tool = ctx.get_winsparkle_tool_path()

    if not winsparkle_tool.exists():
        log_error(f"winsparkle-tool.exe not found: {winsparkle_tool}")
        return {}

    if not env.has_winsparkle_key():
        log_error("WINSPARKLE_PRIVATE_KEY not set")
        return {}

    signatures = {}

    key_file = None
    try:
        key_data = env.winsparkle_private_key

        key_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".key", delete=False
        )
        key_file.write(key_data)
        key_file.close()

        for exe_path in exe_files:
            sig, length = _sign_single_installer(winsparkle_tool, key_file.name, exe_path)
            if sig:
                signatures[exe_path.name] = (sig, length)

    finally:
        if key_file and os.path.exists(key_file.name):
            os.unlink(key_file.name)

    return signatures


def _sign_single_installer(
    winsparkle_tool: Path,
    key_file: str,
    exe_path: Path,
) -> Tuple[Optional[str], int]:
    """Sign a single installer and parse the output

    Args:
        winsparkle_tool: Path to winsparkle-tool.exe
        key_file: Path to temporary key file
        exe_path: Path to .exe installer file

    Returns:
        (signature, length) tuple, or (None, 0) on failure
    """
    log_info(f"🔐 Signing {exe_path.name}...")

    try:
        result = subprocess.run(
            [str(winsparkle_tool), "sign", "--file", key_file, str(exe_path)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            log_error(f"winsparkle-tool failed: {result.stderr}")
            return None, 0

        output = result.stdout.strip()
        sig, length = parse_winsparkle_output(output)

        if sig:
            log_success(f"Signed {exe_path.name}")
            return sig, length
        else:
            log_error(f"Failed to parse winsparkle-tool output: {output}")
            return None, 0

    except Exception as e:
        log_error(f"Error signing {exe_path.name}: {e}")
        return None, 0


def parse_winsparkle_output(output: str) -> Tuple[Optional[str], int]:
    """Parse winsparkle-tool sign output to extract signature and length

    Example output:
        sparkle:edSignature="abc123..." length="1736832"

    Args:
        output: Raw output from winsparkle-tool

    Returns:
        (signature, length) tuple, or (None, 0) if parsing fails
    """
    sig_match = re.search(r'sparkle:edSignature="([^"]+)"', output)
    len_match = re.search(r'length="(\d+)"', output)

    if sig_match and len_match:
        return sig_match.group(1), int(len_match.group(1))

    return None, 0


def get_winsparkle_signatures(ctx: Context) -> Dict[str, Tuple[str, int]]:
    """Get stored WinSparkle signatures from context

    Args:
        ctx: Build context

    Returns:
        Dict mapping filename to (signature, length) tuple
    """
    return ctx.artifacts.get("winsparkle_signatures", {})
