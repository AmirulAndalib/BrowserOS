#!/usr/bin/env python3
"""
Windows signing module for BrowserOS
Handles code signing using SSL.com CodeSignTool
"""

import os
from pathlib import Path
from typing import Optional, List
from ...common.context import BuildContext
from ...utils import (
    run_command,
    log_info,
    log_error,
    log_success,
    log_warning,
    join_paths,
)

# BrowserOS Server binaries packaged alongside Chrome that must be signed prior to
# building the installer. Extend this list when new server-side executables are added.
BROWSEROS_SERVER_BINARIES: List[str] = [
    "browseros_server.exe",
    "codex.exe",
]


def get_browseros_server_binary_paths(build_output_dir: Path) -> List[Path]:
    """Return absolute paths to BrowserOS Server binaries for signing."""
    server_dir = build_output_dir / "BrowserOSServer" / "default" / "resources" / "bin"
    return [server_dir / binary for binary in BROWSEROS_SERVER_BINARIES]


def build_mini_installer(ctx: BuildContext) -> bool:
    """Build the mini_installer.exe"""
    from ..compile import build_target
    log_info("Building mini_installer target...")
    return build_target(ctx, "mini_installer")


def sign(ctx: BuildContext, certificate_name: Optional[str] = None) -> bool:
    """Wrapper for compatibility - calls sign_binaries"""
    return sign_binaries(ctx, certificate_name)


def sign_binaries(ctx: BuildContext, certificate_name: Optional[str] = None) -> bool:
    """Sign Windows binaries using SSL.com CodeSignTool"""
    log_info("\n🔏 Signing Windows binaries...")

    # Get paths to sign
    build_output_dir = join_paths(ctx.chromium_src, ctx.out_dir)

    # STEP 1: Sign chrome.exe and BrowserOS Server binaries BEFORE building mini_installer
    log_info("\nStep 1/3: Signing executables before packaging...")
    binaries_to_sign_first = [build_output_dir / "chrome.exe"]
    binaries_to_sign_first.extend(get_browseros_server_binary_paths(build_output_dir))

    # Check which binaries exist
    existing_binaries = []
    for binary in binaries_to_sign_first:
        if binary.exists():
            existing_binaries.append(binary)
            log_info(f"Found binary to sign: {binary.name}")
        else:
            log_warning(f"Binary not found: {binary}")

    if not existing_binaries:
        log_error("No binaries found to sign")
        return False

    # Sign the executables
    if not sign_with_codesigntool(existing_binaries):
        log_error("Failed to sign executables")
        return False

    # STEP 2: Build mini_installer to package the signed binaries
    log_info("\nStep 2/3: Building mini_installer with signed binaries...")
    if not build_mini_installer(ctx):
        log_error("Failed to build mini_installer")
        return False

    # STEP 3: Sign the mini_installer.exe
    log_info("\nStep 3/3: Signing mini_installer.exe...")
    mini_installer_path = build_output_dir / "mini_installer.exe"
    if not mini_installer_path.exists():
        log_error(f"mini_installer.exe not found at: {mini_installer_path}")
        return False

    if not sign_with_codesigntool([mini_installer_path]):
        log_error("Failed to sign mini_installer.exe")
        return False

    log_success("✅ All binaries signed successfully!")
    return True


