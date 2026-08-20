"""General-purpose station-instance domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._validation import (
    normalize_identifiers,
    validate_identifier,
    validate_non_empty_text,
    validate_station_instance_id,
)


@dataclass(slots=True)
class Station:
    """An identifiable station instance, separate from slots and devices.

    Sample capacity and occupancy are derived by ``LabState`` from child
    ``StationSlot`` objects. ``pose_reference`` is an optional station-level
    service/calibration pose, never a sample placement location.
    """

    id: str
    display_name: str
    station_type: str
    pose_reference: str | None = None
    capabilities: tuple[str, ...] = ()
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    device_id: str | None = None
    display_prefix: str | None = None

    def __post_init__(self) -> None:
        self.station_type = validate_identifier(self.station_type, field_name="station_type")
        self.id = validate_station_instance_id(self.id, station_type=self.station_type)
        self.display_name = validate_non_empty_text(self.display_name, field_name="display_name")
        if self.pose_reference is not None:
            self.pose_reference = validate_identifier(
                self.pose_reference, field_name="pose_reference"
            )
        if self.device_id is not None:
            self.device_id = validate_identifier(self.device_id, field_name="device_id")
        if self.display_prefix is not None:
            self.display_prefix = validate_non_empty_text(
                self.display_prefix, field_name="display_prefix"
            )
        self.capabilities = normalize_identifiers(
            self.capabilities, field_name="station capability"
        )
        self.metadata = dict(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        """Return station identity/configuration without duplicated occupancy."""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "station_type": self.station_type,
            "pose_reference": self.pose_reference,
            "capabilities": list(self.capabilities),
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
            "device_id": self.device_id,
            "display_prefix": self.display_prefix,
        }
