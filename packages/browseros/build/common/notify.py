#!/usr/bin/env python3
"""
Notifier classes for build progress updates
"""

import os
import json
import time
from typing import Optional, List


class Notifier:
    """Base notifier interface"""

    def step_started(self, step_name: str, message: str = None):
        """Called when a build step starts

        Args:
            step_name: Name of the step (e.g., "build", "sign", "package")
            message: Optional additional context (e.g., "for arm64 architecture")
        """
        pass

    def step_completed(self, step_name: str, message: str = None):
        """Called when a build step completes successfully

        Args:
            step_name: Name of the step
            message: Optional completion message (e.g., "in 45s", "3 files processed")
        """
        pass

    def step_failed(self, step_name: str, error: str, message: str = None):
        """Called when a build step fails

        Args:
            step_name: Name of the step
            error: Error description
            message: Optional additional context
        """
        pass


class NullNotifier(Notifier):
    """No-op notifier that does nothing"""
    pass


class SlackNotifier(Notifier):
    """Slack notification implementation"""

    def __init__(self, webhook_url: str = None):
        """Initialize with webhook URL from parameter or environment"""
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
        self.build_start_time = None

    def _get_os_info(self) -> tuple[str, str]:
        """Get OS emoji and name for Slack notifications"""
        from .utils import get_platform
        platform = get_platform()
        if platform == "macos":
            return "🍎", "macOS"
        elif platform == "windows":
            return "🪟", "Windows"
        elif platform == "linux":
            return "🐧", "Linux"
        else:
            return "💻", platform.capitalize()

    def _send_notification(self, message: str, success: bool = True) -> bool:
        """Send a notification to Slack"""
        if not self.webhook_url:
            return True  # Silently skip if no webhook configured

        try:
            import requests
        except ImportError:
            from .utils import log_warning
            log_warning("requests module not available for Slack notifications")
            return False

        # Choose emoji and color based on success status
        emoji = "✅" if success else "❌"
        color = "good" if success else "danger"

        # Get OS information
        os_emoji, os_name = self._get_os_info()

        # Create Slack message payload
        payload = {
            "attachments": [
                {
                    "color": color,
                    "fields": [
                        {
                            "title": "BrowserOS Build",
                            "value": f"{emoji} {message}",
                            "short": False,
                        }
                    ],
                    "footer": f"{os_emoji} BrowserOS Build System - {os_name}",
                    "ts": None,  # Slack will use current timestamp
                }
            ]
        }

        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            if response.status_code == 200:
                from .utils import log_info
                log_info(f"📲 Slack notification sent")
                return True
            else:
                from .utils import log_warning
                log_warning(f"Slack notification failed with status {response.status_code}")
                return False

        except requests.RequestException as e:
            from .utils import log_warning
            log_warning(f"Failed to send Slack notification: {e}")
            return False

    def step_started(self, step_name: str, message: str = None):
        """Notify when a build step starts"""
        notification = f"Starting: {step_name}"
        if message:
            notification += f" - {message}"
        self._send_notification(notification, success=True)

    def step_completed(self, step_name: str, message: str = None):
        """Notify when a build step completes"""
        # Only send notification for major steps
        major_steps = ['build', 'package', 'sign', 'upload', 'compile', 'merge']
        if any(step in step_name.lower() for step in major_steps):
            notification = f"Completed: {step_name}"
            if message:
                notification += f" - {message}"
            self._send_notification(notification, success=True)

    def step_failed(self, step_name: str, error: str, message: str = None):
        """Notify when a build step fails"""
        notification = f"Failed: {step_name}\nError: {error}"
        if message:
            notification += f"\n{message}"
        self._send_notification(notification, success=False)


class ConsoleNotifier(Notifier):
    """Console output notifier for debugging"""

    def __init__(self):
        from .utils import log_info
        self.log_info = log_info

    def step_started(self, step_name: str, message: str = None):
        notification = f"[NOTIFY] Step started: {step_name}"
        if message:
            notification += f" - {message}"
        self.log_info(notification)

    def step_completed(self, step_name: str, message: str = None):
        notification = f"[NOTIFY] Step completed: {step_name}"
        if message:
            notification += f" - {message}"
        self.log_info(notification)

    def step_failed(self, step_name: str, error: str, message: str = None):
        notification = f"[NOTIFY] Step failed: {step_name} - {error}"
        if message:
            notification += f" - {message}"
        self.log_info(notification)