"""
Apply module for dev CLI - Apply patches to Chromium
"""

from .apply import (
    apply_all,
    apply_feature,
    ApplyAllModule,
    ApplyFeatureModule,
)

__all__ = [
    # Legacy functions
    'apply_all',
    'apply_feature',
    # CommandModule classes
    'ApplyAllModule',
    'ApplyFeatureModule',
]