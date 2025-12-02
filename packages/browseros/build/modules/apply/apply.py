"""
Apply module - Apply patches to Chromium source

Simple and straightforward patch application with minimal error handling.
"""

import click
import yaml
from pathlib import Path
from typing import List, Tuple, Optional
from ...common.context import Context
from ...common.module import CommandModule, ValidationError
from .utils import run_git_command, file_exists_in_commit, reset_file_to_commit
from ...common.utils import log_info, log_error, log_success, log_warning


# Core Functions - Can be called programmatically or from CLI
def find_patch_files(patches_dir: Path) -> List[Path]:
    """Find all valid patch files in a directory.

    Args:
        patches_dir: Directory to search for patches

    Returns:
        List of patch file paths, sorted
    """
    if not patches_dir.exists():
        return []

    return sorted(
        [
            p
            for p in patches_dir.rglob("*")
            if p.is_file()
            and not p.name.endswith(".deleted")
            and not p.name.endswith(".binary")
            and not p.name.endswith(".rename")
            and not p.name.startswith(".")
        ]
    )


def apply_single_patch(
    patch_path: Path,
    chromium_src: Path,
    dry_run: bool = False,
    relative_to: Optional[Path] = None,
    reset_to: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Apply a single patch file.

    Args:
        patch_path: Path to the patch file
        chromium_src: Chromium source directory
        dry_run: If True, only check if patch would apply
        relative_to: Base path for displaying relative paths (optional)
        reset_to: Commit to reset file to before applying (optional)

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    display_path = patch_path.relative_to(relative_to) if relative_to else patch_path

    # Reset file to base commit if requested
    if reset_to and not dry_run:
        file_path = str(display_path)
        if file_exists_in_commit(file_path, reset_to, chromium_src):
            log_info(f"  Resetting to {reset_to[:8]}: {file_path}")
            reset_file_to_commit(file_path, reset_to, chromium_src)

    if dry_run:
        # Just check if patch would apply
        result = run_git_command(
            ["git", "apply", "--check", "-p1", str(patch_path)], cwd=chromium_src
        )
        if result.returncode == 0:
            log_success(f"  ✓ Would apply: {display_path}")
            return True, None
        else:
            log_error(f"  ✗ Would fail: {display_path}")
            return False, result.stderr
    else:
        # Try standard apply first
        result = run_git_command(
            [
                "git",
                "apply",
                "--ignore-whitespace",
                "--whitespace=nowarn",
                "-p1",
                str(patch_path),
            ],
            cwd=chromium_src,
        )

        if result.returncode != 0:
            # Try with 3-way merge
            result = run_git_command(
                [
                    "git",
                    "apply",
                    "--ignore-whitespace",
                    "--whitespace=nowarn",
                    "-p1",
                    "--3way",
                    str(patch_path),
                ],
                cwd=chromium_src,
            )

        if result.returncode == 0:
            log_success(f"  ✓ Applied: {display_path}")
            return True, None
        else:
            log_error(f"  ✗ Failed: {display_path}")
            if result.stderr:
                log_error(f"    {result.stderr}")
            return False, result.stderr


def create_patch_commit(
    patch_identifier: str, chromium_src: Path, feature_name: Optional[str] = None
) -> bool:
    """Create a git commit after applying a patch.

    Args:
        patch_identifier: Patch name or path for commit message
        chromium_src: Chromium source directory
        feature_name: Optional feature name for commit message

    Returns:
        True if commit was created successfully
    """
    # Stage all changes
    result = run_git_command(["git", "add", "-A"], cwd=chromium_src)
    if result.returncode != 0:
        log_warning("Failed to stage changes for commit")
        return False

    # Create commit message
    if feature_name:
        commit_msg = f"Apply {feature_name}: {Path(patch_identifier).name}"
    else:
        commit_msg = f"Apply patch: {patch_identifier}"

    result = run_git_command(["git", "commit", "-m", commit_msg], cwd=chromium_src)

    if result.returncode == 0:
        log_success(f"📝 Created commit: {commit_msg}")
        return True
    else:
        log_warning("Failed to create commit")
        return False


def process_patch_list(
    patch_list: List[Tuple[Path, str]],
    chromium_src: Path,
    patches_dir: Path,
    commit_each: bool = False,
    dry_run: bool = False,
    interactive: bool = False,
    feature_name: Optional[str] = None,
    reset_to: Optional[str] = None,
) -> Tuple[int, List[str]]:
    """Process a list of patches.

    Args:
        patch_list: List of (patch_path, display_name) tuples
        chromium_src: Chromium source directory
        patches_dir: Base directory for relative path display
        commit_each: Create a commit after each patch
        dry_run: Only check if patches would apply
        interactive: Ask for confirmation before each patch
        feature_name: Optional feature name for commit messages
        reset_to: Commit to reset files to before applying (optional)

    Returns:
        Tuple of (applied_count, failed_list)
    """
    applied = 0
    failed = []
    skipped = 0

    total = len(patch_list)

    for i, (patch_path, display_name) in enumerate(patch_list, 1):
        if interactive and not dry_run:
            # Show patch info and ask for confirmation
            log_info(f"\n{'='*60}")
            log_info(f"Patch {i}/{total}: {display_name}")
            log_info(f"{'='*60}")

            while True:
                choice = input(
                    "\nOptions:\n  1) Apply this patch\n  2) Skip this patch\n  3) Stop patching\nChoice (1-3): "
                ).strip()

                if choice == "1":
                    break  # Apply the patch
                elif choice == "2":
                    log_warning(f"⏭️  Skipping patch: {display_name}")
                    skipped += 1
                    continue  # Skip to next patch
                elif choice == "3":
                    log_info(
                        f"Stopped. Applied: {applied}, Failed: {len(failed)}, Skipped: {skipped}"
                    )
                    return applied, failed
                else:
                    log_error("Invalid choice. Please enter 1, 2, or 3.")

        if not patch_path.exists():
            log_warning(f"  Patch not found: {display_name}")
            failed.append(display_name)
            continue

        # Apply the patch
        success, error = apply_single_patch(
            patch_path, chromium_src, dry_run, patches_dir, reset_to
        )

        if success:
            applied += 1
            if commit_each and not dry_run:
                create_patch_commit(display_name, chromium_src, feature_name)
        else:
            failed.append(display_name)

            if interactive and not dry_run:
                # Interactive error handling
                log_error("\n" + "=" * 60)
                log_error(f"Patch {display_name} failed to apply")

                while True:
                    choice = input(
                        "\nOptions:\n  1) Continue with next patch\n  2) Abort\n  3) Fix manually and continue\nChoice (1-3): "
                    ).strip()

                    if choice == "1":
                        break  # Continue to next patch
                    elif choice == "2":
                        raise RuntimeError(f"Aborted at patch: {display_name}")
                    elif choice == "3":
                        input("Fix the issue manually, then press Enter to continue...")
                        applied += 1  # Count as applied since user fixed it
                        failed.pop()  # Remove from failed list
                        break
                    else:
                        log_error("Invalid choice.")

    return applied, failed


# ============================================================================
# Main Functions - Entry points for programmatic use
# ============================================================================


def apply_all_patches(
    build_ctx: Context,
    commit_each: bool = False,
    dry_run: bool = False,
    interactive: bool = False,
    reset_to: Optional[str] = None,
) -> Tuple[int, List[str]]:
    """Apply all patches from patches directory.

    Args:
        build_ctx: Build context
        commit_each: Create a commit after each patch
        dry_run: Only check if patches would apply
        interactive: Ask for confirmation before each patch
        reset_to: Commit to reset files to before applying (optional)

    Returns:
        Tuple of (applied_count, failed_list)
    """
    patches_dir = build_ctx.get_dev_patches_dir()

    if not patches_dir.exists():
        log_warning(f"Patches directory does not exist: {patches_dir}")
        return 0, []

    # Find all patch files
    patch_files = find_patch_files(patches_dir)

    if not patch_files:
        log_warning("No patch files found")
        return 0, []

    log_info(f"Found {len(patch_files)} patches")

    if dry_run:
        log_info("DRY RUN - No changes will be made")

    # Create patch list with display names
    patch_list = [(p, p.relative_to(patches_dir)) for p in patch_files]

    # Process patches
    applied, failed = process_patch_list(
        patch_list,
        build_ctx.chromium_src,
        patches_dir,
        commit_each,
        dry_run,
        interactive,
        reset_to=reset_to,
    )

    # Summary
    log_info(f"\nSummary: {applied} applied, {len(failed)} failed")

    if failed:
        log_error("Failed patches:")
        for p in failed:
            log_error(f"  - {p}")

    return applied, failed


def apply_feature_patches(
    build_ctx: Context,
    feature_name: str,
    commit_each: bool = False,
    dry_run: bool = False,
    reset_to: Optional[str] = None,
) -> Tuple[int, List[str]]:
    """Apply patches for a specific feature.

    Args:
        build_ctx: Build context
        feature_name: Name of the feature
        commit_each: Create a commit after each patch
        dry_run: Only check if patches would apply
        reset_to: Commit to reset files to before applying (optional)

    Returns:
        Tuple of (applied_count, failed_list)
    """
    # Load features.yaml
    features_path = build_ctx.get_features_yaml_path()
    if not features_path.exists():
        log_error("No features.yaml found")
        return 0, []

    with open(features_path) as f:
        data = yaml.safe_load(f)

    features = data.get("features", {})

    if feature_name not in features:
        log_error(f"Feature '{feature_name}' not found")
        log_info("Available features:")
        for name in features:
            log_info(f"  - {name}")
        return 0, []

    file_list = features[feature_name].get("files", [])

    if not file_list:
        log_warning(f"Feature '{feature_name}' has no files")
        return 0, []

    log_info(f"Applying patches for feature '{feature_name}' ({len(file_list)} files)")

    if dry_run:
        log_info("DRY RUN - No changes will be made")

    # Create patch list
    patches_dir = build_ctx.get_dev_patches_dir()
    patch_list = []
    for file_path in file_list:
        patch_path = build_ctx.get_patch_path_for_file(file_path)
        patch_list.append((patch_path, file_path))

    # Process patches
    applied, failed = process_patch_list(
        patch_list,
        build_ctx.chromium_src,
        patches_dir,
        commit_each,
        dry_run,
        interactive=False,  # Feature patches don't support interactive mode
        feature_name=feature_name,
        reset_to=reset_to,
    )

    # Summary
    log_info(f"\nSummary: {applied} applied, {len(failed)} failed")

    if failed:
        log_error("Failed patches:")
        for p in failed:
            log_error(f"  - {p}")

    return applied, failed


def apply_single_file_patch(
    build_ctx: Context,
    chromium_path: str,
    reset_to: Optional[str] = None,
    dry_run: bool = False,
) -> Tuple[bool, Optional[str]]:
    """Apply patch for a single chromium file.

    Args:
        build_ctx: Build context
        chromium_path: Path to file in chromium (e.g., chrome/common/foo.h)
        reset_to: Commit to reset file to before applying
        dry_run: If True, only check if patch would apply

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    patch_path = build_ctx.get_patch_path_for_file(chromium_path)

    if not patch_path.exists():
        return False, f"No patch found for: {chromium_path}"

    log_info(f"Applying patch for: {chromium_path}")
    if dry_run:
        log_info("DRY RUN - No changes will be made")

    return apply_single_patch(
        patch_path,
        build_ctx.chromium_src,
        dry_run=dry_run,
        relative_to=build_ctx.get_dev_patches_dir(),
        reset_to=reset_to,
    )


# CLI Commands - Thin wrappers around core functions
@click.group(name="apply")
def apply_group():
    """Apply patches to Chromium source"""
    pass


@apply_group.command(name="all")
@click.option("--commit-each", is_flag=True, help="Create git commit after each patch")
@click.option("--dry-run", is_flag=True, help="Test patches without applying")
@click.pass_context
def apply_all(ctx, commit_each, dry_run):
    """Apply all patches from chromium_src/

    \b
    Examples:
      dev apply all
      dev apply all --commit-each
      dev apply all --dry-run
    """
    chromium_src = ctx.parent.obj.get("chromium_src")

    from dev import create_build_context

    build_ctx = create_build_context(chromium_src)
    if not build_ctx:
        return

    applied, failed = apply_all_patches(build_ctx, commit_each, dry_run)

    # Exit with error code if any patches failed
    if failed:
        ctx.exit(1)


@apply_group.command(name="feature")
@click.argument("feature_name")
@click.option("--commit-each", is_flag=True, help="Create git commit after each patch")
@click.option("--dry-run", is_flag=True, help="Test patches without applying")
@click.pass_context
def apply_feature(ctx, feature_name, commit_each, dry_run):
    """Apply patches for a specific feature

    \b
    Examples:
      dev apply feature llm-chat
      dev apply feature my-feature --commit-each
    """
    chromium_src = ctx.parent.obj.get("chromium_src")

    from dev import create_build_context

    build_ctx = create_build_context(chromium_src)
    if not build_ctx:
        return

    applied, failed = apply_feature_patches(
        build_ctx, feature_name, commit_each, dry_run
    )

    # Exit with error code if any patches failed
    if failed:
        ctx.exit(1)


# CommandModule wrappers for dev CLI

class ApplyAllModule(CommandModule):
    """Apply all patches from chromium_patches/"""
    produces = []
    requires = []
    description = "Apply all patches from chromium_patches/"

    def validate(self, ctx: Context) -> None:
        """Validate git is available"""
        import shutil
        if not shutil.which("git"):
            raise ValidationError("Git is not available in PATH")
        if not ctx.chromium_src.exists():
            raise ValidationError(f"Chromium source not found: {ctx.chromium_src}")

    def execute(self, ctx: Context, interactive: bool = True, commit: bool = False, reset_to: Optional[str] = None, **kwargs) -> None:
        """Execute apply all patches

        Args:
            interactive: Interactive mode (ask before each patch)
            commit: Create git commit after each patch
            reset_to: Commit to reset files to before applying (optional)
        """
        applied, failed = apply_all_patches(
            ctx,
            commit_each=commit,
            dry_run=False,
            interactive=interactive,
            reset_to=reset_to,
        )
        if failed:
            raise RuntimeError(f"Failed to apply {len(failed)} patches")


class ApplyFeatureModule(CommandModule):
    """Apply patches for a specific feature"""
    produces = []
    requires = []
    description = "Apply patches for a specific feature"

    def validate(self, ctx: Context) -> None:
        """Validate git is available"""
        import shutil
        if not shutil.which("git"):
            raise ValidationError("Git is not available in PATH")
        if not ctx.chromium_src.exists():
            raise ValidationError(f"Chromium source not found: {ctx.chromium_src}")

    def execute(self, ctx: Context, feature_name: str, interactive: bool = True, commit: bool = False, reset_to: Optional[str] = None, **kwargs) -> None:
        """Execute apply feature patches

        Args:
            feature_name: Name of the feature to apply
            interactive: Interactive mode (ask before each patch)
            commit: Create git commit after applying
            reset_to: Commit to reset files to before applying (optional)
        """
        applied, failed = apply_feature_patches(
            ctx,
            feature_name,
            commit_each=commit,
            dry_run=False,
            reset_to=reset_to,
        )
        if failed:
            raise RuntimeError(f"Failed to apply {len(failed)} patches for feature '{feature_name}'")
