#!/usr/bin/env python3
"""Notification system for BrowserOS build pipeline"""

import os
import json
import threading
from typing import Optional, Dict, Any
from pathlib import Path
from .utils import log_info, log_warning, log_error


class Notifier:
    """Fire-and-forget notification system"""

    def __init__(self):
        self.slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        self.enabled = bool(self.slack_webhook_url)

    def notify(self, event: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Send notification asynchronously (fire-and-forget)"""
        if not self.enabled:
            return

        # Fire and forget - run in background thread
        thread = threading.Thread(
            target=self._send_notification,
            args=(event, message, details),
            daemon=True
        )
        thread.start()

    def _send_notification(self, event: str, message: str, details: Optional[Dict[str, Any]]) -> None:
        """Internal method to send notification (runs in background thread)"""
        try:
            import requests

            payload = {
                "text": f"*{event}*: {message}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{event}*\n{message}"
                        }
                    }
                ]
            }

            if details:
                fields = []
                for key, value in details.items():
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*{key}:*\n{value}"
                    })

                payload["blocks"].append({
                    "type": "section",
                    "fields": fields
                })

            requests.post(
                self.slack_webhook_url,
                json=payload,
                timeout=5  # Quick timeout for fire-and-forget
            )

        except ImportError:
            pass
        except Exception:
            pass


# Global notifier instance
_notifier = None


def get_notifier() -> Notifier:
    """Get global notifier instance"""
    global _notifier
    if _notifier is None:
        _notifier = Notifier()
    return _notifier


def notify_pipeline_start(pipeline_name: str, modules: list) -> None:
    """Notify that pipeline has started"""
    notifier = get_notifier()
    notifier.notify(
        "Pipeline Started",
        f"Build pipeline started",
        {"Modules": ", ".join(modules)}
    )


def notify_pipeline_end(pipeline_name: str, duration: float) -> None:
    """Notify that pipeline completed successfully"""
    notifier = get_notifier()
    mins = int(duration / 60)
    secs = int(duration % 60)
    notifier.notify(
        "Pipeline Completed ✅",
        f"Build pipeline completed successfully",
        {"Duration": f"{mins}m {secs}s"}
    )


def notify_pipeline_error(pipeline_name: str, error: str) -> None:
    """Notify that pipeline failed with error"""
    notifier = get_notifier()
    notifier.notify(
        "Pipeline Failed ❌",
        f"Build pipeline failed",
        {"Error": error}
    )


def notify_module_start(module_name: str) -> None:
    """Notify that a module started executing"""
    notifier = get_notifier()
    notifier.notify(
        "Module Started",
        f"Module '{module_name}' started",
        None
    )


def notify_module_completion(module_name: str, duration: float) -> None:
    """Notify that a module completed successfully"""
    notifier = get_notifier()
    notifier.notify(
        "Module Completed",
        f"Module '{module_name}' completed",
        {"Duration": f"{duration:.1f}s"}
    )
