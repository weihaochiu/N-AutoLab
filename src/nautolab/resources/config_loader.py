"""YAML loader for portable laboratory resource configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from nautolab.core import ConfigurationError, Device, Sample, Station, StationSlot

from .lab_state import LabState


def load_lab_config(path: Path) -> LabState:
    """Load and validate a Phase 1A.1 slot-hierarchy configuration file."""
    config_path = Path(path)
    try:
        with config_path.open("r", encoding="utf-8") as stream:
            document = yaml.safe_load(stream)
    except OSError as exc:
        raise ConfigurationError(f"cannot read lab configuration {config_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"invalid YAML in {config_path}: {exc}") from exc

    root = _require_mapping(document, "configuration root")
    if root.get("schema_version") != 2:
        raise ConfigurationError("schema_version must be 2")

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
                pose_reference=data.get("pose_reference"),
                capabilities=tuple(data.get("capabilities", [])),
                enabled=data.get("enabled", True),
                metadata=_optional_mapping(data.get("metadata"), "station metadata"),
                device_id=data.get("device_id"),
                display_prefix=data.get("display_prefix"),
            )
            if station.device_id is not None:
                state.devices.get(station.device_id)
            state.stations.add(station)

            slot_data = _require_mapping_list(data.get("slots", []), f"station {station.id} slots")
            if not slot_data:
                raise ConfigurationError(
                    f"sample-holding station {station.id!r} must define at least one slot"
                )
            for entry in slot_data:
                slot_index = _required(entry, "index", f"station {station.id} slot")
                explicit_parent_id = entry.get("parent_station_id")
                if explicit_parent_id is not None and explicit_parent_id != station.id:
                    raise ConfigurationError(
                        f"slot {_required(entry, 'id', f'station {station.id} slot')!r} "
                        f"is nested under station {station.id!r} but declares parent "
                        f"{explicit_parent_id!r}"
                    )
                state.slots.add(
                    StationSlot(
                        id=_required(entry, "id", f"station {station.id} slot"),
                        display_name=_required(
                            entry, "display_name", f"station {station.id} slot"
                        ),
                        parent_station_id=station.id,
                        slot_index=slot_index,
                        capacity=entry.get("capacity", 1),
                        pose_reference=entry.get("pose_reference"),
                        enabled=entry.get("enabled", True),
                        capabilities=tuple(entry.get("capabilities", [])),
                        metadata=_optional_mapping(
                            entry.get("metadata"), f"station {station.id} slot metadata"
                        ),
                    )
                )

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
                initial_location = data["initial_location"]
                if state.stations.contains(initial_location):
                    raise ConfigurationError(
                        f"sample {sample.id!r} initial_location must reference an exact "
                        f"slot, not station {initial_location!r}"
                    )
                pending_placements.append((sample.id, initial_location))

        for sample_id, slot_id in pending_placements:
            state.place_sample(sample_id, slot_id, note="Loaded from lab configuration")
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
