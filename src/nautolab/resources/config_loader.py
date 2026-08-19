"""YAML loader for portable laboratory resource configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from nautolab.core import ConfigurationError, Device, Sample, Station

from .lab_state import LabState


def load_lab_config(path: Path) -> LabState:
    """Load and validate a Phase 1A laboratory configuration file."""
    config_path = Path(path)
    try:
        with config_path.open("r", encoding="utf-8") as stream:
            document = yaml.safe_load(stream)
    except OSError as exc:
        raise ConfigurationError(f"cannot read lab configuration {config_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"invalid YAML in {config_path}: {exc}") from exc

    root = _require_mapping(document, "configuration root")
    if root.get("schema_version") != 1:
        raise ConfigurationError("schema_version must be 1")

    state = LabState()
    try:
        for data in _require_mapping_list(root.get("devices", []), "devices"):
            state.devices.add(
                Device(
                    id=_required(data, "id", "device"),
                    display_name=_required(data, "display_name", "device"),
                    device_type=_required(data, "device_type", "device"),
                    implementation_state=data.get("implementation_state", "NOT_IMPLEMENTED"),
                    connection_state=data.get("connection_state", "DISCONNECTED"),
                    capabilities=tuple(data.get("capabilities", [])),
                    backend_name=data.get("backend_name"),
                    metadata=_optional_mapping(data.get("metadata"), "device metadata"),
                )
            )

        for data in _require_mapping_list(root.get("stations", []), "stations"):
            station = Station(
                id=_required(data, "id", "station"),
                display_name=_required(data, "display_name", "station"),
                station_type=_required(data, "station_type", "station"),
                capacity=_required(data, "capacity", "station"),
                pose_reference=data.get("pose_reference"),
                capabilities=tuple(data.get("capabilities", [])),
                enabled=data.get("enabled", True),
                metadata=_optional_mapping(data.get("metadata"), "station metadata"),
                device_id=data.get("device_id"),
            )
            if station.device_id is not None:
                state.devices.get(station.device_id)
            state.stations.add(station)

        pending_placements: list[tuple[str, str]] = []
        for data in _require_mapping_list(root.get("samples", []), "samples"):
            sample = Sample(
                id=_required(data, "id", "sample"),
                name=_required(data, "name", "sample"),
                sample_type=data.get("sample_type"),
                status=data.get("status", "READY"),
                metadata=_optional_mapping(data.get("metadata"), "sample metadata"),
            )
            state.samples.add(sample)
            if data.get("initial_location") is not None:
                pending_placements.append((sample.id, data["initial_location"]))

        for sample_id, station_id in pending_placements:
            state.place_sample(sample_id, station_id, note="Loaded from lab configuration")
    except ConfigurationError:
        raise
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"invalid value in {config_path}: {exc}") from exc

    return state


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{label} must be a mapping")
    return value


def _require_mapping_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ConfigurationError(f"{label} must be a list")
    result: list[dict[str, Any]] = []
    for index, entry in enumerate(value):
        result.append(_require_mapping(entry, f"{label}[{index}]"))
    return result


def _required(data: dict[str, Any], key: str, label: str) -> Any:
    if key not in data:
        raise ConfigurationError(f"{label} is missing required field {key!r}")
    return data[key]


def _optional_mapping(value: Any, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    return _require_mapping(value, label)
