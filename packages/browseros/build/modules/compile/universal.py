#!/usr/bin/env python3
"""
Universal Build Module - Build universal binary (arm64 + x64) for macOS

This module orchestrates building both architectures and merging them into
a universal binary. It replicates the logic from the old build.py.backup
universal build flow.

Design:
    1. Build arm64: resources → configure → compile
    2. Build x64: resources → configure → compile
    3. Merge using universalizer_patched.py
    4. Output: out/Default_universal/BrowserOS.app

Prerequisites (must run BEFORE this module):
    - clean (optional)
    - git_setup
    - sparkle_setup (macOS)
    - chromium_replace
    - string_replaces
    - patches

This module will run (for EACH architecture):
    - resources (arch-specific binaries)
    - configure (GN configuration)
    - compile (ninja build)

Then merge the results.
"""

import shutil
from pathlib import Path
from typing import Optional

from ...common.module import CommandModule, ValidationError
from ...common.context import Context
from ...common.utils import log_info, log_success, log_warning, log_error, IS_MACOS


class UniversalBuildModule(CommandModule):
    """Build universal binary (arm64 + x64) for macOS

    This module handles the complete multi-architecture build and merge workflow.
    It internally creates separate contexts for arm64 and x64, builds each,
    then merges them into a universal binary.

    The base context passed to this module can have any architecture value -
    it will be ignored and arm64/x64 will be built explicitly.
    """

    produces = []
    requires = []
    description = "Build universal binary (arm64 + x64) for macOS"

    def validate(self, ctx: Context) -> None:
        """Validate universal build can run"""
        if not IS_MACOS():
            raise ValidationError("Universal builds only supported on macOS")

        # Check universalizer script exists
        universalizer = ctx.root_dir / "build/modules/package/universalizer_patched.py"
        if not universalizer.exists():
            raise ValidationError(f"Universalizer script not found: {universalizer}")

    def execute(self, ctx: Context) -> None:
        """Build arm64 + x64, then merge into universal binary"""

        log_info("\n" + "=" * 70)
        log_info("🔄 Universal Build Mode")
        log_info("Building arm64 + x64, then merging...")
        log_info("=" * 70)

        # Import modules we'll use
        from ..resources.resources import ResourcesModule
        from ..setup.configure import ConfigureModule
        from .standard import CompileModule

        built_apps = []
        architectures = ["arm64", "x64"]

        # Build each architecture
        for arch in architectures:
            log_info("\n" + "=" * 70)
            log_info(f"🏗️  Building for architecture: {arch}")
            log_info("=" * 70)

            # Create architecture-specific context
            arch_ctx = self._create_arch_context(ctx, arch)

            log_info(f"📍 Chromium: {arch_ctx.chromium_version}")
            log_info(f"📍 BrowserOS: {arch_ctx.browseros_version}")
            log_info(f"📍 Output directory: {arch_ctx.out_dir}")

            # Copy resources (arch-specific binaries like browseros_server, codex)
            # The ResourcesModule reads copy_resources.yaml which filters by arch
            log_info(f"\n📦 Copying resources for {arch}...")
            ResourcesModule().execute(arch_ctx)

            # Configure build (GN gen)
            log_info(f"\n🔧 Configuring {arch}...")
            ConfigureModule().execute(arch_ctx)

            # Compile (ninja)
            log_info(f"\n🏗️  Compiling {arch}...")
            CompileModule().execute(arch_ctx)

            # Get app path for this architecture
            app_path = arch_ctx.get_app_path()

            if not app_path.exists():
                raise RuntimeError(f"Build failed - app not found: {app_path}")

            log_success(f"✅ {arch} build complete: {app_path}")
            built_apps.append(app_path)

        # Merge architectures into universal binary
        log_info("\n" + "=" * 70)
        log_info("🔄 Merging into universal binary...")
        log_info("=" * 70)

        self._merge_universal(ctx, built_apps[0], built_apps[1])

        # Verify universal binary was created
        universal_app = ctx.chromium_src / "out/Default_universal/BrowserOS.app"
        if not universal_app.exists():
            raise RuntimeError(f"Universal binary not found: {universal_app}")

        log_success(f"✅ Universal binary created: {universal_app}")
        log_info("=" * 70)

    def _create_arch_context(self, base_ctx: Context, arch: str) -> Context:
        """Create a new context for a specific architecture

        Args:
            base_ctx: Base context with common settings
            arch: Architecture to build (arm64 or x64)

        Returns:
            New Context object with architecture set
        """
        return Context(
            root_dir=base_ctx.root_dir,
            chromium_src=base_ctx.chromium_src,
            architecture=arch,
            build_type=base_ctx.build_type,
        )

    def _merge_universal(
        self,
        ctx: Context,
        arm64_app: Path,
        x64_app: Path,
    ) -> None:
        """Merge arm64 + x64 into universal binary

        Args:
            ctx: Base context
            arm64_app: Path to arm64 .app bundle
            x64_app: Path to x64 .app bundle

        Raises:
            RuntimeError: If merge fails
        """
        # Use existing merge helper
        from ..package.merge import merge_architectures

        # Prepare output path
        universal_dir = ctx.chromium_src / "out/Default_universal"

        # Clean old universal dir if it exists
        if universal_dir.exists():
            log_info("🧹 Cleaning old universal output directory...")
            shutil.rmtree(universal_dir)

        # Create fresh universal directory
        universal_dir.mkdir(parents=True, exist_ok=True)
        universal_app = universal_dir / "BrowserOS.app"

        # Find universalizer script
        universalizer_script = ctx.root_dir / "build/modules/package/universalizer_patched.py"

        log_info(f"📱 Input 1 (arm64): {arm64_app}")
        log_info(f"📱 Input 2 (x64): {x64_app}")
        log_info(f"🎯 Output (universal): {universal_app}")
        log_info(f"🔧 Universalizer: {universalizer_script}")

        # Merge the architectures
        success = merge_architectures(
            arch1_path=arm64_app,
            arch2_path=x64_app,
            output_path=universal_app,
            universalizer_script=universalizer_script,
        )

        if not success:
            raise RuntimeError("Failed to merge architectures into universal binary")
