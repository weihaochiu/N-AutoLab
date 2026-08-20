"""Validation tests for malformed hierarchy configuration."""

from pathlib import Path

import pytest
import yaml

from nautolab.core import (
    ConfigurationError,
    DuplicateResourceError,
    DuplicateSlotIndexError,
    InvalidBooleanError,
    InvalidCapacityError,
    InvalidIdentifierError,
    ResourceNotFoundError,
)
from nautolab.resources import load_lab_config


def write_config(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "lab.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def base_config() -> dict[str, object]:
    return {
        "schema_version": 2,
        "devices": [],
        "stations": [
            {
                "id": "storage_01",
                "display_name": "Storage 01",
                "station_type": "storage",
                "slots": [
                    {
                        "index": 1,
                        "id": "storage_01.slot_01",
                        "display_name": "ST01-S01",
                        "capacity": 1,
                    }
                ],
            }
        ],
        "samples": [],
    }


def test_duplicate_station_id_is_rejected(tmp_path: Path) -> None:
    data = base_config()
    data["stations"] = [*data["stations"], *data["stations"]]  # type: ignore[index]
    with pytest.raises(DuplicateResourceError):
        load_lab_config(write_config(tmp_path, data))


def test_duplicate_slot_id_is_rejected(tmp_path: Path) -> None:
    data = base_config()
    slots = data["stations"][0]["slots"]  # type: ignore[index]
    slots.append(dict(slots[0]))
    with pytest.raises(DuplicateResourceError):
        load_lab_config(write_config(tmp_path, data))


def test_duplicate_slot_index_is_rejected(tmp_path: Path) -> None:
    data = base_config()
    data["stations"][0]["slots"].append(  # type: ignore[index]
        {"index": 1, "id": "storage_01.slot_001", "display_name": "duplicate index"}
    )
    with pytest.raises(DuplicateSlotIndexError):
        load_lab_config(write_config(tmp_path, data))


def test_nested_slot_cannot_declare_a_different_parent(tmp_path: Path) -> None:
    data = base_config()
    slot = data["stations"][0]["slots"][0]  # type: ignore[index]
    slot["parent_station_id"] = "storage_99"
    slot["id"] = "storage_99.slot_01"
    with pytest.raises(ConfigurationError, match="nested under station 'storage_01'"):
        load_lab_config(write_config(tmp_path, data))


def test_nested_slot_may_repeat_its_actual_parent(tmp_path: Path) -> None:
    data = base_config()
    data["stations"][0]["slots"][0]["parent_station_id"] = "storage_01"  # type: ignore[index]
    state = load_lab_config(write_config(tmp_path, data))
    assert state.slots.get("storage_01.slot_01").parent_station_id == "storage_01"


def test_nested_slot_id_must_belong_to_its_outer_station(tmp_path: Path) -> None:
    data = base_config()
    data["stations"][0]["slots"][0]["id"] = "storage_99.slot_01"  # type: ignore[index]
    with pytest.raises(InvalidIdentifierError, match="does not belong"):
        load_lab_config(write_config(tmp_path, data))


@pytest.mark.parametrize("capacity", [-1, True, 1.5])
def test_invalid_slot_capacity_is_rejected(tmp_path: Path, capacity: object) -> None:
    data = base_config()
    data["stations"][0]["slots"][0]["capacity"] = capacity  # type: ignore[index]
    with pytest.raises(InvalidCapacityError):
        load_lab_config(write_config(tmp_path, data))


def test_sample_location_cannot_reference_parent_station(tmp_path: Path) -> None:
    data = base_config()
    data["samples"] = [
        {"id": "sample_001", "name": "Sample", "initial_location": "storage_01"}
    ]
    with pytest.raises(ConfigurationError, match="exact slot"):
        load_lab_config(write_config(tmp_path, data))


def test_sample_missing_slot_reference_is_rejected(tmp_path: Path) -> None:
    data = base_config()
    data["samples"] = [
        {
            "id": "sample_001",
            "name": "Sample",
            "initial_location": "storage_01.slot_99",
        }
    ]
    with pytest.raises(ResourceNotFoundError, match="station slot"):
        load_lab_config(write_config(tmp_path, data))


@pytest.mark.parametrize(("station_enabled", "slot_enabled"), [(False, True), (True, False)])
def test_disabled_parent_or_slot_loads_when_unoccupied(
    tmp_path: Path, station_enabled: bool, slot_enabled: bool
) -> None:
    data = base_config()
    data["stations"][0]["enabled"] = station_enabled  # type: ignore[index]
    data["stations"][0]["slots"][0]["enabled"] = slot_enabled  # type: ignore[index]
    state = load_lab_config(write_config(tmp_path, data))
    assert state.stations.get("storage_01").enabled is station_enabled
    assert state.slots.get("storage_01.slot_01").enabled is slot_enabled


@pytest.mark.parametrize("enabled", ["true", "false", 1, 0, None, []])
def test_station_enabled_requires_yaml_boolean(tmp_path: Path, enabled: object) -> None:
    data = base_config()
    data["stations"][0]["enabled"] = enabled  # type: ignore[index]
    with pytest.raises(InvalidBooleanError, match="Boolean true/false"):
        load_lab_config(write_config(tmp_path, data))


@pytest.mark.parametrize("enabled", ["true", "false", 1, 0, None, []])
def test_slot_enabled_requires_yaml_boolean(tmp_path: Path, enabled: object) -> None:
    data = base_config()
    data["stations"][0]["slots"][0]["enabled"] = enabled  # type: ignore[index]
    with pytest.raises(InvalidBooleanError, match="Boolean true/false"):
        load_lab_config(write_config(tmp_path, data))


def test_missing_station_device_reference_is_rejected(tmp_path: Path) -> None:
    data = base_config()
    data["stations"][0]["device_id"] = "missing_device"  # type: ignore[index]
    with pytest.raises(ResourceNotFoundError, match="device"):
        load_lab_config(write_config(tmp_path, data))


def test_invalid_device_state_is_configuration_error(tmp_path: Path) -> None:
    data = base_config()
    data["devices"] = [
        {
            "id": "device_01",
            "display_name": "Device",
            "device_type": "generic_device",
            "implementation_state": "READY",
        }
    ]
    with pytest.raises(ConfigurationError, match="invalid value"):
        load_lab_config(write_config(tmp_path, data))


def test_station_without_slots_is_rejected(tmp_path: Path) -> None:
    data = base_config()
    data["stations"][0]["slots"] = []  # type: ignore[index]
    with pytest.raises(ConfigurationError, match="at least one slot"):
        load_lab_config(write_config(tmp_path, data))


def test_wrong_schema_version_and_non_mapping_root_are_rejected(tmp_path: Path) -> None:
    data = base_config()
    data["schema_version"] = 1
    with pytest.raises(ConfigurationError, match="schema_version"):
        load_lab_config(write_config(tmp_path, data))
    with pytest.raises(ConfigurationError, match="root"):
        load_lab_config(write_config(tmp_path, ["not", "a", "mapping"]))
