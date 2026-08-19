"""General-purpose station domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._validation import normalize_identifiers, validate_identifier, validate_non_empty_text
from .errors import InvalidCapacityError, LocationMismatchError, StationOccupiedError


@dataclass(slots=True)
class Station:
    """A logical laboratory location, separate from any attached device."""

    id: str
    display_name: str
    station_type: str
    capacity: int
    pose_reference: str | None = None
    capabilities: tuple[str, ...] = ()
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    device_id: str | None = None
    _occupant_ids: list[str] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.id = validate_identifier(self.id)
        self.display_name = validate_non_empty_text(self.display_name, field_name="display_name")
        self.station_type = validate_identifier(self.station_type, field_name="station_type")
        if isinstance(self.capacity, bool) or not isinstance(self.capacity, int) or self.capacity < 0:
            raise InvalidCapacityError(
                f"station {self.id!r} capacity must be a non-negative integer"
            )
        if self.pose_reference is not None:
            self.pose_reference = validate_identifier(
                self.pose_reference, field_name="pose_reference"
            )
        if self.device_id is not None:
            self.device_id = validate_identifier(self.device_id, field_name="device_id")
        self.capabilities = normalize_identifiers(
            self.capabilities, field_name="station capability"
        )
        self.metadata = dict(self.metadata)

    @property
    def occupant_ids(self) -> tuple[str, ...]:
        """Return an immutable ordered view of occupying sample identifiers."""
        return tuple(self._occupant_ids)

    @property
    def occupancy(self) -> int:
        """Return the number of samples currently occupying the station."""
        return len(self._occupant_ids)

    @property
    def remaining_capacity(self) -> int:
        """Return the number of additional samples the station can accept."""
        return self.capacity - self.occupancy

    def contains_sample(self, sample_id: str) -> bool:
        """Return whether the sample occupies this station."""
        return sample_id in self._occupant_ids

    def _add_occupant(self, sample_id: str) -> None:
        """Add a previously validated occupant; resource layer only."""
        sample_id = validate_identifier(sample_id, field_name="sample_id")
        if sample_id in self._occupant_ids:
            raise LocationMismatchError(
                f"sample {sample_id!r} already occupies station {self.id!r}"
            )
        if self.occupancy >= self.capacity:
            raise StationOccupiedError(
                f"station {self.id!r} is full ({self.occupancy}/{self.capacity})"
            )
        self._occupant_ids.append(sample_id)

    def _remove_occupant(self, sample_id: str) -> None:
        """Remove a previously validated occupant; resource layer only."""
        if sample_id not in self._occupant_ids:
            raise LocationMismatchError(
                f"sample {sample_id!r} does not occupy station {self.id!r}"
            )
        self._occupant_ids.remove(sample_id)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/YAML-friendly station data."""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "station_type": self.station_type,
            "capacity": self.capacity,
            "occupant_ids": list(self.occupant_ids),
            "pose_reference": self.pose_reference,
            "capabilities": list(self.capabilities),
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
            "device_id": self.device_id,
        }
