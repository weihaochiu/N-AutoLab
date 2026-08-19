"""Integration tests for canonical sample/station state transitions."""

import pytest

from nautolab.core import (
    LocationMismatchError,
    Sample,
    SampleHistoryEventType,
    Station,
    StationDisabledError,
    StationOccupiedError,
)
from nautolab.resources import LabState


def make_state(*, destination_capacity: int = 1) -> LabState:
    state = LabState()
    state.stations.add(
        Station(id="storage_s1", display_name="Storage S1", station_type="storage", capacity=2)
    )
    state.stations.add(
        Station(
            id="process_station",
            display_name="Process Station",
            station_type="process",
            capacity=destination_capacity,
        )
    )
    state.samples.add(Sample(id="sample_001", name="Sample 001"))
    state.place_sample("sample_001", "storage_s1")
    return state


def test_initial_placement_updates_both_views() -> None:
    state = make_state()
    sample = state.samples.get("sample_001")
    station = state.stations.get("storage_s1")
    assert sample.current_location == "storage_s1"
    assert station.occupant_ids == ("sample_001",)
    assert sample.history[-1].event_type is SampleHistoryEventType.PLACED


def test_relocation_updates_both_views_and_history() -> None:
    state = make_state()
    state.relocate_sample("sample_001", "storage_s1", "process_station")
    sample = state.samples.get("sample_001")
    assert sample.current_location == "process_station"
    assert state.stations.get("storage_s1").occupant_ids == ()
    assert state.stations.get("process_station").occupant_ids == ("sample_001",)
    assert sample.history[-1].event_type is SampleHistoryEventType.RELOCATED


def test_remove_updates_both_views() -> None:
    state = make_state()
    state.remove_sample("sample_001")
    assert state.samples.get("sample_001").current_location is None
    assert state.stations.get("storage_s1").occupant_ids == ()


def test_occupied_destination_failure_does_not_partially_mutate() -> None:
    state = make_state()
    state.samples.add(Sample(id="sample_002", name="Sample 002"))
    state.place_sample("sample_002", "process_station")
    before_history = state.samples.get("sample_001").history

    with pytest.raises(StationOccupiedError):
        state.relocate_sample("sample_001", "storage_s1", "process_station")

    assert state.samples.get("sample_001").current_location == "storage_s1"
    assert state.stations.get("storage_s1").occupant_ids == ("sample_001",)
    assert state.stations.get("process_station").occupant_ids == ("sample_002",)
    assert state.samples.get("sample_001").history == before_history


def test_source_mismatch_failure_does_not_mutate() -> None:
    state = make_state()
    with pytest.raises(LocationMismatchError):
        state.relocate_sample("sample_001", "process_station", "storage_s1")
    assert state.samples.get("sample_001").current_location == "storage_s1"
    assert state.stations.get("storage_s1").occupant_ids == ("sample_001",)


def test_disabled_destination_rejects_placement_without_mutation() -> None:
    state = make_state()
    state.samples.add(Sample(id="sample_002", name="Sample 002"))
    state.stations.get("process_station").enabled = False
    with pytest.raises(StationDisabledError):
        state.place_sample("sample_002", "process_station")
    assert state.samples.get("sample_002").current_location is None
    assert state.stations.get("process_station").occupant_ids == ()


def test_capacity_greater_than_one_accepts_multiple_samples() -> None:
    state = make_state(destination_capacity=2)
    state.samples.add(Sample(id="sample_002", name="Sample 002"))
    state.samples.add(Sample(id="sample_003", name="Sample 003"))
    state.place_sample("sample_002", "process_station")
    state.place_sample("sample_003", "process_station")
    assert state.stations.get("process_station").occupant_ids == (
        "sample_002",
        "sample_003",
    )
    state.samples.add(Sample(id="sample_004", name="Sample 004"))
    with pytest.raises(StationOccupiedError):
        state.place_sample("sample_004", "process_station")
    assert state.samples.get("sample_004").current_location is None
    assert state.stations.get("process_station").occupant_ids == (
        "sample_002",
        "sample_003",
    )


def test_place_already_located_sample_is_rejected() -> None:
    state = make_state()
    with pytest.raises(LocationMismatchError):
        state.place_sample("sample_001", "process_station")
    assert state.samples.get("sample_001").current_location == "storage_s1"


def test_invalid_transition_metadata_cannot_cause_partial_mutation() -> None:
    state = make_state()
    with pytest.raises((TypeError, ValueError)):
        state.relocate_sample(
            "sample_001",
            "storage_s1",
            "process_station",
            metadata="not_a_mapping",  # type: ignore[arg-type]
        )
    assert state.samples.get("sample_001").current_location == "storage_s1"
    assert state.stations.get("storage_s1").occupant_ids == ("sample_001",)
    assert state.stations.get("process_station").occupant_ids == ()
