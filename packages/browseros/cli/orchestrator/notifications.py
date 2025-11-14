"""Notification integrations for the build system."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from cli.orchestrator.runner import RunnerEvent, EventData

# Add parent paths to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent))


class SlackNotifier:
    """Slack notification handler that bridges to existing Slack module."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self._build_type = None
        self._architectures = None
        self._current_step = None

        # Import existing Slack functions if enabled
        if self.enabled and os.environ.get("SLACK_WEBHOOK_URL"):
            try:
                from build.modules.slack import (
                    notify_build_started,
                    notify_build_step,
                    notify_build_success,
                    notify_build_failure,
                    notify_build_interrupted,
                    notify_gcs_upload,
                )
                self.notify_build_started = notify_build_started
                self.notify_build_step = notify_build_step
                self.notify_build_success = notify_build_success
                self.notify_build_failure = notify_build_failure
                self.notify_build_interrupted = notify_build_interrupted
                self.notify_gcs_upload = notify_gcs_upload
                print("✓ Slack notifications enabled")
            except ImportError as e:
                print(f"Warning: Could not import Slack module: {e}")
                self.enabled = False
        elif self.enabled:
            print("Warning: SLACK_WEBHOOK_URL not set, disabling Slack notifications")
            self.enabled = False

    def on_pipeline_start(self, data: EventData):
        """Handle pipeline start event."""
        if not self.enabled:
            return

        # Extract build info from context if available
        if hasattr(data, 'metadata') and data.metadata:
            self._build_type = data.metadata.get('build_type', 'release')
            self._architectures = data.metadata.get('architectures', ['unknown'])

        # Send notification
        try:
            self.notify_build_started(
                build_type=self._build_type or 'release',
                architectures=str(self._architectures or [])
            )
        except Exception as e:
            print(f"Slack notification error: {e}")

    def on_pipeline_end(self, data: EventData):
        """Handle pipeline end event."""
        if not self.enabled:
            return

        success = data.metadata.get("success", False) if data.metadata else False
        message = data.metadata.get("message", "") if data.metadata else ""

        try:
            if success:
                self.notify_build_success(
                    build_type=self._build_type or 'release',
                    message=message or "Build completed successfully"
                )
            else:
                self.notify_build_failure(
                    error_message=message or "Build failed",
                    build_type=self._build_type or 'release'
                )
        except Exception as e:
            print(f"Slack notification error: {e}")

    def on_step_start(self, data: EventData):
        """Handle step start event."""
        if not self.enabled:
            return

        self._current_step = data.step_name

        # Map module names to user-friendly descriptions
        step_descriptions = {
            "clean": "Cleaning build artifacts",
            "setup-env": "Setting up environment",
            "git-sync": "Syncing Git and Chromium source",
            "patch-chromium": "Applying Chromium patches",
            "patch-strings": "Applying string replacements",
            "patch-sparkle": "Setting up Sparkle framework",
            "patch-apply": "Applying Git patches",
            "copy-resources": "Copying resources",
            "configure": "Configuring build with GN",
            "build": "Building the browser",
            "sign": "Signing binaries",
            "sign-mac": "Signing macOS app",
            "sign-windows": "Signing Windows binaries",
            "package": "Creating package",
            "package-mac": "Creating DMG",
            "package-windows": "Creating Windows installer",
            "package-linux": "Creating Linux package",
            "upload-gcs": "Uploading to GCS",
        }

        description = step_descriptions.get(data.step_name, f"Running {data.step_name}")

        try:
            self.notify_build_step(f"Started: {description}")
        except Exception as e:
            print(f"Slack notification error: {e}")

    def on_step_end(self, data: EventData):
        """Handle step end event."""
        if not self.enabled:
            return

        if data.result and not data.result.success:
            # Step failed, notification will be sent by pipeline_end
            return

        # Map module names to completion messages
        step_completions = {
            "build": "Completed building",
            "sign-mac": "Completed macOS signing",
            "sign-windows": "Completed Windows signing",
            "package-mac": "Completed DMG creation",
            "package-windows": "Completed Windows installer creation",
            "package-linux": "Completed Linux package creation",
            "upload-gcs": "Completed upload to GCS",
        }

        if data.step_name in step_completions:
            try:
                self.notify_build_step(step_completions[data.step_name])

                # Special handling for GCS upload
                if data.step_name == "upload-gcs" and data.result and data.result.metadata:
                    gcs_uris = data.result.metadata.get("gcs_uris", [])
                    if gcs_uris:
                        architecture = data.result.metadata.get("architecture", "unknown")
                        self.notify_gcs_upload(architecture, gcs_uris)
            except Exception as e:
                print(f"Slack notification error: {e}")

    def on_step_error(self, data: EventData):
        """Handle step error event."""
        if not self.enabled:
            return

        try:
            self.notify_build_step(f"❌ Error in {data.step_name}: {str(data.error)}")
        except Exception as e:
            print(f"Slack notification error: {e}")


def setup_slack_notifications(runner, enabled: bool = False) -> Optional[SlackNotifier]:
    """Setup Slack notifications for a pipeline runner."""
    if not enabled:
        return None

    notifier = SlackNotifier(enabled=enabled)

    if notifier.enabled:
        # Register event handlers
        runner.add_handler(RunnerEvent.PIPELINE_START, notifier.on_pipeline_start)
        runner.add_handler(RunnerEvent.PIPELINE_END, notifier.on_pipeline_end)
        runner.add_handler(RunnerEvent.STEP_START, notifier.on_step_start)
        runner.add_handler(RunnerEvent.STEP_END, notifier.on_step_end)
        runner.add_handler(RunnerEvent.STEP_ERROR, notifier.on_step_error)

    return notifier