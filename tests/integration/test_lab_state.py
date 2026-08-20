"""Integration tests for canonical slot-level state and resource queries."""

import pytest

from nautolab.core import (
    LocationMismatchError,
    Sample,
    SampleHistoryEventType,
    SlotDisabledError,
    Station,
    StationDisabledError,
    StationOccupiedError,
    StationSlot,
)
from nautolab.resources import LabState


def add_station(state: LabState, station_id: str, station_type: str, slots: int = 3) -> None:
    state.stations.add(
        Station(id=station_id, display_name=station_id, station_type=station_type)
    )
    for index in range(1, slots + 1):
        state.slots.add(
            StationSlot(
                id=f"{station_id}.slot_{index:02d}",
                display_name=f"{station_id}-S{index:02d}",
                parent_station_id=station_id,
                slot_index=index,
                pose_reference=f"{station_id}_slot_{index:02d}",
            )
        )


def make_state() -> LabState:
    state = LabState()
    add_station(state, "storage_01", "storage", 4)
    add_station(state, "hotplate_01", "hotplate")
    add_station(state, "hotplate_02", "hotplate")
    state.samples.add(Sample(id="sample_001", name="Sample 001"))
    state.place_sample("sample_001", "storage_01.slot_01")
    return state


def add_sample(state: LabState, sample_id: str) -> None:
    state.samples.add(Sample(id=sample_id, name=sample_id))


def test_initial_placement_updates_sample_and_exact_slot() -> None:
    state = make_state()
    sample = state.samples.get("sample_001")
    assert sample.current_location == "storage_01.slot_01"
    assert state.slots.get("storage_01.slot_01").occupant_ids == ("sample_001",)
    assert sample.history[-1].event_type is SampleHistoryEventType.PLACED


def test_exact_slot_move_does_not_affect_other_same_type_station() -> None:
    state = make_state()
    state.relocate_sample(
        "sample_001", "storage_01.slot_01", "hotplate_02.slot_03"
    )
    assert state.samples.get("sample_001").current_location == "hotplate_02.slot_03"
    assert state.slots.get("storage_01.slot_01").occupant_ids == ()
    assert state.slots.get("hotplate_02.slot_03").occupant_ids == ("sample_001",)
    assert state.station_occupancy("hotplate_01") == 0


def test_multiple_samples_occupy_distinct_slots_on_one_hotplate() -> None:
    state = make_state()
    state.relocate_sample(
        "sample_001", "storage_01.slot_01", "hotplate_01.slot_01"
    )
    for number in (2, 3):
        sample_id = f"sample_{number:03d}"
        add_sample(state, sample_id)
        state.place_sample(sample_id, f"hotplate_01.slot_{number:02d}")
    assert state.station_occupancy("hotplate_01") == 3
    assert state.station_total_capacity("hotplate_01") == 3
    assert state.station_available_capacity("hotplate_01") == 0
    assert state.station_occupant_ids("hotplate_01") == (
        "sample_001",
        "sample_002",
        "sample_003",
    )


def test_same_slot_collision_has_no_partial_mutation() -> None:
    state = make_state()
    add_sample(state, "sample_002")
    state.place_sample("sample_002", "hotplate_01.slot_01")
    before_history = state.samples.get("sample_001").history
    with pytest.raises(StationOccupiedError):
        state.relocate_sample(
            "sample_001", "storage_01.slot_01", "hotplate_01.slot_01"
        )
    assert state.samples.get("sample_001").current_location == "storage_01.slot_01"
    assert state.slots.get("storage_01.slot_01").occupant_ids == ("sample_001",)
    assert state.slots.get("hotplate_01.slot_01").occupant_ids == ("sample_002",)
    assert state.samples.get("sample_001").history == before_history


def test_source_slot_mismatch_is_rejected_without_mutation() -> None:
    state = make_state()
    with pytest.raises(LocationMismatchError):
        state.relocate_sample(
            "sample_001", "hotplate_01.slot_01", "hotplate_02.slot_01"
        )
    assert state.samples.get("sample_001").current_location == "storage_01.slot_01"


