"""Resolved execution-plan models, independent of Recipe and GUI rows."""

from __future__ import annotations

from dataclasses import dataclass, field

from nautolab.core import (
    ActionType, InvalidWorkflowTransitionError, WorkflowStatus, WorkflowStepStatus,
)


@dataclass(slots=True)
class WorkflowStep:
    step_id: str
    recipe_step_id: str
    action_type: ActionType
    sample_id: str | None = None
    source_slot_id: str | None = None
    destination_slot_id: str | None = None
    duration_seconds: float = 0.0
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    error: str | None = None


@dataclass(slots=True)
class Workflow:
    workflow_id: str
    recipe_id: str
    recipe_name: str
    steps: list[WorkflowStep]
    status: WorkflowStatus = WorkflowStatus.CREATED
    error: str | None = None

    _allowed: dict[WorkflowStatus, frozenset[WorkflowStatus]] = field(
        default_factory=lambda: {
            WorkflowStatus.CREATED: frozenset({WorkflowStatus.VALIDATED}),
            WorkflowStatus.VALIDATED: frozenset({WorkflowStatus.READY}),
            WorkflowStatus.READY: frozenset({WorkflowStatus.RUNNING, WorkflowStatus.ABORTED}),
            WorkflowStatus.RUNNING: frozenset({WorkflowStatus.PAUSED, WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.ABORTED}),
            WorkflowStatus.PAUSED: frozenset({WorkflowStatus.RUNNING, WorkflowStatus.ABORTED}),
        }, init=False, repr=False
    )

    def transition(self, target: WorkflowStatus) -> None:
        target = WorkflowStatus(target)
        if target not in self._allowed.get(self.status, frozenset()):
            raise InvalidWorkflowTransitionError(
                f"workflow cannot transition from {self.status.value} to {target.value}"
            )
        self.status = target

    @property
    def progress(self) -> float:
        if not self.steps:
            return 0.0
        completed = sum(step.status is WorkflowStepStatus.COMPLETED for step in self.steps)
        return completed / len(self.steps)
