#!/usr/bin/env python3
"""Test script to verify wrapped modules can be instantiated and registered."""

import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent))

from cli.modules.registry import get_module, list_modules
from cli.orchestrator.module import Phase


def test_modules():
    """Test that all registered modules can be instantiated."""

    print("🧪 Testing module registry...")
    print("=" * 60)

    modules = list_modules()
    print(f"\n📦 Found {len(modules)} registered modules:")

    success_count = 0
    failed_modules = []

    for name, module_class in modules.items():
        try:
            # Try to instantiate the module
            instance = get_module(name)

            # Verify basic attributes
            assert hasattr(instance, 'name'), f"Module {name} missing 'name' attribute"
            assert hasattr(instance, 'phase'), f"Module {name} missing 'phase' attribute"
            assert hasattr(instance, 'should_run'), f"Module {name} missing 'should_run' method"
            assert hasattr(instance, 'run'), f"Module {name} missing 'run' method"

            # Display module info
            print(f"\n  ✅ {name:20} [{instance.phase.value:10}] order={instance.default_order}")

            # Show additional info
            if instance.requires:
                print(f"     requires: {instance.requires}")
            if instance.provides:
                print(f"     provides: {instance.provides}")
            if hasattr(instance, 'supported_platforms') and instance.supported_platforms != {"macos", "linux", "windows"}:
                print(f"     platforms: {instance.supported_platforms}")

            success_count += 1

        except Exception as e:
            print(f"\n  ❌ {name:20} - Failed: {str(e)}")
            failed_modules.append((name, str(e)))

    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Successfully loaded: {success_count}/{len(modules)} modules")

    if failed_modules:
        print(f"❌ Failed modules: {len(failed_modules)}")
        for name, error in failed_modules:
            print(f"   - {name}: {error}")
        return False

    # Group modules by phase
    print("\n📊 Modules by phase:")
    phases = {}
    for name in modules:
        instance = get_module(name)
        phase = instance.phase.value
        if phase not in phases:
            phases[phase] = []
        phases[phase].append(name)

    for phase in ["prepare", "build", "sign", "package", "publish"]:
        if phase in phases:
            print(f"  {phase:10}: {', '.join(phases[phase])}")

    return True


if __name__ == "__main__":
    success = test_modules()
    sys.exit(0 if success else 1)