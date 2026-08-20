"""Boundary-pausing, fail-closed simulation workflow executor."""

from __future__ import annotations

from nautolab.core import (
    ActionType, InvalidWorkflowTransitionError, WorkflowStatus, WorkflowStepStatus,
)
from nautolab.simulation import SimulationTransporter

from .events import (
    EventBus, StepCompleted, StepFailed, StepStarted,
    WorkflowAborted, WorkflowCompleted, WorkflowFailed, WorkflowPaused,
    WorkflowResumed, WorkflowStarted,
)
from .model import Workflow


class WorkflowExecutor:
    def __init__(self, transporter: SimulationTransporter, events: EventBus) -> None:
        self._transporter = transporter
        self._events = events
        self._pause_requested = False
        self._abort_requested = False

    def request_pause(self, workflow: Workflow) -> None:
        if workflow.status not in {WorkflowStatus.READY, WorkflowStatus.RUNNING}:
            raise InvalidWorkflowTransitionError("pause is available only before or during a run")
        self._pause_requested = True

    def request_abort(self, workflow: Workflow) -> None:
        if workflow.status not in {WorkflowStatus.READY, WorkflowStatus.RUNNING, WorkflowStatus.PAUSED}:
            raise InvalidWorkflowTransitionError("abort is unavailable in the current state")
        if workflow.status in {WorkflowStatus.READY, WorkflowStatus.PAUSED}:
            self._abort(workflow)
        else:
            self._abort_requested = True

    def resume(self, workflow: Workflow) -> Workflow:
        if workflow.status is not WorkflowStatus.PAUSED:
            raise InvalidWorkflowTransitionError("resume requires a PAUSED workflow")
        self._pause_requested = False
        self._events.publish(WorkflowResumed(workflow.workflow_id, message="Workflow resumed"))
        return self.run(workflow)

    def run(self, workflow: Workflow) -> Workflow:
        if workflow.status is WorkflowStatus.READY:
            workflow.transition(WorkflowStatus.RUNNING)
            self._events.publish(WorkflowStarted(workflow.workflow_id, message="Workflow started"))
        elif workflow.status is WorkflowStatus.PAUSED:
            workflow.transition(WorkflowStatus.RUNNING)
        elif workflow.status is not WorkflowStatus.RUNNING:
            raise InvalidWorkflowTransitionError("executor requires READY, RUNNING, or PAUSED workflow")

        for step in workflow.steps:
            if step.status is not WorkflowStepStatus.PENDING:
                continue
            if self._abort_requested:
                self._abort(workflow)
                return workflow
            if self._pause_requested:
                workflow.transition(WorkflowStatus.PAUSED)
                self._events.publish(WorkflowPaused(workflow.workflow_id, message="Workflow paused at step boundary"))
                return workflow
            step.status = WorkflowStepStatus.RUNNING
            self._events.publish(StepStarted(workflow.workflow_id, step.step_id, f"Step {step.recipe_step_id} started"))
            try:
                if step.action_type is ActionType.MOVE_SAMPLE:
                    assert step.sample_id and step.source_slot_id and step.destination_slot_id
                    self._transporter.move_sample(
                        step.sample_id, step.source_slot_id, step.destination_slot_id,
                        workflow_id=workflow.workflow_id, step_id=step.step_id,
                        simulated_duration_seconds=step.duration_seconds,
                    )
                elif step.action_type is ActionType.WAIT:
                    _virtual_duration = step.duration_seconds  # deliberately no wall-clock wait
                else:
                    raise RuntimeError(f"unsupported action {step.action_type.value}")
                step.status = WorkflowStepStatus.COMPLETED
                self._events.publish(StepCompleted(workflow.workflow_id, step.step_id, "Step completed"))
            except Exception as exc:
                step.status = WorkflowStepStatus.FAILED
                step.error = str(exc)
                workflow.error = str(exc)
                workflow.transition(WorkflowStatus.FAILED)
                self._events.publish(StepFailed(workflow.workflow_id, step.step_id, str(exc)))
                self._events.publish(WorkflowFailed(workflow.workflow_id, step.step_id, str(exc)))
                return workflow

        workflow.transition(WorkflowStatus.COMPLETED)
        self._events.publish(WorkflowCompleted(workflow.workflow_id, message="Workflow completed"))
        return workflow

    def _abort(self, workflow: Workflow) -> None:
        workflow.transition(WorkflowStatus.ABORTED)
        for step in workflow.steps:
            if step.status is WorkflowStepStatus.PENDING:
                step.status = WorkflowStepStatus.ABORTED
        self._events.publish(WorkflowAborted(workflow.workflow_id, message="Workflow aborted at step boundary"))
