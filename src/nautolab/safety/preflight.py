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

        relevant_sample_ids = {
            step.action.sample_id
            for step in recipe.steps
            if step.enabled and step.action.sample_id is not None
        }
        issues.extend(self._check_canonical_state(relevant_sample_ids))

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

    def _check_canonical_state(self, relevant_sample_ids: set[str]) -> list[PreflightIssue]:
        """Allow unused/unlocated resources but reject every canonical contradiction."""
        issues: list[PreflightIssue] = []
        for sample in self._lab.samples.list_all():
            if sample.current_location is None:
                if sample.id in relevant_sample_ids:
                    issues.append(PreflightIssue(
                        "RELEVANT_SAMPLE_UNLOCATED",
                        f"workflow sample {sample.id} has no current location",
                    ))
                continue
            try:
                slot = self._lab.slots.get(sample.current_location)
            except ResourceNotFoundError as exc:
                issues.append(PreflightIssue("GLOBAL_LOCATION_INVALID", f"{sample.id}: {exc}"))
                continue
            if not slot.contains_sample(sample.id):
                issues.append(PreflightIssue(
                    "GLOBAL_LOCATION_MISMATCH",
                    f"{sample.id} location and slot occupancy disagree",
                ))
        for slot in self._lab.slots.list_all():
            for occupant_id in slot.occupant_ids:
                try:
                    occupant = self._lab.samples.get(occupant_id)
                except ResourceNotFoundError:
                    issues.append(PreflightIssue(
                        "GLOBAL_OCCUPANT_UNKNOWN",
                        f"slot {slot.id} contains unregistered sample {occupant_id}",
                    ))
                    continue
                if occupant.current_location != slot.id:
                    issues.append(PreflightIssue(
                        "GLOBAL_OCCUPANCY_MISMATCH",
                        f"slot {slot.id} contains {occupant_id}, whose location is "
                        f"{occupant.current_location}",
                    ))
        return issues

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
            assert action.sample_id and action.destination
            sample_exists = self._lab.samples.contains(action.sample_id)
            if not sample_exists:
                issues.append(PreflightIssue("SAMPLE_MISSING", f"{action.sample_id} not found"))
            current_source = locations.get(action.sample_id)
            if (
                action.source_slot_id is not None
                and action.source_slot_id != current_source
            ):
                issues.append(PreflightIssue(
                    "SOURCE_MISMATCH",
                    f"{action.sample_id} explicit source {action.source_slot_id} "
                    f"does not match current resolved location {current_source}",
                ))
            source_exists = current_source is not None and self._lab.slots.contains(current_source)
            if sample_exists and current_source is not None and not source_exists:
                issues.append(PreflightIssue("SOURCE_MISSING", f"source slot {current_source} not found"))
            source_released = False
            if sample_exists and source_exists:
                if occupancy[current_source] <= 0:
                    issues.append(PreflightIssue(
                        "SOURCE_MISMATCH",
                        f"{action.sample_id} source {current_source} has no matching occupancy",
                    ))
                else:
                    occupancy[current_source] -= 1
                    source_released = True
            try:
                destination = resolver.resolve(action.destination, occupancy=occupancy)
            except ResourceResolutionError as exc:
                issues.append(PreflightIssue("DESTINATION_UNAVAILABLE", f"{step.step_id}: {exc}"))
                if source_released:
                    occupancy[current_source] += 1
            else:
                if source_released:
                    if destination.id == current_source:
                        issues.append(PreflightIssue(
                            "DESTINATION_EQUALS_SOURCE",
                            f"{step.step_id}: source and resolved destination are both {current_source}",
                        ))
                        occupancy[current_source] += 1
                    else:
                        occupancy[destination.id] = occupancy.get(destination.id, destination.occupancy) + 1
                        locations[action.sample_id] = destination.id
        return issues
