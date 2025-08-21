#!/usr/bin/env python3
"""
Developer patch utilities: split monolithic patches, apply per-file patches, and import
changes from a Chromium checkout into per-file patches stored under the repository's
`chromium_src/` directory mirroring Chromium paths.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from utils import log_info, log_warning, log_error, log_success, run_command


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _detect_patch_target_path(header_line: str, block_lines: List[str]) -> Optional[str]:
    """Given a 'diff --git a/.. b/..' header line and subsequent block lines,
    determine the target chromium-relative path for storing the patch.

    Prefers the destination (b/...) path unless it is /dev/null (deletions), falling
    back to the source (a/...) path.
    """
    try:
        parts = header_line.strip().split()
        # Expected: ["diff", "--git", "a/<path>", "b/<path>"]
        a_path = parts[2]
        b_path = parts[3]
    except Exception:
        return None

    def strip_prefix(p: str) -> str:
        return p[2:] if p.startswith("a/") or p.startswith("b/") else p

    a_rel = strip_prefix(a_path)
    b_rel = strip_prefix(b_path)

    # Prefer destination path unless it's /dev/null
    if b_rel == "/dev/null":
        return a_rel
    return b_rel


def split_monolithic_patch(patch_file: Path, into_dir: Path) -> Dict[str, Path]:
    """Split a monolithic patch into per-file patches under `into_dir`.

    Returns a mapping of chromium-relative path -> written patch file path.
    Appends to an existing per-file patch if multiple diffs affect the same file.
    """
    if not patch_file.exists():
        raise FileNotFoundError(f"Patch not found: {patch_file}")

    into_dir.mkdir(parents=True, exist_ok=True)

    log_info(f"🔪 Splitting patch: {patch_file}")
    mapping: Dict[str, Path] = {}

    with open(patch_file, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    current_block: List[str] = []
    current_header: Optional[str] = None

    def flush_block():
        nonlocal current_block, current_header, mapping
        if not current_block or not current_header:
            current_block = []
            current_header = None
            return
        rel_path = _detect_patch_target_path(current_header, current_block)
        if not rel_path:
            log_warning("Skipping a block with undetectable path header")
            current_block = []
            current_header = None
            return
        out_path = into_dir / f"{rel_path}.patch"
        _ensure_dir(out_path)
        write_mode = "a" if out_path.exists() else "w"
        with open(out_path, write_mode, encoding="utf-8") as out:
            # Ensure block ends with a newline
            if current_block and not current_block[-1].endswith("\n"):
                current_block[-1] = current_block[-1] + "\n"
            out.writelines(current_block)
        mapping[rel_path] = out_path
        current_block = []
        current_header = None

    for line in lines:
        if line.startswith("diff --git "):
            # New file block starts; flush previous
            flush_block()
            current_header = line
            current_block = [line]
        else:
            if current_block is not None:
                current_block.append(line)

    # Flush last block
    flush_block()

    log_success(f"✂️  Created/updated {len(mapping)} per-file patch(es) in {into_dir}")
    return mapping


def apply_per_file_patches(chromium_src: Path, patch_root: Path) -> Tuple[int, List[Tuple[Path, int]]]:
    """Apply all per-file patches found under `patch_root` into the `chromium_src` checkout.

    Returns a tuple: (applied_count, failures) where failures is a list of (patch_path, exit_code).
    """
    if not chromium_src.exists():
        raise FileNotFoundError(f"Chromium source not found: {chromium_src}")
    if not patch_root.exists():
        log_warning(f"Patch root does not exist: {patch_root}")
        return 0, []

    patches = sorted(patch_root.rglob("*.patch"))
    if not patches:
        log_warning(f"No patches found under: {patch_root}")
        return 0, []

    log_info(f"📦 Applying {len(patches)} patch(es) to {chromium_src}")
    applied = 0
    failures: List[Tuple[Path, int]] = []

    for p in patches:
        rel_display = p.relative_to(patch_root)
        log_info(f"➡️  Applying {rel_display}")
        try:
            # Use -p1 to strip the a/ and b/ prefixes
            run_command(
                [
                    "git",
                    "apply",
                    "-p1",
                    "--ignore-whitespace",
                    "--whitespace=nowarn",
                    "--3way",
                    str(p),
                ],
                cwd=chromium_src,
                check=True,
            )
            applied += 1
        except Exception as e:
            log_error(f"Failed to apply {rel_display}: {e}")
            failures.append((p, 1))

    if failures:
        log_warning(f"Some patches failed: {len(failures)} of {len(patches)}")
    else:
        log_success("All patches applied successfully")
    return applied, failures


def import_commit_as_per_file_patches(
    chromium_src: Path, commit: Optional[str], patch_root: Path
) -> Dict[str, Path]:
    """Import the changes from a specific commit (or HEAD) in the Chromium checkout
    and write per-file patches under `patch_root`.

    Returns a mapping of chromium-relative path -> written patch file path.
    """
    if not chromium_src.exists():
        raise FileNotFoundError(f"Chromium source not found: {chromium_src}")

    # Resolve commit
    commit_ref = commit or "HEAD"

    # Verify this is a git repo
    try:
        run_command(["git", "rev-parse", "--is-inside-work-tree"], cwd=chromium_src)
    except Exception:
        raise RuntimeError(f"{chromium_src} is not a git repository")

    # Get changed files in the commit (first parent for merges)
    files_result = run_command(
        [
            "git",
            "show",
            "--pretty=format:",
            "--name-only",
            commit_ref,
        ],
        cwd=chromium_src,
        check=True,
    )
    files = [
        line.strip()
        for line in files_result.stdout.splitlines()
        if line.strip() and not line.startswith("\0")
    ]

    if not files:
        log_warning(f"No changed files found in commit {commit_ref}")
        return {}

    patch_root.mkdir(parents=True, exist_ok=True)
    log_info(f"🛬 Importing {len(files)} file(s) from {commit_ref} into {patch_root}")

    mapping: Dict[str, Path] = {}

    for rel in files:
        # Generate unified diff for this file only
        diff_res = run_command(
            ["git", "show", commit_ref, "--pretty=format:", "--unified=3", "--", rel],
            cwd=chromium_src,
            check=True,
        )
        diff_text = diff_res.stdout.strip()
        if not diff_text:
            log_warning(f"No diff produced for {rel}; skipping")
            continue

        # Heuristic: ensure the diff starts at a diff header; git show may produce multiple
        # diffs if there are renames or mode changes—we keep as-is.
        out_path = patch_root / f"{rel}.patch"
        _ensure_dir(out_path)
        with open(out_path, "w", encoding="utf-8") as out:
            out.write(diff_text)
            if not diff_text.endswith("\n"):
                out.write("\n")
        mapping[rel] = out_path
        log_info(f"📝 Wrote patch: {out_path}")

    log_success(f"Imported {len(mapping)} per-file patch(es) from {commit_ref}")
    return mapping

