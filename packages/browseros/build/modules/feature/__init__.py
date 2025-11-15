"""
Feature module for dev CLI - Manage features
"""

from .feature import (
    list_features,
    show_feature,
    add_feature,
    ListFeaturesModule,
    ShowFeatureModule,
    AddFeatureModule,
)

__all__ = [
    # Legacy functions
    'list_features',
    'show_feature',
    'add_feature',
    # CommandModule classes
    'ListFeaturesModule',
    'ShowFeatureModule',
    'AddFeatureModule',
]