#!/usr/bin/env python3
"""Main entry point for BrowserOS CLI."""

import sys
from pathlib import Path

# Add the parent directory to Python path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli import app


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()