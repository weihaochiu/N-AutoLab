"""Side-effect-free, aggregate simulation preflight."""

from __future__ import annotations

from dataclasses import dataclass

from nautolab.core import (
    ActionType, ExecutionMode, Recipe, ResourceNotFoundError, ResourceResolutionError,
)
from nautolab.resources import LabState, ResourceResolver
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
                except ResourceNotFoundError as exc:
                    issues.append(PreflightIssue("LOCATION_INVALID", f"{sample.id}: {exc}"))

        issues.extend(self._check_steps(recipe))

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

    def _check_steps(self, recipe: Recipe) -> list[PreflightIssue]:
        """Collect independent and sequential resolution failures without mutation."""
        issues: list[PreflightIssue] = []
        resolver = ResourceResolver(self._lab)
        occupancy = {slot.id: slot.occupancy for slot in self._lab.slots.list_all()}
        locations = {sample.id: sample.current_location for sample in self._lab.samples.list_all()}
        for step in recipe.steps:
            if not step.enabled:
                continue
            action = step.action
            if action.action_type not in {ActionType.MOVE_SAMPLE, ActionType.WAIT}:
                issues.append(PreflightIssue("UNSUPPORTED_ACTION", f"{action.action_type.value} has no simulation implementation"))
                continue
            if action.action_type is ActionType.WAIT:
                continue
            assert action.sample_id and action.source_slot_id and action.destination
            sample_exists = self._lab.samples.contains(action.sample_id)
            if not sample_exists:
                issues.append(PreflightIssue("SAMPLE_MISSING", f"{action.sample_id} not found"))
            source_exists = self._lab.slots.contains(action.source_slot_id)
            if not source_exists:
                issues.append(PreflightIssue("SOURCE_MISSING", f"source slot {action.source_slot_id} not found"))
            source_released = False
            if sample_exists and source_exists:
                actual = locations[action.sample_id]
                if actual != action.source_slot_id or occupancy[action.source_slot_id] <= 0:
                    issues.append(PreflightIssue(
                        "SOURCE_MISMATCH",
                        f"{action.sample_id} expected at {action.source_slot_id}, found {actual}",
                    ))
                else:
                    occupancy[action.source_slot_id] -= 1
                    source_released = True
            try:
                destination = resolver.resolve(action.destination, occupancy=occupancy)
            except ResourceResolutionError as exc:
                issues.append(PreflightIssue("DESTINATION_UNAVAILABLE", f"{step.step_id}: {exc}"))
                if source_released:
                    occupancy[action.source_slot_id] += 1
            else:
                if source_released:
                    occupancy[destination.id] = occupancy.get(destination.id, destination.occupancy) + 1
                    locations[action.sample_id] = destination.id
        return issues
