"""Tests for Station state and capacity semantics."""

import pytest

from nautolab.core import InvalidCapacityError, Station


def make_station(**overrides: object) -> Station:
    values = {
        "id": "storage_s1",
        "display_name": "Storage S1",
        "station_type": "storage",
        "capacity": 1,
    }
    values.update(overrides)
    return Station(**values)  # type: ignore[arg-type]


def test_station_has_semantic_pose_reference() -> None:
    station = make_station(pose_reference="storage_s1_pose")
    assert station.pose_reference == "storage_s1_pose"


def test_station_occupancy_is_read_only_and_initially_empty() -> None:
    station = make_station()
    assert station.occupant_ids == ()
    assert station.occupancy == 0
    with pytest.raises(AttributeError):
        station.occupant_ids = ("sample_001",)  # type: ignore[misc]


def test_station_supports_capacity_greater_than_one() -> None:
    station = make_station(capacity=3)
    assert station.capacity == 3
    assert station.remaining_capacity == 3


def test_station_enabled_state_is_explicit() -> None:
    station = make_station(enabled=False)
    assert station.enabled is False


@pytest.mark.parametrize("capacity", [-1, 1.5, True, "1"])
def test_station_rejects_invalid_capacity(capacity: object) -> None:
    with pytest.raises(InvalidCapacityError):
        make_station(capacity=capacity)


def test_station_is_distinct_from_attached_device() -> None:
    station = make_station(device_id="hotplate_01")
    assert station.device_id == "hotplate_01"
    assert not hasattr(station, "connection_state")


def test_station_to_dict_reports_occupancy() -> None:
    data = make_station().to_dict()
    assert data["occupant_ids"] == []
    assert data["capacity"] == 1
