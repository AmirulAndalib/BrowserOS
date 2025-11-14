#!/usr/bin/env python3
"""
BrowserOS Build System - Main Entry Point

Unified CLI for building, developing, and releasing BrowserOS browser.

Usage:
    # As installed command:
    browseros build --help

    # As module:
    python -m build.browseros build --help
"""
import typer

from .cli import build

# Create main app
app = typer.Typer(help="BrowserOS Build System")

# Create build sub-app and register build.main as its callback
build_app = typer.Typer()
build_app.callback(invoke_without_command=True)(build.main)

# Add build as a subcommand
app.add_typer(build_app, name="build", help="Build BrowserOS browser")

# TODO: Add dev and release commands in future phases
# app.add_typer(dev_app, name="dev", help="Dev patch management")
# app.add_typer(release_app, name="release", help="Release automation")


if __name__ == "__main__":
    app()
