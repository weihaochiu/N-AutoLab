from __future__ import annotations

from pathlib import Path

from nautolab.core import (
    Action, ActionType, AllocationMode, ExecutionMode, MoveDestination,
    Recipe, RecipeStep, Sample, Station, StationSlot, WorkflowStatus,
)
from nautolab.resources import LabState, load_lab_config
from nautolab.safety import PreflightService
from nautolab.simulation import SimulationTransporter
from nautolab.workflow import EventBus, WorkflowExecutor


ROOT = Path(__file__).resolve().parents[2]


def _golden_recipe() -> Recipe:
    moves = [
        ("storage_01.slot_01", MoveDestination(station_type="hotplate")),
        ("hotplate_01.slot_03", MoveDestination(station_type="spin_coater")),
        ("spin_coater_01.slot_01", MoveDestination(station_type="hotplate")),
        ("hotplate_01.slot_03", MoveDestination(exact_slot_id="storage_01.slot_01")),
    ]
    return Recipe("golden_recipe", "Golden Path", [
        RecipeStep(
            f"move_{index}", index,
            Action(f"action_{index}", ActionType.MOVE_SAMPLE, "sample_001", source, destination,
                   parameters={"duration_seconds": 120}),
        ) for index, (source, destination) in enumerate(moves, 1)
    ])


def test_golden_path_resolves_and_executes_without_real_wait() -> None:
    lab = load_lab_config(ROOT / "config" / "demo_lab.yaml")
    recipe = _golden_recipe(); before = recipe.to_dict(); events = EventBus()
    report = PreflightService(lab, events).check(recipe, ExecutionMode.SIMULATION)
    assert report.passed and report.workflow
    assert recipe.to_dict() == before
    destinations = [step.destination_slot_id for step in report.workflow.steps]
    assert destinations == [
        "hotplate_01.slot_03", "spin_coater_01.slot_01",
        "hotplate_01.slot_03", "storage_01.slot_01",
    ]
    report.workflow.transition(WorkflowStatus.READY)
    executor = WorkflowExecutor(SimulationTransporter(lab, events), events)
    executor.run(report.workflow)
    assert report.workflow.status is WorkflowStatus.COMPLETED
    sample = lab.samples.get("sample_001")
    assert sample.current_location == "storage_01.slot_01"
    assert [entry.destination for entry in sample.history][-4:] == destinations
    assert lab.slots.get("hotplate_01.slot_03").occupancy == 0
    assert any(event.category == "SIMULATION" for event in events.events)


def test_pause_resume_abort_and_runtime_failure() -> None:
    lab = load_lab_config(ROOT / "config" / "demo_lab.yaml")
    events = EventBus(); report = PreflightService(lab, events).check(_golden_recipe())
    workflow = report.workflow; assert workflow
    workflow.transition(WorkflowStatus.READY)
    executor = WorkflowExecutor(SimulationTransporter(lab, events), events)
    executor.request_pause(workflow); executor.run(workflow)
    assert workflow.status is WorkflowStatus.PAUSED
    executor.resume(workflow); assert workflow.status is WorkflowStatus.COMPLETED

    lab2 = load_lab_config(ROOT / "config" / "demo_lab.yaml")
    report2 = PreflightService(lab2).check(_golden_recipe()); workflow2 = report2.workflow; assert workflow2
    workflow2.transition(WorkflowStatus.READY)
    executor2 = WorkflowExecutor(SimulationTransporter(lab2, EventBus()), EventBus())
    executor2.request_abort(workflow2)
    assert workflow2.status is WorkflowStatus.ABORTED


def test_three_samples_fill_three_slots_of_one_hotplate() -> None:
    lab = LabState()
    for station in (Station("storage_01", "Storage", "storage"), Station("hotplate_01", "Hot Plate", "hotplate")):
        lab.stations.add(station)
        for index in range(1, 4):
            lab.slots.add(StationSlot(f"{station.id}.slot_{index:02d}", f"S{index}", station.id, index))
    for index in range(1, 4):
        sample_id = f"sample_{index:03d}"; source = f"storage_01.slot_{index:02d}"
        lab.samples.add(Sample(sample_id, f"Sample {index}")); lab.place_sample(sample_id, source)
        recipe = Recipe(f"recipe_{index}", f"Move {index}", [RecipeStep(
            f"step_{index}", 1, Action(f"action_{index}", ActionType.MOVE_SAMPLE,
            sample_id, source, MoveDestination(station_type="hotplate"))
        )])
        events = EventBus(); workflow = PreflightService(lab, events).check(recipe).workflow; assert workflow
        workflow.transition(WorkflowStatus.READY)
        WorkflowExecutor(SimulationTransporter(lab, events), events).run(workflow)
    assert lab.station_occupant_ids("hotplate_01") == ("sample_001", "sample_002", "sample_003")


def test_real_mode_is_forbidden_and_failures_aggregate() -> None:
    lab = LabState()
    recipe = Recipe("empty", "Empty", [])
    report = PreflightService(lab).check(recipe, ExecutionMode.REAL)
    assert {issue.code for issue in report.issues} == {"REAL_FORBIDDEN", "EMPTY_RECIPE"}


def test_preflight_aggregates_missing_sample_full_type_and_disabled_station() -> None:
    lab = LabState()
    lab.stations.add(Station("storage_01", "Storage", "storage"))
    lab.slots.add(StationSlot("storage_01.slot_01", "ST1", "storage_01", 1))
    lab.stations.add(Station("hotplate_01", "HP", "hotplate"))
    lab.slots.add(StationSlot("hotplate_01.slot_01", "HP1", "hotplate_01", 1))
    occupant = Sample("sample_001", "Occupant"); lab.samples.add(occupant); lab.place_sample(occupant.id, "hotplate_01.slot_01")
    lab.stations.add(Station("spin_coater_01", "SC", "spin_coater", enabled=False))
    lab.slots.add(StationSlot("spin_coater_01.slot_01", "SC1", "spin_coater_01", 1))
    recipe = Recipe("aggregate", "Aggregate", (
        RecipeStep("hotplate_step", 1, Action("move_hotplate", ActionType.MOVE_SAMPLE, "sample_missing", "storage_01.slot_01", MoveDestination(station_type="hotplate"))),
        RecipeStep("spin_step", 2, Action("move_spin", ActionType.MOVE_SAMPLE, "sample_missing", "storage_01.slot_01", MoveDestination(exact_station_id="spin_coater_01"))),
    ))
    report = PreflightService(lab).check(recipe)
    messages = "\n".join(issue.message for issue in report.issues)
    assert "sample_missing not found" in messages
    assert "hotplate" in messages and "no available slot" in messages
    assert "spin_coater_01" in messages and "disabled" in messages
