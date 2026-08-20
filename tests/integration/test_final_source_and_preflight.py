from __future__ import annotations

from pathlib import Path

import pytest

from nautolab.application.services import RecipeService
from nautolab.core import (
    Action, ActionType, LocationMismatchError, MoveDestination, Recipe, RecipeStep,
    Sample, Station, StationSlot,
)
from nautolab.resources import LabState, load_lab_config
from nautolab.safety import PreflightService
from nautolab.workflow import build_workflow


ROOT = Path(__file__).resolve().parents[2]


def _move(step_id: str, sample_id: str, destination: MoveDestination, source: str | None = None) -> RecipeStep:
    return RecipeStep(step_id, int(step_id.rsplit("_", 1)[-1]), Action(
        f"action_{step_id}", ActionType.MOVE_SAMPLE, sample_id, source, destination,
    ))


def test_forced_hotplate_02_allocation_chains_actual_source() -> None:
    lab = LabState()
    for station_id, station_type, count in (
        ("storage_01", "storage", 4), ("hotplate_01", "hotplate", 3),
        ("hotplate_02", "hotplate", 2), ("spin_coater_01", "spin_coater", 1),
    ):
        lab.stations.add(Station(station_id, station_id, station_type))
        for index in range(1, count + 1):
            lab.slots.add(StationSlot(f"{station_id}.slot_{index:02d}", f"S{index}", station_id, index))
    for index in range(1, 4):
        blocker = Sample(f"blocker_{index}", f"Blocker {index}")
        lab.samples.add(blocker); lab.place_sample(blocker.id, f"hotplate_01.slot_{index:02d}")
    sample = Sample("sample_001", "Target"); lab.samples.add(sample); lab.place_sample(sample.id, "storage_01.slot_01")
    recipe = Recipe("dynamic", "Dynamic", (
        _move("step_1", "sample_001", MoveDestination(station_type="hotplate")),
        _move("step_2", "sample_001", MoveDestination(station_type="spin_coater")),
    ))
    workflow = build_workflow(recipe, lab)
    assert workflow.steps[0].destination_slot_id == "hotplate_02.slot_01"
    assert workflow.steps[1].source_slot_id == "hotplate_02.slot_01"
    assert all(step.action.source_slot_id is None for step in recipe.steps)


def test_explicit_source_remains_an_assertion() -> None:
    lab = load_lab_config(ROOT / "config" / "demo_lab.yaml")
    recipe = Recipe("mismatch", "Mismatch", (
        _move("step_1", "sample_001", MoveDestination(station_type="hotplate"), "storage_01.slot_02"),
    ))
    with pytest.raises(LocationMismatchError, match="SOURCE_MISMATCH"):
        build_workflow(recipe, lab)


def test_auto_source_cannot_resolve_back_to_same_exact_slot() -> None:
    lab = load_lab_config(ROOT / "config" / "demo_lab.yaml")
    recipe = Recipe("same", "Same", (
        _move("step_1", "sample_001", MoveDestination(exact_slot_id="storage_01.slot_01")),
    ))
    report = PreflightService(lab).check(recipe)
    assert not report.passed
    assert any(issue.code == "DESTINATION_EQUALS_SOURCE" for issue in report.issues)


def test_three_samples_keep_independent_auto_locations_when_interleaved() -> None:
    lab = LabState()
    for station_id, station_type in (("storage_01", "storage"), ("hotplate_01", "hotplate")):
        lab.stations.add(Station(station_id, station_id, station_type))
        for index in range(1, 4):
            lab.slots.add(StationSlot(f"{station_id}.slot_{index:02d}", f"S{index}", station_id, index))
    for index in range(1, 4):
        sample = Sample(f"sample_{index:03d}", f"Sample {index}")
        lab.samples.add(sample); lab.place_sample(sample.id, f"storage_01.slot_{index:02d}")
    steps = []
    order = 1
    for index in range(1, 4):
        steps.append(_move(f"step_{order}", f"sample_{index:03d}", MoveDestination(station_type="hotplate"))); order += 1
    for index in range(1, 4):
        steps.append(_move(f"step_{order}", f"sample_{index:03d}", MoveDestination(exact_slot_id=f"storage_01.slot_{index:02d}"))); order += 1
    workflow = build_workflow(Recipe("interleaved", "Interleaved", steps), lab)
    assert [step.source_slot_id for step in workflow.steps[3:]] == [
        "hotplate_01.slot_01", "hotplate_01.slot_02", "hotplate_01.slot_03",
    ]


def test_preflight_scopes_unlocated_readiness_to_relevant_samples() -> None:
    lab = load_lab_config(ROOT / "config" / "demo_lab.yaml")
    lab.samples.add(Sample("sample_unused", "Unused"))
    assert PreflightService(lab).check(RecipeService.golden_path_recipe()).passed

    used = Recipe("used", "Used", (
        _move("step_1", "sample_unused", MoveDestination(station_type="hotplate")),
    ))
    report = PreflightService(lab).check(used)
    assert not report.passed
    assert any(issue.code == "RELEVANT_SAMPLE_UNLOCATED" for issue in report.issues)


def test_unused_canonical_contradiction_still_blocks() -> None:
    lab = load_lab_config(ROOT / "config" / "demo_lab.yaml")
    unused = Sample("sample_unused", "Unused")
    lab.samples.add(unused)
    unused._restore_location_state("hotplate_01.slot_03", unused.history)
    report = PreflightService(lab).check(RecipeService.golden_path_recipe())
    assert not report.passed
    assert any(issue.code == "GLOBAL_LOCATION_MISMATCH" for issue in report.issues)
