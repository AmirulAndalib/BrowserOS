"""Pipeline execution runner."""

from typing import Optional, Callable, Dict, Any
from enum import Enum
from dataclasses import dataclass
from cli.orchestrator.context import PipelineContext, BuildContext
from cli.orchestrator.plan import BuildPlan
from cli.orchestrator.module import StepResult


class RunnerEvent(str, Enum):
    """Events emitted during pipeline execution."""
    PIPELINE_START = "pipeline_start"
    PIPELINE_END = "pipeline_end"
    STEP_START = "step_start"
    STEP_END = "step_end"
    STEP_SKIP = "step_skip"
    STEP_ERROR = "step_error"


@dataclass
class EventData:
    """Data passed to event handlers."""
    event: RunnerEvent
    step_name: Optional[str] = None
    result: Optional[StepResult] = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PipelineRunner:
    """Execute build plans with event handling."""

    def __init__(self, pipeline_ctx: PipelineContext):
        self.pipeline_ctx = pipeline_ctx
        self.event_handlers: Dict[RunnerEvent, list] = {event: [] for event in RunnerEvent}

    def add_handler(self, event: RunnerEvent, handler: Callable[[EventData], None]):
        """Register an event handler."""
        self.event_handlers[event].append(handler)

    def execute(self, plan: BuildPlan, ctx: BuildContext) -> StepResult:
        """Execute a build plan."""
        self._emit(RunnerEvent.PIPELINE_START, metadata={"plan": plan.pipeline_name})

        overall_success = True
        overall_message = ""

        for step in plan.steps:
            step_name = step.module_name

            # Check dry run
            if self.pipeline_ctx.dry_run and not step.module.supports_dry_run:
                self._emit(RunnerEvent.STEP_SKIP, step_name=step_name,
                          metadata={"reason": "dry_run_not_supported"})
                print(f"Skipping {step_name} (dry run not supported)")
                continue

            # Emit step start
            self._emit(RunnerEvent.STEP_START, step_name=step_name)
            print(f"Running {step_name}...")

            try:
                # Validate requirements
                if not step.module.validate_requirements(ctx):
                    raise RuntimeError(f"Module {step_name} requirements not met")

                # Execute module
                result = step.module.run(ctx, step.config)

                # Update context with artifacts and metadata
                if result.artifacts:
                    ctx.artifacts.update(result.artifacts)
                if result.metadata:
                    ctx.metadata.update(result.metadata)

                # Emit step end
                self._emit(RunnerEvent.STEP_END, step_name=step_name, result=result)

                if result.success:
                    print(f"✓ {step_name} completed")
                else:
                    print(f"✗ {step_name} failed: {result.message}")
                    overall_success = False
                    overall_message = f"Step {step_name} failed: {result.message}"

                    # Stop on failure
                    if not self.pipeline_ctx.dry_run:
                        break

            except Exception as e:
                self._emit(RunnerEvent.STEP_ERROR, step_name=step_name, error=e)
                print(f"✗ {step_name} error: {str(e)}")
                overall_success = False
                overall_message = f"Step {step_name} error: {str(e)}"

                # Stop on error
                if not self.pipeline_ctx.dry_run:
                    break

        self._emit(RunnerEvent.PIPELINE_END, metadata={
            "success": overall_success,
            "message": overall_message
        })

        return StepResult(
            success=overall_success,
            message=overall_message or "Pipeline completed"
        )

    def _emit(self, event: RunnerEvent, **kwargs):
        """Emit an event to all registered handlers."""
        event_data = EventData(event=event, **kwargs)

        for handler in self.event_handlers[event]:
            try:
                handler(event_data)
            except Exception as e:
                print(f"Error in event handler: {e}")


class SlackNotifier:
    """Slack notification handler for pipeline events."""

    def __init__(self, slack_client: Any):
        self.slack_client = slack_client
        self.channel = "#builds"

    def on_pipeline_start(self, data: EventData):
        """Handle pipeline start event."""
        if self.slack_client:
            self.slack_client.send_message(
                self.channel,
                f"🚀 Pipeline '{data.metadata.get('plan', 'unknown')}' started"
            )

    def on_pipeline_end(self, data: EventData):
        """Handle pipeline end event."""
        if self.slack_client:
            success = data.metadata.get("success", False)
            icon = "✅" if success else "❌"
            status = "completed" if success else "failed"
            message = data.metadata.get("message", "")

            self.slack_client.send_message(
                self.channel,
                f"{icon} Pipeline {status}: {message}"
            )

    def on_step_error(self, data: EventData):
        """Handle step error event."""
        if self.slack_client:
            self.slack_client.send_message(
                self.channel,
                f"⚠️ Step '{data.step_name}' error: {str(data.error)}"
            )