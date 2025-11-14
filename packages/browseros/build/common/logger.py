#!/usr/bin/env python3
"""
Logging utilities for the build system
Provides consistent logging across all build modules with file output
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Global log file handle
_log_file = None


def _ensure_log_file():
    """Ensure log file is created with timestamp"""
    global _log_file
    if _log_file is None:
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file_path = log_dir / f"build_{timestamp}.log"
        # Open with UTF-8 encoding to handle any characters
        _log_file = open(log_file_path, "w", encoding="utf-8")
        _log_file.write(
            f"Nxtscape Build Log - Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        _log_file.write("=" * 80 + "\n\n")
    return _log_file


def _log_to_file(message: str):
    """Write message to log file with timestamp"""
    log_file = _ensure_log_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file.write(f"[{timestamp}] {message}\n")
    log_file.flush()


def _sanitize_for_windows(message: str) -> str:
    """Remove non-ASCII characters on Windows to avoid encoding issues"""
    if sys.platform == "win32":
        # Remove all non-ASCII characters
        return "".join(char for char in message if ord(char) < 128)
    return message


def log_info(message: str):
    """Print info message"""
    print(_sanitize_for_windows(message))
    _log_to_file(f"INFO: {message}")


def log_warning(message: str):
    """Print warning message"""
    if sys.platform == "win32":
        print(f"[WARN] {_sanitize_for_windows(message)}")
    else:
        print(f"⚠️ {message}")
    _log_to_file(f"WARNING: {message}")


def log_error(message: str):
    """Print error message"""
    if sys.platform == "win32":
        print(f"[ERROR] {_sanitize_for_windows(message)}")
    else:
        print(f"❌ {message}")
    _log_to_file(f"ERROR: {message}")


def log_success(message: str):
    """Print success message"""
    if sys.platform == "win32":
        print(f"[SUCCESS] {_sanitize_for_windows(message)}")
    else:
        print(f"✅ {message}")
    _log_to_file(f"SUCCESS: {message}")


def log_debug(message: str, enabled: bool = False):
    """Print debug message if enabled"""
    if enabled:
        if sys.platform == "win32":
            print(f"[DEBUG] {_sanitize_for_windows(message)}")
        else:
            print(f"🔍 {message}")
        _log_to_file(f"DEBUG: {message}")


def close_log_file():
    """Close the log file if it's open"""
    global _log_file
    if _log_file:
        _log_file.close()
        _log_file = None


# Export all logging functions
__all__ = [
    'log_info',
    'log_warning',
    'log_error',
    'log_success',
    'log_debug',
    'close_log_file',
    '_log_to_file',  # Internal use by utils.run_command
]