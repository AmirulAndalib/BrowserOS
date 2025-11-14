#!/usr/bin/env python3
"""Test script for new pipeline configurations."""

import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent))

from cli.orchestrator.context import PipelineContext, BuildContext
from cli.orchestrator.loader import ConfigLoader
from cli.orchestrator.plan import PlanBuilder


def test_config(config_path: Path, platform: str, architecture: str = "x64"):
    """Test loading and building a plan from a config."""
    print(f"\n📄 Testing: {config_path.name}")
    print(f"   Platform: {platform}, Architecture: {architecture}")

    try:
        # Load config
        loader = ConfigLoader()
        config = loader.load_config(config_path)

        # Create contexts
        pipeline_ctx = PipelineContext(
            root_path=Path.cwd(),
            config_path=config_path,
            dry_run=True
        )

        build_ctx = BuildContext(
            pipeline_ctx=pipeline_ctx,
            architecture=architecture,
            build_type="release" if "release" in str(config_path) else "debug",
            platform=platform,
            chromium_path=Path("/tmp/chromium/src")  # Dummy path
        )

        # Build plan
        plan_builder = PlanBuilder()
        plan = plan_builder.build_plan(config, build_ctx)

        print(f"   ✅ Successfully built plan with {len(plan.steps)} steps:")

        # Group steps by phase
        phases = {
            "prep": [],
            "patch": [],
            "build": [],
            "package": [],
            "dist": []
        }

        for step in plan.steps:
            name = step.module_name
            if name in ["clean", "setup-env", "git-sync"]:
                phases["prep"].append(name)
            elif "patch" in name or name == "copy-resources":
                phases["patch"].append(name)
            elif name in ["configure", "build"]:
                phases["build"].append(name)
            elif "sign" in name or "package" in name:
                phases["package"].append(name)
            elif "upload" in name:
                phases["dist"].append(name)

        # Display grouped steps
        for phase_name, steps in phases.items():
            if steps:
                print(f"      {phase_name:8}: {', '.join(steps)}")

        return True

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_verb_flags_with_new_config():
    """Test that verb flags work with new configs."""
    print("\n🧪 Testing Verb Flag Filtering")

    config_path = Path("cli/config/release-macos.yaml")
    if not config_path.exists():
        print("   ⚠️  Config not found")
        return False

    try:
        loader = ConfigLoader()
        config = loader.load_config(config_path)

        pipeline_ctx = PipelineContext(
            root_path=Path.cwd(),
            config_path=config_path,
            dry_run=True
        )

        # Simulate --clean --sync --build flags
        build_ctx = BuildContext(
            pipeline_ctx=pipeline_ctx,
            architecture="x64",
            build_type="release",
            platform="macos",
            chromium_path=Path("/tmp/chromium/src"),
            only_modules=["clean", "setup-env", "git-sync", "configure", "build"]
        )

        plan_builder = PlanBuilder()
        plan = plan_builder.build_plan(config, build_ctx)

        actual = [s.module_name for s in plan.steps]
        expected = ["clean", "setup-env", "git-sync", "configure", "build"]

        if actual == expected:
            print(f"   ✅ Verb flags correctly filtered to: {', '.join(actual)}")
            return True
        else:
            print(f"   ❌ Expected: {expected}")
            print(f"   ❌ Got: {actual}")
            return False

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def test_conditional_execution():
    """Test when conditions work correctly."""
    print("\n🧪 Testing Conditional Execution")

    config = {
        "name": "test-conditional",
        "steps": [
            "clean",
            {"patch-sparkle": {"when": "platform == 'macos'"}},
            {"sign-mac-universal": {"when": "arch == 'universal'"}},
            {"upload-gcs": {"when": "build_type == 'release'"}}
        ]
    }

    try:
        pipeline_ctx = PipelineContext(
            root_path=Path.cwd(),
            config_path=Path("test.yaml"),
            dry_run=True
        )

        # Test with macOS, x64, release
        build_ctx = BuildContext(
            pipeline_ctx=pipeline_ctx,
            architecture="x64",
            build_type="release",
            platform="macos",
            chromium_path=Path("/tmp/chromium/src")
        )

        plan_builder = PlanBuilder()
        plan = plan_builder.build_plan(config, build_ctx)

        steps = [s.module_name for s in plan.steps]

        # Should include: clean, patch-sparkle (macOS), upload-gcs (release)
        # Should NOT include: sign-mac-universal (not universal arch)
        expected_in = ["clean", "patch-sparkle", "upload-gcs"]
        expected_out = ["sign-mac-universal"]

        success = True
        for step in expected_in:
            if step not in steps:
                print(f"   ❌ Expected '{step}' but not found")
                success = False

        for step in expected_out:
            if step in steps:
                print(f"   ❌ Unexpected '{step}' was included")
                success = False

        if success:
            print(f"   ✅ Conditional execution works correctly")
            print(f"      Included: {', '.join(steps)}")

        return success

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Testing New Pipeline Configurations")
    print("=" * 60)

    success = True

    # Test all release configs
    configs_to_test = [
        ("cli/config/release-macos.yaml", "macos", "arm64"),
        ("cli/config/release-windows.yaml", "windows", "x64"),
        ("cli/config/release-linux.yaml", "linux", "x64"),
        ("cli/config/debug.yaml", "macos", "x64"),
        ("cli/config/quick-build.yaml", "macos", "x64"),
    ]

    print("\n📦 Testing Pipeline Configurations")
    print("-" * 40)

    for config_path, platform, arch in configs_to_test:
        path = Path(config_path)
        if path.exists():
            if not test_config(path, platform, arch):
                success = False
        else:
            print(f"\n📄 Skipping: {config_path} (not found)")

    # Test verb flags
    print("\n🔧 Testing Features")
    print("-" * 40)

    if not test_verb_flags_with_new_config():
        success = False

    if not test_conditional_execution():
        success = False

    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        print("\nThe new configs are working correctly:")
        print("- Pipeline loading works")
        print("- Plan building works")
        print("- Verb flag filtering works")
        print("- Conditional execution works")
        print("\n🎉 Ready to use the new pipeline system!")
    else:
        print("❌ Some tests failed")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())