def sign_with_codesigntool(binaries: List[Path]) -> bool:
    """Sign binaries using SSL.com CodeSignTool"""
    log_info("Using SSL.com CodeSignTool for signing...")

    # Get CodeSignTool directory from environment
    codesigntool_dir = os.environ.get("CODE_SIGN_TOOL_PATH")
    if not codesigntool_dir:
        log_error("CODE_SIGN_TOOL_PATH not set in .env file")
        log_error("Set CODE_SIGN_TOOL_PATH=C:/src/CodeSignTool-v1.3.2-windows")
        return False

    # Construct path to CodeSignTool.bat
    codesigntool_path = Path(codesigntool_dir) / "CodeSignTool.bat"
    if not codesigntool_path.exists():
        log_error(f"CodeSignTool.bat not found at: {codesigntool_path}")
        log_error(f"Make sure CODE_SIGN_TOOL_PATH points to the CodeSignTool directory")
        return False

    # Check for required environment variables
    username = os.environ.get("ESIGNER_USERNAME")
    password = os.environ.get("ESIGNER_PASSWORD")
    totp_secret = os.environ.get("ESIGNER_TOTP_SECRET")
    credential_id = os.environ.get("ESIGNER_CREDENTIAL_ID")

    if not all([username, password, totp_secret]):
        log_error("Missing required eSigner environment variables in .env:")
        log_error("  ESIGNER_USERNAME=your-email")
        log_error("  ESIGNER_PASSWORD=your-password")
        log_error("  ESIGNER_TOTP_SECRET=your-totp-secret")
        if not credential_id:
            log_warning("  ESIGNER_CREDENTIAL_ID is recommended but optional")
        return False

    all_success = True
    for binary in binaries:
        try:
            log_info(f"Signing {binary.name}...")

            # Build command
            # Create a temp output directory to avoid source/dest conflict
            temp_output_dir = binary.parent / "signed_temp"
            temp_output_dir.mkdir(exist_ok=True)

            cmd = [
                str(codesigntool_path),
                "sign",
                "-username",
                username,
                "-password",
                f'"{password}"',  # Always quote the password for shell
            ]

            # Add credential_id BEFORE totp_secret (order matters!)
            if credential_id:
                cmd.extend(["-credential_id", credential_id])

            cmd.extend(
                [
                    "-totp_secret",
                    totp_secret,
                    "-input_file_path",
                    str(binary),
                    "-output_dir_path",
                    str(temp_output_dir),
                    "-override",  # Add this back
                ]
            )

            # Note: Timestamp server is configured on SSL.com side automatically

            # CodeSignTool needs to be run as a shell command for proper quote handling
            cmd_str = " ".join(cmd)
            log_info(f"Running: {cmd_str}")

            import subprocess

            result = subprocess.run(
                cmd_str,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(codesigntool_path.parent),
            )

            # Print output for debugging
            if result.stdout:
                for line in result.stdout.split("\n"):
                    if line.strip():
                        log_info(line.strip())
            if result.stderr:
                for line in result.stderr.split("\n"):
                    if line.strip() and "WARNING" not in line:
                        log_error(line.strip())

            # Check if signing actually succeeded by looking for error messages
            # CodeSignTool returns 0 even on auth errors, so we need to check output
            if result.stdout and "Error:" in result.stdout:
                log_error(
                    f"✗ Failed to sign {binary.name} - Authentication or signing error"
                )
                all_success = False
                continue

            # Move the signed file back to original location
            signed_file = temp_output_dir / binary.name
            if signed_file.exists():
                import shutil

                shutil.move(str(signed_file), str(binary))
                log_info(f"Moved signed {binary.name} to original location")

            # Clean up temp directory
            try:
                temp_output_dir.rmdir()
            except:
                pass  # Directory might not be empty

            # Verify the file is actually signed (Windows only)
            verify_cmd = [
                "powershell",
                "-Command",
                f"(Get-AuthenticodeSignature '{binary}').Status",
            ]
            try:
                import subprocess

                verify_result = subprocess.run(
                    verify_cmd, capture_output=True, text=True
                )
                if "Valid" in verify_result.stdout:
                    log_success(f"✓ {binary.name} signed and verified successfully")
                else:
                    log_error(
                        f"✗ {binary.name} signing verification failed - Status: {verify_result.stdout.strip()}"
                    )
                    all_success = False
            except:
                log_warning(f"Could not verify signature for {binary.name}")

        except Exception as e:
            log_error(f"Failed to sign {binary.name}: {e}")
            all_success = False

    return all_success


def sign_universal(contexts: List[BuildContext]) -> bool:
    """Windows doesn't support universal binaries"""
    log_warning("Universal signing is not supported on Windows")
    return True


def check_signing_environment() -> bool:
    """Check if Windows signing environment is properly configured"""
    # Check for CodeSignTool
    codesigntool_dir = os.environ.get("CODE_SIGN_TOOL_PATH")
    if not codesigntool_dir:
        log_error("CODE_SIGN_TOOL_PATH not set")
        return False

    # Check for required environment variables
    required_vars = ["ESIGNER_USERNAME", "ESIGNER_PASSWORD", "ESIGNER_TOTP_SECRET"]
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)

    if missing:
        log_error(f"Missing environment variables: {', '.join(missing)}")
        return False

    return True