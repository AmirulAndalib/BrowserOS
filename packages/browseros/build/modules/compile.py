#!/usr/bin/env python3
"""Build execution module for BrowserOS build system"""

import tempfile
import shutil
from pathlib import Path
from ..common.module import BuildModule, ValidationError
from ..common.context import BuildContext
from ..common.utils import (
    run_command,
    log_info,
    log_success,
    log_warning,
    join_paths,
    IS_WINDOWS,
)


class CompileModule(BuildModule):
    produces = ["built_app"]
    requires = []
    description = "Build BrowserOS using autoninja"

    def validate(self, ctx: BuildContext) -> None:
        if not ctx.chromium_src.exists():
            raise ValidationError(f"Chromium source not found: {ctx.chromium_src}")

        if not ctx.browseros_chromium_version:
            raise ValidationError("BrowserOS chromium version not set")

        args_file = ctx.get_gn_args_file()
        if not args_file.exists():
            raise ValidationError(f"Build not configured - args.gn not found: {args_file}")

    def execute(self, ctx: BuildContext) -> None:
        log_info("\n🔨 Building BrowserOS (this will take a while)...")

        self._create_version_file(ctx)

        autoninja_cmd = "autoninja.bat" if IS_WINDOWS() else "autoninja"
        log_info("Using default autoninja parallelism")

        run_command([autoninja_cmd, "-C", ctx.out_dir, "chrome", "chromedriver"], cwd=ctx.chromium_src)

        app_path = ctx.get_chromium_app_path()
        new_path = ctx.get_app_path()

        if app_path.exists() and not new_path.exists():
            shutil.move(str(app_path), str(new_path))

        ctx.artifact_registry.add("built_app", new_path)

        log_success("Build complete!")

    def _create_version_file(self, ctx: BuildContext) -> None:
        parts = ctx.browseros_chromium_version.split(".")
        if len(parts) != 4:
            log_warning(f"Invalid version format: {ctx.browseros_chromium_version}")
            return

        version_content = f"MAJOR={parts[0]}\nMINOR={parts[1]}\nBUILD={parts[2]}\nPATCH={parts[3]}"

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write(version_content)
            temp_path = temp_file.name

        chrome_version_path = join_paths(ctx.chromium_src, "chrome", "VERSION")
        shutil.copy2(temp_path, chrome_version_path)
        Path(temp_path).unlink()

        log_info(f"Created VERSION file: {ctx.browseros_chromium_version}")


def build(ctx: BuildContext) -> bool:
    module = CompileModule()
    module.validate(ctx)
    module.execute(ctx)
    return True
