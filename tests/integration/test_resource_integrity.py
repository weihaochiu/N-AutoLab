"""Hardening tests for destructive resource mutations."""

import pytest

from nautolab.core import (
    ResourceInUseError,
    Sample,
    Station,
    StationOccupiedError,
    StationSlot,
)
from nautolab.resources import LabState


def make_state() -> LabState:
    state = LabState()
    state.stations.add(
        Station(id="storage_01", display_name="Storage", station_type="storage")
    )
    state.slots.add(
        StationSlot(
            id="storage_01.slot_01",
            display_name="ST01-S01",
            parent_station_id="storage_01",
            slot_index=1,
        )
    )
    return state


def test_placed_sample_cannot_be_removed_through_registry_or_lab_state() -> None:
    state = make_state()
    sample = Sample(id="sample_001", name="Sample")
    state.samples.add(sample)
    state.place_sample(sample.id, "storage_01.slot_01")

    with pytest.raises(ResourceInUseError, match="remove/unplace"):
        state.samples.remove(sample.id)
    with pytest.raises(ResourceInUseError, match="remove/unplace"):
        state.remove_sample_resource(sample.id)

    assert state.samples.get(sample.id) is sample
    assert sample.current_location == "storage_01.slot_01"
    assert state.slots.get("storage_01.slot_01").occupant_ids == (sample.id,)


def test_unplaced_sample_resource_can_be_removed_safely() -> None:
    state = make_state()
    sample = Sample(id="sample_001", name="Sample")
    state.samples.add(sample)
    assert state.remove_sample_resource(sample.id) is sample
    assert not state.samples.contains(sample.id)


def test_sample_can_be_unplaced_then_removed_as_separate_operations() -> None:
    state = make_state()
    sample = Sample(id="sample_001", name="Sample")
    state.samples.add(sample)
    state.place_sample(sample.id, "storage_01.slot_01")
    state.remove_sample(sample.id)
    assert state.remove_sample_resource(sample.id) is sample
    assert state.slots.get("storage_01.slot_01").occupant_ids == ()


def test_station_with_empty_child_slot_cannot_be_removed() -> None:
    state = make_state()
    before = state.slots.list_by_station("storage_01")
    with pytest.raises(ResourceInUseError, match="child slots"):
        state.remove_station_resource("storage_01")
    assert state.stations.contains("storage_01")
    assert state.slots.list_by_station("storage_01") == before


def test_station_with_occupied_child_slot_cannot_be_removed() -> None:
    state = make_state()
    sample = Sample(id="sample_001", name="Sample")
    state.samples.add(sample)
    state.place_sample(sample.id, "storage_01.slot_01")
    with pytest.raises(ResourceInUseError, match="storage_01.slot_01"):
        state.remove_station_resource("storage_01")
    assert state.stations.contains("storage_01")
    assert state.slots.get("storage_01.slot_01").occupant_ids == (sample.id,)


def test_direct_station_registry_removal_cannot_bypass_lab_state() -> None:
    state = make_state()
    with pytest.raises(ResourceInUseError, match="LabState.remove_station_resource"):
        state.stations.remove("storage_01")
    assert state.stations.contains("storage_01")


def test_station_without_child_slots_can_be_removed_by_lab_state() -> None:
    state = LabState()
    station = Station(id="storage_01", display_name="Storage", station_type="storage")
    state.stations.add(station)
    assert state.remove_station_resource(station.id) is station
    assert not state.stations.contains(station.id)


def test_empty_slot_is_removable_but_occupied_slot_is_blocked() -> None:
    state = make_state()
    empty_slot = state.slots.get("storage_01.slot_01")
    assert state.slots.remove(empty_slot.id) is empty_slot

    state.slots.add(empty_slot)
    sample = Sample(id="sample_001", name="Sample")
    state.samples.add(sample)
    state.place_sample(sample.id, empty_slot.id)
    with pytest.raises(StationOccupiedError, match="remove the samples first"):
        state.slots.remove(empty_slot.id)
    with pytest.raises(ResourceInUseError):
        state.remove_sample_resource(sample.id)

    assert state.slots.get(empty_slot.id).occupant_ids == (sample.id,)
    assert state.samples.get(sample.id).current_location == empty_slot.id
