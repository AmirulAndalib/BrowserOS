#!/usr/bin/env python3
"""
Minimal runner for executing build steps sequentially
"""

from typing import Callable, List, Optional


def run(
    ctx,  # BuildContext - avoid circular import
    steps: List[Callable],
    notifier=None  # Optional[Notifier]
) -> bool:
    """
    Execute steps sequentially

    Args:
        ctx: BuildContext with all state
        steps: List of callables that take ctx and return bool
        notifier: Optional notifier for progress updates

    Returns:
        True if all steps succeeded, False otherwise
    """
    # Import here to avoid circular dependencies
    from ..utils import log_info, log_error
    from .notify import NullNotifier

    notifier = notifier or NullNotifier()

    for step_func in steps:
        step_name = step_func.__name__

        log_info(f"▶ {step_name}")

        # Extract optional message from context if available (e.g., architecture, build type)
        message = None
        if hasattr(ctx, 'architecture') and ctx.architecture:
            message = f"for {ctx.architecture}"

        notifier.step_started(step_name, message)

        try:
            success = step_func(ctx)

            if not success:
                log_error(f"Step failed: {step_name}")
                notifier.step_failed(step_name, "Returned False", message)
                return False

            notifier.step_completed(step_name, message)

        except Exception as e:
            log_error(f"Step failed with exception: {step_name}")
            notifier.step_failed(step_name, str(e), message)
            raise

    return True