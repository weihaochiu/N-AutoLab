"""Validation tests for malformed laboratory YAML."""

from pathlib import Path

import pytest
import yaml

from nautolab.core import (
    ConfigurationError,
    DuplicateResourceError,
    InvalidCapacityError,
    ResourceNotFoundError,
)
from nautolab.resources import load_lab_config


def write_config(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "lab.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def base_config() -> dict[str, object]:
    return {
        "schema_version": 1,
        "devices": [],
        "stations": [
            {
                "id": "storage_s1",
                "display_name": "Storage S1",
                "station_type": "storage",
                "capacity": 1,
            }
        ],
        "samples": [],
    }


def test_duplicate_station_id_is_rejected(tmp_path: Path) -> None:
    data = base_config()
    data["stations"] = [*data["stations"], *data["stations"]]  # type: ignore[index]
    with pytest.raises(DuplicateResourceError):
        load_lab_config(write_config(tmp_path, data))


def test_invalid_station_capacity_is_rejected(tmp_path: Path) -> None:
    data = base_config()
    data["stations"][0]["capacity"] = -1  # type: ignore[index]
    with pytest.raises(InvalidCapacityError):
        load_lab_config(write_config(tmp_path, data))


def test_missing_initial_station_reference_is_rejected(tmp_path: Path) -> None:
    data = base_config()
    data["samples"] = [
        {"id": "sample_001", "name": "Sample", "initial_location": "missing_station"}
    ]
    with pytest.raises(ResourceNotFoundError, match="station"):
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


def test_wrong_schema_version_is_rejected(tmp_path: Path) -> None:
    data = base_config()
    data["schema_version"] = 99
    with pytest.raises(ConfigurationError, match="schema_version"):
        load_lab_config(write_config(tmp_path, data))


def test_yaml_root_must_be_mapping(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="root"):
        load_lab_config(write_config(tmp_path, ["not", "a", "mapping"]))
