"""Tests for exact sample-holding StationSlot resources."""

import pytest

from nautolab.core import (
    InvalidCapacityError,
    InvalidIdentifierError,
    StationOccupiedError,
    StationSlot,
)


def make_slot(**overrides: object) -> StationSlot:
    values = {
        "id": "hotplate_01.slot_01",
        "display_name": "HP01-S01",
        "parent_station_id": "hotplate_01",
        "slot_index": 1,
        "capacity": 1,
        "pose_reference": "hotplate_01_slot_01",
        "capabilities": ("heated_position", "robot_accessible"),
    }
    values.update(overrides)
    return StationSlot(**values)  # type: ignore[arg-type]


def test_slot_contains_parent_index_pose_and_capabilities() -> None:
    slot = make_slot()
    assert slot.parent_station_id == "hotplate_01"
    assert slot.slot_index == 1
    assert slot.pose_reference == "hotplate_01_slot_01"
    assert slot.capabilities == ("heated_position", "robot_accessible")


def test_slot_occupancy_tracks_exact_samples_and_is_read_only() -> None:
    slot = make_slot(capacity=2)
    slot._add_occupant("sample_001")
    slot._add_occupant("sample_002")
    assert slot.occupant_ids == ("sample_001", "sample_002")
    assert slot.occupancy == 2
    assert slot.remaining_capacity == 0
    with pytest.raises(StationOccupiedError):
        slot._add_occupant("sample_003")
    with pytest.raises(AttributeError):
        slot.occupant_ids = ("sample_004",)  # type: ignore[misc]


def test_slot_enabled_state_is_explicit() -> None:
    assert make_slot(enabled=False).enabled is False


@pytest.mark.parametrize("capacity", [-1, 1.5, True, "1"])
def test_slot_rejects_invalid_capacity(capacity: object) -> None:
    with pytest.raises(InvalidCapacityError):
        make_slot(capacity=capacity)


@pytest.mark.parametrize(
    "overrides",
    [
        {"id": "hotplate_01"},
        {"id": "HP01-S01"},
        {"id": "hotplate_02.slot_01"},
        {"id": "hotplate_01.slot_02"},
    ],
)
def test_slot_rejects_invalid_or_inconsistent_id(overrides: dict[str, object]) -> None:
    with pytest.raises(InvalidIdentifierError):
        make_slot(**overrides)


def test_slot_serialization_includes_exact_state() -> None:
    data = make_slot().to_dict()
    assert data["id"] == "hotplate_01.slot_01"
    assert data["parent_station_id"] == "hotplate_01"
    assert data["occupant_ids"] == []
