#!/usr/bin/env python3
"""Pipeline validation for BrowserOS build system"""

from typing import Dict, List, Type
from .module import BuildModule
from .utils import log_error, log_info


def validate_pipeline(pipeline: List[str], available_modules: Dict[str, Type[BuildModule]]) -> None:
    """Validate that all modules in pipeline exist in available_modules
    
    Raises SystemExit if validation fails
    """
    invalid_modules = []
    
    for module_name in pipeline:
        if module_name not in available_modules:
            invalid_modules.append(module_name)
    
    if invalid_modules:
        log_error("Invalid module names in pipeline:")
        for module_name in invalid_modules:
            log_error(f"  - {module_name}")
        
        log_error("\nAvailable modules:")
        for module_name in sorted(available_modules.keys()):
            module_class = available_modules[module_name]
            log_info(f"  - {module_name}: {module_class.description}")
        
        raise SystemExit(1)


def show_available_modules(available_modules: Dict[str, Type[BuildModule]]) -> None:
    """Display all available modules with descriptions"""
    log_info("\nAvailable modules:\n")
    
    for module_name in sorted(available_modules.keys()):
        module_class = available_modules[module_name]
        log_info(f"  {module_name:20} - {module_class.description}")
        
        if module_class.produces:
            log_info(f"{'':22}Produces: {', '.join(module_class.produces)}")
        if module_class.requires:
            log_info(f"{'':22}Requires: {', '.join(module_class.requires)}")
        log_info("")
