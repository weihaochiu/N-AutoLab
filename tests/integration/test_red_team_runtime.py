from __future__ import annotations

from pathlib import Path

import pytest

from nautolab.application.services import RecipeService
from nautolab.core import (
    Action, ActionType, MoveDestination, Recipe, RecipeStep, Sample,
    Station, StationSlot, WorkflowStatus, WorkflowStepStatus,
)
from nautolab.resources import LabState, load_lab_config
from nautolab.safety import PreflightService
from nautolab.simulation import SimulationTransporter
from nautolab.workflow import EventBus, WorkflowExecutor, build_workflow
from nautolab.workflow.events import Event


ROOT = Path(__file__).resolve().parents[2]


def _ready_golden():
    lab = load_lab_config(ROOT / "config" / "demo_lab.yaml")
    events = EventBus()
    workflow = PreflightService(lab, events).check(RecipeService.golden_path_recipe()).workflow
    assert workflow
    workflow.transition(WorkflowStatus.READY)
    return lab, events, workflow


def test_two_samples_cannot_resolve_same_capacity_one_slot() -> None:
    lab = LabState()
    for station in (Station("storage_01", "Storage", "storage"), Station("hotplate_01", "HP", "hotplate")):
        lab.stations.add(station)
    for index in (1, 2):
        lab.slots.add(StationSlot(f"storage_01.slot_{index:02d}", f"ST{index}", "storage_01", index))
        sample = Sample(f"sample_{index:03d}", f"Sample {index}")
        lab.samples.add(sample); lab.place_sample(sample.id, f"storage_01.slot_{index:02d}")
    lab.slots.add(StationSlot("hotplate_01.slot_01", "HP1", "hotplate_01", 1))
    recipe = Recipe("conflict", "Conflict", tuple(RecipeStep(f"step_{index}", index, Action(
        f"move_{index}", ActionType.MOVE_SAMPLE, f"sample_{index:03d}", f"storage_01.slot_{index:02d}",
        MoveDestination(exact_slot_id="hotplate_01.slot_01"),
    )) for index in (1, 2)))
    with pytest.raises(Exception, match="full"):
        build_workflow(recipe, lab)
    assert lab.slots.get("hotplate_01.slot_01").occupancy == 0


def test_station_disabled_after_resolution_fails_and_stops_future_steps() -> None:
    lab, events, workflow = _ready_golden()
    lab.stations.get("hotplate_01").enabled = False
    WorkflowExecutor(SimulationTransporter(lab, events), events).run(workflow)
    assert workflow.status is WorkflowStatus.FAILED
    assert workflow.steps[0].status is WorkflowStepStatus.FAILED
    assert all(step.status is WorkflowStepStatus.PENDING for step in workflow.steps[1:])
    assert lab.samples.get("sample_001").current_location == "storage_01.slot_01"


def test_destination_slot_disappears_after_resolution_fails_closed() -> None:
    lab, events, workflow = _ready_golden()
    lab.slots.remove("hotplate_01.slot_03")
    WorkflowExecutor(SimulationTransporter(lab, events), events).run(workflow)
    assert workflow.status is WorkflowStatus.FAILED
    assert "not registered" in (workflow.error or "")


def test_sample_disappears_after_resolution_fails_closed() -> None:
    lab, events, workflow = _ready_golden()
    lab.remove_sample("sample_001"); lab.remove_sample_resource("sample_001")
    WorkflowExecutor(SimulationTransporter(lab, events), events).run(workflow)
    assert workflow.status is WorkflowStatus.FAILED
    assert "not registered" in (workflow.error or "")


def test_pause_requested_after_first_move_takes_effect_at_next_boundary() -> None:
    lab, events, workflow = _ready_golden()
    base = SimulationTransporter(lab, events); executor = WorkflowExecutor(base, events)
    original = base.move_sample; calls = 0
    def move(*args, **kwargs):
        nonlocal calls
        original(*args, **kwargs); calls += 1
        if calls == 1: executor.request_pause(workflow)
    base.move_sample = move
    executor.run(workflow)
    assert workflow.status is WorkflowStatus.PAUSED
    assert workflow.steps[0].status is WorkflowStepStatus.COMPLETED
    assert workflow.steps[1].status is WorkflowStepStatus.PENDING
    executor.resume(workflow)
    assert workflow.status is WorkflowStatus.COMPLETED


def test_intermediate_station_disabled_after_pause_fails_on_resume() -> None:
    lab, events, workflow = _ready_golden()
    base = SimulationTransporter(lab, events); executor = WorkflowExecutor(base, events)
    original = base.move_sample; calls = 0
    def move(*args, **kwargs):
        nonlocal calls
        original(*args, **kwargs); calls += 1
        if calls == 1: executor.request_pause(workflow)
    base.move_sample = move
    executor.run(workflow)
    assert workflow.status is WorkflowStatus.PAUSED
    current = lab.samples.get("sample_001").current_location; assert current
    lab.stations.get(lab.slots.get(current).parent_station_id).enabled = False
    executor.resume(workflow)
    assert workflow.status is WorkflowStatus.FAILED
    assert "source station" in (workflow.error or "")


def test_duplicate_observer_event_cannot_change_business_state() -> None:
    lab = load_lab_config(ROOT / "config" / "demo_lab.yaml")
    before = lab.samples.get("sample_001").current_location
    bus = EventBus(); event = Event(message="duplicate")
    bus.publish(event); bus.publish(event)
    assert len(bus.events) == 2
    assert lab.samples.get("sample_001").current_location == before
