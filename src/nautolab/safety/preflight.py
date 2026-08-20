"""Side-effect-free, aggregate simulation preflight."""

from __future__ import annotations

from dataclasses import dataclass

from nautolab.core import ActionType, ExecutionMode, Recipe
from nautolab.resources import LabState
from nautolab.workflow.builder import build_workflow
from nautolab.workflow.events import EventBus, PreflightFailed
from nautolab.workflow.model import Workflow


@dataclass(frozen=True, slots=True)
class PreflightIssue:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class PreflightReport:
    issues: tuple[PreflightIssue, ...]
    workflow: Workflow | None = None

    @property
    def passed(self) -> bool:
        return not self.issues and self.workflow is not None

    def format(self) -> str:
        if self.passed:
            return "Preflight PASSED"
        return "Preflight FAILED\n" + "\n".join(f"- {issue.message}" for issue in self.issues)


class PreflightService:
    def __init__(self, lab: LabState, events: EventBus | None = None) -> None:
        self._lab = lab
        self._events = events

    def check(self, recipe: Recipe, mode: ExecutionMode = ExecutionMode.SIMULATION) -> PreflightReport:
        issues: list[PreflightIssue] = []
        if ExecutionMode(mode) is ExecutionMode.REAL:
            issues.append(PreflightIssue("REAL_FORBIDDEN", "REAL execution is forbidden in Phase 1"))
        if not recipe.steps or not any(step.enabled for step in recipe.steps):
            issues.append(PreflightIssue("EMPTY_RECIPE", "recipe has no enabled steps"))

        for sample in self._lab.samples.list_all():
            if sample.current_location is None:
                issues.append(PreflightIssue("UNLOCATED_SAMPLE", f"{sample.id} has no current location"))
            else:
                try:
                    slot = self._lab.slots.get(sample.current_location)
                    if not slot.contains_sample(sample.id):
                        issues.append(PreflightIssue("LOCATION_MISMATCH", f"{sample.id} location and slot occupancy disagree"))
                except Exception as exc:
                    issues.append(PreflightIssue("LOCATION_INVALID", f"{sample.id}: {exc}"))

        for step in recipe.steps:
            if not step.enabled:
                continue
            action = step.action
            if action.action_type not in {ActionType.MOVE_SAMPLE, ActionType.WAIT}:
                issues.append(PreflightIssue("UNSUPPORTED_ACTION", f"{action.action_type.value} has no simulation implementation"))
            if action.sample_id and not self._lab.samples.contains(action.sample_id):
                issues.append(PreflightIssue("SAMPLE_MISSING", f"{action.sample_id} not found"))

        workflow = None
        if not issues:
            try:
                workflow = build_workflow(recipe, self._lab, self._events)
            except Exception as exc:
                issues.append(PreflightIssue("WORKFLOW_BUILD_FAILED", str(exc)))
        report = PreflightReport(tuple(issues), workflow)
        if issues and self._events:
            self._events.publish(PreflightFailed(message=report.format()))
        return report
