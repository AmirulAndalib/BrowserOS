"""
Extract module for dev CLI - Extract patches from git commits
"""

from .extract import (
    extract_commit,
    extract_range,
    ExtractCommitModule,
    ExtractRangeModule,
)

__all__ = [
    # Legacy functions (Click commands)
    'extract_commit',
    'extract_range',
    # CommandModule classes
    'ExtractCommitModule',
    'ExtractRangeModule',
]