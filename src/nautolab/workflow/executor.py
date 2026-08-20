"""Boundary-pausing, fail-closed simulation workflow executor."""

from __future__ import annotations

from threading import Event
from typing import TYPE_CHECKING

from nautolab.core import (
    ActionType, InvalidWorkflowTransitionError, SimulationAbortRequested,
    WorkflowStatus, WorkflowStepStatus,
)
if TYPE_CHECKING:
    from nautolab.simulation import SimulationTransporter

from .events import (
    EventBus, StepCompleted, StepFailed, StepStarted,
    WorkflowAborted, WorkflowCompleted, WorkflowFailed, WorkflowPauseRequested,
    WorkflowPaused, WorkflowResumed, WorkflowStarted,
)
from .model import Workflow


class WorkflowExecutor:
    def __init__(self, transporter: "SimulationTransporter", events: EventBus) -> None:
        self._transporter = transporter
        self._events = events
        self._pause_requested = Event()
        self._abort_requested = Event()

    @property
    def pause_pending(self) -> bool:
        return self._pause_requested.is_set()

    def request_pause(self, workflow: Workflow) -> None:
        if workflow.status not in {WorkflowStatus.READY, WorkflowStatus.RUNNING}:
            raise InvalidWorkflowTransitionError("pause is available only before or during a run")
        self._pause_requested.set()
        self._events.publish(WorkflowPauseRequested(
            workflow.workflow_id, message="Pause requested; waiting for safe step boundary"
        ))

    def request_abort(self, workflow: Workflow) -> None:
        if workflow.status not in {WorkflowStatus.READY, WorkflowStatus.RUNNING, WorkflowStatus.PAUSED}:
            raise InvalidWorkflowTransitionError("abort is unavailable in the current state")
        if workflow.status in {WorkflowStatus.READY, WorkflowStatus.PAUSED}:
            self._abort(workflow)
        else:
            self._abort_requested.set()

    def resume(self, workflow: Workflow) -> Workflow:
        if workflow.status is not WorkflowStatus.PAUSED:
            raise InvalidWorkflowTransitionError("resume requires a PAUSED workflow")
        self._pause_requested.clear()
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
            if self._abort_requested.is_set():
                self._abort(workflow)
                return workflow
            if self._pause_requested.is_set():
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
                        abort_requested=self._abort_requested.is_set,
                    )
                elif step.action_type is ActionType.WAIT:
                    self._transporter.wait(step.duration_seconds, self._abort_requested.is_set)
                else:
                    raise RuntimeError(f"unsupported action {step.action_type.value}")
                step.status = WorkflowStepStatus.COMPLETED
                self._events.publish(StepCompleted(workflow.workflow_id, step.step_id, "Step completed"))
                if self._abort_requested.is_set():
                    self._abort(workflow)
                    return workflow
            except SimulationAbortRequested:
                self._abort(workflow)
                return workflow
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
            if step.status in {WorkflowStepStatus.PENDING, WorkflowStepStatus.RUNNING}:
                step.status = WorkflowStepStatus.ABORTED
        self._events.publish(WorkflowAborted(workflow.workflow_id, message="Workflow aborted at step boundary"))
