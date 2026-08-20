"""Build a resolved Workflow without mutating its source Recipe or LabState."""

from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from nautolab.core import ActionType, InvalidRecipeError, LocationMismatchError, Recipe, WorkflowStatus
from nautolab.resources import LabState, ResourceResolver

from .events import EventBus, ResourceResolved
from .model import Workflow, WorkflowStep


def build_workflow(recipe: Recipe, lab: LabState, events: EventBus | None = None) -> Workflow:
    if not recipe.steps or not any(step.enabled for step in recipe.steps):
        raise InvalidRecipeError("recipe must contain at least one enabled step")
    original = deepcopy(recipe.to_dict())
    resolver = ResourceResolver(lab)
    occupancy = {slot.id: slot.occupancy for slot in lab.slots.list_all()}
    locations = {sample.id: sample.current_location for sample in lab.samples.list_all()}
    workflow_id = f"workflow_{uuid4().hex[:12]}"
    resolved: list[WorkflowStep] = []
    for recipe_step in recipe.steps:
        if not recipe_step.enabled:
            continue
        action = recipe_step.action
        destination_id = None
        if action.action_type is ActionType.MOVE_SAMPLE:
            assert action.sample_id and action.destination
            if not lab.samples.contains(action.sample_id):
                raise InvalidRecipeError(f"sample {action.sample_id!r} is not registered")
            current_source = locations[action.sample_id]
            if current_source is None:
                raise LocationMismatchError(
                    f"sample {action.sample_id!r} has no current resolved location"
                )
            if action.source_slot_id is not None and action.source_slot_id != current_source:
                raise LocationMismatchError(
                    f"SOURCE_MISMATCH: sample {action.sample_id!r} expected at "
                    f"{action.source_slot_id!r}, found {current_source!r}"
                )
            occupancy[current_source] -= 1
            try:
                destination = resolver.resolve(action.destination, occupancy=occupancy)
            except Exception:
                occupancy[current_source] += 1
                raise
            if destination.id == current_source:
                occupancy[current_source] += 1
                raise InvalidRecipeError(
                    f"MOVE_SAMPLE source and resolved destination must differ: {current_source}"
                )
            destination_id = destination.id
            occupancy[destination_id] = occupancy.get(destination_id, destination.occupancy) + 1
            locations[action.sample_id] = destination_id
            if events:
                events.publish(ResourceResolved(workflow_id, recipe_step.step_id, f"{action.destination.allocation_mode.value} → {destination_id}"))
        elif action.action_type is not ActionType.WAIT:
            raise InvalidRecipeError(f"action {action.action_type.value} has no Phase 1 simulation implementation")
        duration = float(action.parameters.get("duration_seconds", 0.0))
        resolved.append(WorkflowStep(
            step_id=f"{workflow_id}_step_{len(resolved) + 1:03d}",
            recipe_step_id=recipe_step.step_id,
            action_type=action.action_type,
            sample_id=action.sample_id,
            source_slot_id=current_source if action.action_type is ActionType.MOVE_SAMPLE else None,
            destination_slot_id=destination_id,
            duration_seconds=duration,
        ))
    if recipe.to_dict() != original:
        raise RuntimeError("workflow resolution mutated the canonical recipe")
    workflow = Workflow(workflow_id, recipe.id, recipe.name, resolved)
    workflow.transition(WorkflowStatus.VALIDATED)
    return workflow
