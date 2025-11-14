"""
Extract module for dev CLI - Extract patches from git commits
"""

from .extract import extract_commit, extract_range

__all__ = ['extract_commit', 'extract_range']