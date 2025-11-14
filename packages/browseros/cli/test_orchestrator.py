#!/usr/bin/env python3
"""Test script for the orchestrator (plan builder and runner)."""

import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent))

from cli.orchestrator.context import PipelineContext, BuildContext
from cli.orchestrator.loader import ConfigLoader
from cli.orchestrator.plan import PlanBuilder
from cli.orchestrator.runner import PipelineRunner, RunnerEvent


def test_plan_builder():
    """Test the plan builder with different configs."""
    print("🧪 Testing Plan Builder")
    print("=" * 60)

    # Test with new pipeline format
    loader = ConfigLoader()

    # Test macOS pipeline
    config_path = Path("build/config/pipelines/macos-release.yaml")
    if config_path.exists():
        print(f"\n📄 Loading pipeline config: {config_path}")
        config = loader.load_config(config_path)

        # Create contexts
        pipeline_ctx = PipelineContext(
            root_path=Path.cwd(),
            config_path=config_path,
            dry_run=True
        )

        build_ctx = BuildContext(
            pipeline_ctx=pipeline_ctx,
            architecture="arm64",
            build_type="release",
            platform="macos",
            chromium_path=Path("/tmp/chromium/src")  # Dummy path for testing
        )

        # Build plan
        plan_builder = PlanBuilder()
        plan = plan_builder.build_plan(config, build_ctx)

        print(f"✅ Built plan with {len(plan.steps)} steps:")
        for step in plan.steps:
            print(f"   - {step.module_name}")

    # Test with old config format
    old_config_path = Path("build/config/release.macos.yaml")
    if old_config_path.exists():
        print(f"\n📄 Testing backward compatibility with: {old_config_path}")
        config = loader.load_config(old_config_path)

        # Create contexts
        pipeline_ctx = PipelineContext(
            root_path=Path.cwd(),
            config_path=old_config_path,
            dry_run=True
        )

        build_ctx = BuildContext(
            pipeline_ctx=pipeline_ctx,
            architecture="x64",
            build_type="release",
            platform="macos",
            chromium_path=Path("/tmp/chromium/src")
        )

        # Build plan
        plan_builder = PlanBuilder()
        plan = plan_builder.build_plan(config, build_ctx)

        print(f"✅ Built plan from old format with {len(plan.steps)} steps:")
        for step in plan.steps:
            print(f"   - {step.module_name}")

    return True


def test_runner_dry_run():
    """Test the runner in dry-run mode."""
    print("\n🧪 Testing Runner (Dry Run)")
    print("=" * 60)

    # Create a simple test plan
    loader = ConfigLoader()
    config_path = Path("build/config/pipelines/macos-release.yaml")

    if not config_path.exists():
        print("⚠️  Pipeline config not found, creating test config")
        # Create a minimal test config
        config = {
            "pipelines": {
                "test": {
                    "description": "Test pipeline",
                    "steps": ["clean", "setup-env"]
                }
            }
        }
    else:
        config = loader.load_config(config_path)

    # Create contexts
    pipeline_ctx = PipelineContext(
        root_path=Path.cwd(),
        config_path=config_path if config_path.exists() else Path("test.yaml"),
        dry_run=True  # Important: dry run mode
    )

    build_ctx = BuildContext(
        pipeline_ctx=pipeline_ctx,
        architecture="arm64",
        build_type="release",
        platform="macos",
        chromium_path=Path("/tmp/chromium/src"),
        only_modules=["clean", "copy-resources"]  # Use modules that don't check env vars
    )

    # Build plan
    plan_builder = PlanBuilder()
    plan = plan_builder.build_plan(config, build_ctx)

    print(f"📋 Plan has {len(plan.steps)} steps")

    # Create runner with event tracking
    runner = PipelineRunner(pipeline_ctx)

    # Track events
    events_fired = []

    def track_event(data):
        events_fired.append(data.event)
        print(f"  Event: {data.event.value}")

    # Register event handlers
    for event in RunnerEvent:
        runner.add_handler(event, track_event)

    # Execute plan
    print("\n▶️  Executing plan in dry-run mode...")
    result = runner.execute(plan, build_ctx)

    print(f"\n{'✅' if result.success else '❌'} Result: {result.message}")
    print(f"📊 Events fired: {len(events_fired)}")

    return result.success


def test_verb_flags():
    """Test that verb flags work correctly."""
    print("\n🧪 Testing Verb Flags")
    print("=" * 60)

    pipeline_ctx = PipelineContext(
        root_path=Path.cwd(),
        config_path=Path("test.yaml"),
        dry_run=True
    )

    # Test with verb flags simulating --clean --sync --build
    build_ctx = BuildContext(
        pipeline_ctx=pipeline_ctx,
        architecture="x64",
        build_type="debug",
        platform="macos",
        chromium_path=Path("/tmp/chromium/src"),
        only_modules=["clean", "setup-env", "git-sync", "configure", "build"]
    )

    # Simple config
    config = {
        "description": "Test with verb flags",
        "steps": [
            "clean", "setup-env", "git-sync", "patch-chromium",
            "patch-strings", "patch-sparkle", "patch-apply",
            "copy-resources", "configure", "build", "sign-mac",
            "package-mac", "upload-gcs"
        ]
    }

    plan_builder = PlanBuilder()
    plan = plan_builder.build_plan(config, build_ctx)

    print(f"✅ With verb flags (--clean --sync --build), got {len(plan.steps)} steps:")
    for step in plan.steps:
        print(f"   - {step.module_name}")

    expected = ["clean", "setup-env", "git-sync", "configure", "build"]
    actual = [s.module_name for s in plan.steps]

    if actual == expected:
        print("✅ Verb flag filtering works correctly!")
        return True
    else:
        print(f"❌ Expected: {expected}")
        print(f"❌ Got: {actual}")
        return False


def main():
    """Run all tests."""
    print("🚀 Testing Orchestrator Components")
    print("=" * 70)

    success = True

    try:
        # Test plan builder
        if not test_plan_builder():
            success = False
    except Exception as e:
        print(f"❌ Plan builder test failed: {e}")
        import traceback
        traceback.print_exc()
        success = False

    try:
        # Test runner
        if not test_runner_dry_run():
            success = False
    except Exception as e:
        print(f"❌ Runner test failed: {e}")
        import traceback
        traceback.print_exc()
        success = False

    try:
        # Test verb flags
        if not test_verb_flags():
            success = False
    except Exception as e:
        print(f"❌ Verb flag test failed: {e}")
        import traceback
        traceback.print_exc()
        success = False

    print("\n" + "=" * 70)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())