def test_disabled_slot_rejects_new_sample() -> None:
    state = make_state()
    state.slots.get("hotplate_02.slot_02").enabled = False
    with pytest.raises(SlotDisabledError):
        state.relocate_sample(
            "sample_001", "storage_01.slot_01", "hotplate_02.slot_02"
        )
    assert state.samples.get("sample_001").current_location == "storage_01.slot_01"
    assert "hotplate_02.slot_02" not in {
        slot.id for slot in state.available_slots_for_station("hotplate_02")
    }


def test_disabled_parent_station_rejects_enabled_slot() -> None:
    state = make_state()
    state.stations.get("hotplate_02").enabled = False
    assert state.slots.get("hotplate_02.slot_03").enabled is True
    with pytest.raises(StationDisabledError):
        state.relocate_sample(
            "sample_001", "storage_01.slot_01", "hotplate_02.slot_03"
        )
    assert state.available_slots_for_station("hotplate_02") == ()


def test_available_slots_for_station_are_slot_index_ordered() -> None:
    state = make_state()
    add_sample(state, "sample_002")
    add_sample(state, "sample_003")
    state.place_sample("sample_002", "hotplate_01.slot_01")
    state.place_sample("sample_003", "hotplate_01.slot_02")
    assert [slot.id for slot in state.available_slots_for_station("hotplate_01")] == [
        "hotplate_01.slot_03"
    ]


def test_available_slots_for_type_span_stations_deterministically() -> None:
    state = make_state()
    for number, slot_id in enumerate(
        (
            "hotplate_01.slot_01",
            "hotplate_01.slot_02",
            "hotplate_01.slot_03",
            "hotplate_02.slot_01",
        ),
        start=2,
    ):
        sample_id = f"sample_{number:03d}"
        add_sample(state, sample_id)
        state.place_sample(sample_id, slot_id)
    assert [
        slot.id for slot in state.available_slots_for_station_type("hotplate")
    ] == ["hotplate_02.slot_02", "hotplate_02.slot_03"]


def test_slot_capacity_greater_than_one_accepts_two_and_rejects_third() -> None:
    state = LabState()
    add_station(state, "batch_holder_01", "batch_holder", slots=0)
    state.slots.add(
        StationSlot(
            id="batch_holder_01.slot_01",
            display_name="Batch Holder",
            parent_station_id="batch_holder_01",
            slot_index=1,
            capacity=2,
        )
    )
    for number in (1, 2, 3):
        add_sample(state, f"sample_{number:03d}")
    state.place_sample("sample_001", "batch_holder_01.slot_01")
    state.place_sample("sample_002", "batch_holder_01.slot_01")
    with pytest.raises(StationOccupiedError):
        state.place_sample("sample_003", "batch_holder_01.slot_01")
    assert state.slots.get("batch_holder_01.slot_01").occupant_ids == (
        "sample_001",
        "sample_002",
    )
    assert state.samples.get("sample_003").current_location is None


def test_remove_sample_updates_only_exact_slot_and_history() -> None:
    state = make_state()
    state.remove_sample("sample_001")
    assert state.samples.get("sample_001").current_location is None
    assert state.slots.get("storage_01.slot_01").occupant_ids == ()
    assert state.samples.get("sample_001").history[-1].event_type is SampleHistoryEventType.REMOVED


def test_invalid_metadata_cannot_cause_partial_mutation() -> None:
    state = make_state()
    with pytest.raises((TypeError, ValueError)):
        state.relocate_sample(
            "sample_001",
            "storage_01.slot_01",
            "hotplate_01.slot_01",
            metadata="not_a_mapping",  # type: ignore[arg-type]
        )
    assert state.samples.get("sample_001").current_location == "storage_01.slot_01"
    assert state.slots.get("storage_01.slot_01").occupant_ids == ("sample_001",)
