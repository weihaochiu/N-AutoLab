"""Tests for station-instance identity and device separation."""

import pytest

from nautolab.core import InvalidBooleanError, InvalidIdentifierError, Station


def make_station(**overrides: object) -> Station:
    values = {
        "id": "storage_01",
        "display_name": "Storage 01",
        "station_type": "storage",
    }
    values.update(overrides)
    return Station(**values)  # type: ignore[arg-type]


def test_station_instance_separates_id_type_and_display_name() -> None:
    station = make_station(display_prefix="ST01")
    assert station.id == "storage_01"
    assert station.station_type == "storage"
    assert station.display_name == "Storage 01"
    assert station.display_prefix == "ST01"


def test_station_has_optional_service_pose_not_sample_occupancy() -> None:
    station = make_station(pose_reference="storage_01_service")
    assert station.pose_reference == "storage_01_service"
    assert not hasattr(station, "occupant_ids")
    assert not hasattr(station, "capacity")


def test_station_enabled_state_is_explicit() -> None:
    assert make_station(enabled=False).enabled is False


@pytest.mark.parametrize("enabled", ["true", "false", 1, 0, None, []])
def test_station_enabled_requires_strict_boolean(enabled: object) -> None:
    with pytest.raises(InvalidBooleanError, match="enabled"):
        make_station(enabled=enabled)


def test_station_is_distinct_from_primary_device() -> None:
    station = make_station(device_id="storage_device_01")
    assert station.device_id == "storage_device_01"
    assert not hasattr(station, "connection_state")


@pytest.mark.parametrize(
    ("station_id", "station_type"),
    [("storage", "storage"), ("storage_s1", "storage"), ("hotplate_01", "storage")],
)
def test_station_rejects_noncanonical_or_mismatched_id(
    station_id: str, station_type: str
) -> None:
    with pytest.raises(InvalidIdentifierError):
        make_station(id=station_id, station_type=station_type)


def test_station_serialization_has_no_duplicate_occupancy_state() -> None:
    data = make_station().to_dict()
    assert data["id"] == "storage_01"
    assert "occupant_ids" not in data
    assert "capacity" not in data
