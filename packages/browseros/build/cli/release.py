#!/usr/bin/env python3
"""Release CLI - Thin CLI layer for release automation"""

from typing import Optional

import typer

from ..common.env import EnvConfig
from ..common.utils import log_info, log_error, log_success, log_warning
from ..modules.release import (
    PLATFORMS,
    PLATFORM_DISPLAY_NAMES,
    fetch_all_release_metadata,
    format_size,
    generate_appcast_item,
    generate_release_notes,
    get_repo_from_git,
    check_gh_cli,
    create_github_release,
    download_and_upload_artifacts,
)

app = typer.Typer(
    help="Release automation commands",
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
)


@app.command("list")
def list_artifacts(
    version: str = typer.Option(..., "--version", "-v", help="Version to list (e.g., 0.31.0)"),
):
    """List artifacts for a version from R2"""
    env = EnvConfig()

    if not env.has_r2_config():
        log_error("R2 configuration not set")
        raise typer.Exit(1)

    metadata = fetch_all_release_metadata(version, env)

    if not metadata:
        log_error(f"No release metadata found for version {version}")
        raise typer.Exit(1)

    log_info(f"\n{'='*60}")
    log_info(f"Release: v{version}")
    log_info(f"{'='*60}")

    for platform in PLATFORMS:
        if platform not in metadata:
            continue

        release = metadata[platform]
        log_info(f"\n{PLATFORM_DISPLAY_NAMES[platform]}:")
        log_info(f"  Build Date: {release.get('build_date', 'N/A')}")
        log_info(f"  Chromium: {release.get('chromium_version', 'N/A')}")

        if platform == "macos" and "sparkle_version" in release:
            log_info(f"  Sparkle Version: {release['sparkle_version']}")

        for key, artifact in release.get("artifacts", {}).items():
            size = format_size(artifact.get("size", 0))
            sig_indicator = " [signed]" if "sparkle_signature" in artifact else ""
            log_info(f"  - {key}: {artifact['filename']} ({size}){sig_indicator}")

    log_info(f"\n{'='*60}")


@app.command()
def appcast(
    version: str = typer.Option(..., "--version", "-v", help="Version to generate appcast for"),
):
    """Generate appcast XML snippets for macOS auto-update"""
    env = EnvConfig()

    if not env.has_r2_config():
        log_error("R2 configuration not set")
        raise typer.Exit(1)

    metadata = fetch_all_release_metadata(version, env)

    if "macos" not in metadata:
        log_error(f"No macOS release metadata found for version {version}")
        raise typer.Exit(1)

    release = metadata["macos"]
    sparkle_version = release.get("sparkle_version", "")
    build_date = release.get("build_date", "")
    artifacts = release.get("artifacts", {})

    log_info(f"\n{'='*60}")
    log_info(f"APPCAST SNIPPETS FOR v{version}")
    log_info(f"{'='*60}")

    arch_to_file = {
        "arm64": "appcast.xml",
        "x64": "appcast-x86_64.xml",
        "universal": "appcast.xml",
    }

    for arch in ["arm64", "x64", "universal"]:
        if arch not in artifacts:
            continue

        artifact = artifacts[arch]
        if "sparkle_signature" not in artifact:
            log_warning(f"{arch} artifact missing sparkle_signature")

        log_info(f"\n{arch_to_file[arch]} ({arch}):")
        print(generate_appcast_item(artifact, version, sparkle_version, build_date))

    log_info(f"\n{'='*60}")


@app.command()
def create(
    version: str = typer.Option(..., "--version", "-v", help="Version to release"),
    draft: bool = typer.Option(True, "--draft/--publish", help="Create as draft (default: draft)"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="GitHub repo (owner/name)"),
    skip_upload: bool = typer.Option(False, "--skip-upload", help="Skip uploading artifacts to GitHub"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Release title (default: v{version})"),
):
    """Create GitHub release from R2 artifacts"""
    env = EnvConfig()

    if not env.has_r2_config():
        log_error("R2 configuration not set")
        raise typer.Exit(1)

    # Check gh CLI
    if not check_gh_cli():
        log_error("gh CLI not found. Install from: https://cli.github.com")
        raise typer.Exit(1)

    # Fetch metadata
    metadata = fetch_all_release_metadata(version, env)
    if not metadata:
        log_error(f"No release metadata found for version {version}")
        raise typer.Exit(1)

    log_info(f"\n{'='*60}")
    log_info(f"Creating GitHub Release: v{version}")
    log_info(f"{'='*60}")

    for platform, release in metadata.items():
        artifacts = release.get("artifacts", {})
        log_info(f"  {PLATFORM_DISPLAY_NAMES[platform]}: {len(artifacts)} artifact(s)")

    # Determine repo
    if not repo:
        repo = get_repo_from_git()
        if not repo:
            log_error("Could not detect repo from git remote. Use --repo flag.")
            raise typer.Exit(1)

    log_info(f"  Repo: {repo}")
    log_info(f"  Draft: {draft}")

    # Create release
    release_title = title or f"v{version}"
    notes = generate_release_notes(version, metadata)

    log_info("\nCreating GitHub release...")
    success, result = create_github_release(version, repo, release_title, notes, draft)

    if success:
        log_success(f"Release created: {result}")
    else:
        if "already exists" in result:
            log_warning(result)
        else:
            log_error(f"Failed to create release: {result}")
            raise typer.Exit(1)

    # Upload artifacts
    if not skip_upload:
        log_info("\nUploading artifacts to GitHub release...")
        results = download_and_upload_artifacts(version, repo, metadata)

        failed = [f for f, ok in results if not ok]
        if failed:
            log_warning(f"Failed to upload: {', '.join(failed)}")

    # Print appcast snippet
    if "macos" in metadata:
        log_info("\n" + "=" * 60)
        log_info("APPCAST SNIPPET")
        log_info("=" * 60)

        release = metadata["macos"]
        sparkle_version = release.get("sparkle_version", "")
        build_date = release.get("build_date", "")

        arch_to_file = {"arm64": "appcast.xml", "x64": "appcast-x86_64.xml", "universal": "appcast.xml"}

        for arch in ["arm64", "x64", "universal"]:
            if arch in release.get("artifacts", {}):
                artifact = release["artifacts"][arch]
                log_info(f"\n{arch_to_file[arch]} ({arch}):")
                print(generate_appcast_item(artifact, version, sparkle_version, build_date))

    log_info(f"\n{'='*60}")
    log_success(f"Release v{version} complete!")
