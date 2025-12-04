#!/usr/bin/env python3
"""Release module - Business logic for release automation"""

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..common.env import EnvConfig
from ..common.utils import log_info, log_error, log_success, log_warning
from .upload import get_release_json, get_r2_client, BOTO3_AVAILABLE

PLATFORMS = ["macos", "win", "linux"]
PLATFORM_DISPLAY_NAMES = {"macos": "macOS", "win": "Windows", "linux": "Linux"}


def fetch_all_release_metadata(
    version: str, env: Optional[EnvConfig] = None
) -> Dict[str, Dict]:
    """Fetch release.json from all platforms for a version

    Args:
        version: Semantic version (e.g., "0.31.0")
        env: Optional EnvConfig instance

    Returns:
        Dict mapping platform name to release metadata
    """
    if env is None:
        env = EnvConfig()

    metadata = {}
    for platform in PLATFORMS:
        release_data = get_release_json(version, platform, env)
        if release_data:
            metadata[platform] = release_data

    return metadata


def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size"""
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    elif size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.0f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.0f} KB"
    return f"{size_bytes} B"


def generate_appcast_item(
    artifact: Dict,
    version: str,
    sparkle_version: str,
    build_date: str,
) -> str:
    """Generate Sparkle <item> XML for an artifact

    Args:
        artifact: Artifact dict with url, sparkle_signature, size/sparkle_length
        version: Semantic version
        sparkle_version: Sparkle version string (e.g., "7534.49")
        build_date: ISO format build date

    Returns:
        XML string for Sparkle appcast <item>
    """
    # Parse build date to RFC 2822 format
    try:
        dt = datetime.fromisoformat(build_date.replace("Z", "+00:00"))
        pub_date = dt.strftime("%a, %d %b %Y %H:%M:%S %z")
    except Exception:
        pub_date = build_date

    signature = artifact.get("sparkle_signature", "")
    length = artifact.get("sparkle_length", artifact.get("size", 0))

    return f"""<item>
  <title>BrowserOS - {version}</title>
  <description sparkle:format="plain-text">
  </description>
  <sparkle:version>{sparkle_version}</sparkle:version>
  <sparkle:shortVersionString>{version}</sparkle:shortVersionString>
  <pubDate>{pub_date}</pubDate>
  <link>https://browseros.com</link>
  <enclosure
    url="{artifact['url']}"
    sparkle:edSignature="{signature}"
    length="{length}"
    type="application/octet-stream" />
  <sparkle:minimumSystemVersion>10.15</sparkle:minimumSystemVersion>
</item>"""


def generate_release_notes(version: str, metadata: Dict[str, Dict]) -> str:
    """Generate markdown release notes from metadata

    Args:
        version: Semantic version
        metadata: Dict mapping platform to release metadata

    Returns:
        Markdown formatted release notes
    """
    # Get chromium version from first available platform
    chromium_version = "unknown"
    for platform in PLATFORMS:
        if platform in metadata:
            chromium_version = metadata[platform].get("chromium_version", "unknown")
            break

    notes = f"""## BrowserOS v{version}

Chromium version: {chromium_version}

### Downloads

"""
    for platform in PLATFORMS:
        if platform not in metadata:
            continue

        platform_name = PLATFORM_DISPLAY_NAMES[platform]
        notes += f"**{platform_name}:**\n"

        for key, artifact in metadata[platform].get("artifacts", {}).items():
            notes += f"- [{artifact['filename']}]({artifact['url']})\n"
        notes += "\n"

    return notes


def get_repo_from_git() -> Optional[str]:
    """Get GitHub repo (owner/name) from git remote

    Returns:
        Repo string like "owner/repo" or None if detection fails
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        remote_url = result.stdout.strip()

        if "github.com" not in remote_url:
            return None

        # Parse: git@github.com:owner/repo.git or https://github.com/owner/repo.git
        if remote_url.startswith("git@"):
            return remote_url.split(":")[-1].replace(".git", "")
        else:
            return "/".join(remote_url.split("/")[-2:]).replace(".git", "")
    except Exception:
        return None


def check_gh_cli() -> bool:
    """Check if gh CLI is available"""
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


def create_github_release(
    version: str,
    repo: str,
    title: str,
    notes: str,
    draft: bool = True,
) -> Tuple[bool, str]:
    """Create GitHub release via gh CLI

    Args:
        version: Semantic version (used as tag)
        repo: GitHub repo (owner/name)
        title: Release title
        notes: Release notes (markdown)
        draft: Create as draft (default: True)

    Returns:
        (success, url_or_error) tuple
    """
    cmd = [
        "gh",
        "release",
        "create",
        f"v{version}",
        "--repo",
        repo,
        "--title",
        title,
        "--notes",
        notes,
    ]
    if draft:
        cmd.append("--draft")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if "already exists" in e.stderr:
            return False, f"Release v{version} already exists"
        return False, e.stderr


def download_file(url: str, dest: Path) -> bool:
    """Download file from URL using curl

    Args:
        url: Source URL
        dest: Destination path

    Returns:
        True if successful
    """
    try:
        subprocess.run(
            ["curl", "-L", "-o", str(dest), url],
            check=True,
            capture_output=True,
        )
        return True
    except Exception:
        return False


def upload_to_github_release(
    version: str,
    repo: str,
    file_path: Path,
) -> bool:
    """Upload file to existing GitHub release

    Args:
        version: Release version (tag)
        repo: GitHub repo (owner/name)
        file_path: Local file to upload

    Returns:
        True if successful
    """
    try:
        subprocess.run(
            ["gh", "release", "upload", f"v{version}", str(file_path), "--repo", repo],
            check=True,
            capture_output=True,
        )
        return True
    except Exception:
        return False


def download_and_upload_artifacts(
    version: str,
    repo: str,
    metadata: Dict[str, Dict],
    platforms: List[str] = None,
) -> List[Tuple[str, bool]]:
    """Download artifacts from R2 and upload to GitHub release

    Args:
        version: Release version
        repo: GitHub repo
        metadata: Release metadata dict
        platforms: Platforms to process (default: ["win", "linux"])

    Returns:
        List of (filename, success) tuples
    """
    if platforms is None:
        platforms = ["win", "linux"]  # Skip macOS - served from CDN

    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        for platform in platforms:
            if platform not in metadata:
                continue

            for key, artifact in metadata[platform].get("artifacts", {}).items():
                url = artifact["url"]
                filename = artifact["filename"]
                local_path = tmppath / filename

                log_info(f"  Downloading {filename}...")
                if not download_file(url, local_path):
                    log_error(f"  Failed to download {filename}")
                    results.append((filename, False))
                    continue

                log_info(f"  Uploading {filename}...")
                if upload_to_github_release(version, repo, local_path):
                    log_success(f"  Uploaded {filename}")
                    results.append((filename, True))
                else:
                    log_error(f"  Failed to upload {filename}")
                    results.append((filename, False))

    return results
