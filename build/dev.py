#!/usr/bin/env python3
"""
Developer CLI for managing per-file Chromium patches.

Implements:
- split: split a monolithic patch into per-file patches stored under repo ./chromium_src/
- apply: apply all per-file patches from ./chromium_src/ to a Chromium checkout
- import: import changes from a Chromium commit into per-file patches under ./chromium_src/
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import click

from utils import (
    log_info,
    log_warning,
    log_error,
    log_success,
)
from modules.dev_patches import (
    split_monolithic_patch,
    apply_per_file_patches,
    import_commit_as_per_file_patches,
)


def _repo_root() -> Path:
    return Path(__file__).parent.parent


def _default_patch_root() -> Path:
    # Store per-file patches under repo-local chromium_src/ mirroring Chromium paths
    return _repo_root() / "chromium_src"


@click.group()
def cli():
    """Nxtscape Dev CLI"""
    pass


@cli.command("split")
@click.option(
    "--patch",
    "patch_file",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Monolithic patch file to split",
)
@click.option(
    "--into",
    "into_dir",
    type=click.Path(path_type=Path),
    default=_default_patch_root,
    show_default=True,
    help="Directory to write per-file patches into (mirrors Chromium paths)",
)
def cmd_split(patch_file: Path, into_dir: Path):
    """Split a monolithic patch into per-file patches under chromium_src/."""
    try:
        mapping = split_monolithic_patch(patch_file, into_dir)
        log_info(f"✅ Split complete. Files: {len(mapping)}")
    except Exception as e:
        log_error(f"Split failed: {e}")
        raise SystemExit(1)


@cli.command("apply")
@click.option(
    "--chromium-src",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to Chromium checkout (repo root)",
)
@click.option(
    "--patch-root",
    type=click.Path(path_type=Path),
    default=_default_patch_root,
    show_default=True,
    help="Root directory containing per-file patches (mirrors Chromium paths)",
)
def cmd_apply(chromium_src: Path, patch_root: Path):
    """Apply all per-file patches from chromium_src/ to a Chromium checkout."""
    try:
        applied, failures = apply_per_file_patches(chromium_src, patch_root)
        if failures:
            raise SystemExit(1)
        log_success(f"Applied {applied} patch(es)")
    except SystemExit:
        raise
    except Exception as e:
        log_error(f"Apply failed: {e}")
        raise SystemExit(1)


@cli.command("import")
@click.option(
    "--chromium-src",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to Chromium checkout (repo root)",
)
@click.option(
    "--commit",
    type=str,
    default=None,
    help="Commit hash/ref to import (defaults to HEAD)",
)
@click.option(
    "--patch-root",
    type=click.Path(path_type=Path),
    default=_default_patch_root,
    show_default=True,
    help="Root directory to write per-file patches (mirrors Chromium paths)",
)
def cmd_import(chromium_src: Path, commit: Optional[str], patch_root: Path):
    """Import changes from a Chromium commit into per-file patches under chromium_src/."""
    try:
        mapping = import_commit_as_per_file_patches(chromium_src, commit, patch_root)
        log_success(f"Imported {len(mapping)} patch(es)")
    except Exception as e:
        log_error(f"Import failed: {e}")
        raise SystemExit(1)


def main():
    cli()


if __name__ == "__main__":
    main()

