"""Sample-holding child resource of a station instance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._validation import (
    normalize_identifiers,
    validate_bool,
    validate_identifier,
    validate_non_empty_text,
    validate_slot_id,
    validate_station_instance_id,
)
from .errors import InvalidCapacityError, LocationMismatchError, StationOccupiedError


@dataclass(slots=True)
class StationSlot:
    """An exact sample position with its own capacity and semantic pose."""

    id: str
    display_name: str
    parent_station_id: str
    slot_index: int
    capacity: int = 1
    pose_reference: str | None = None
    enabled: bool = True
    capabilities: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    _occupant_ids: list[str] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.parent_station_id = validate_station_instance_id(self.parent_station_id)
        if isinstance(self.slot_index, bool) or not isinstance(self.slot_index, int):
            raise InvalidCapacityError("slot_index must be a positive integer")
        if self.slot_index < 1:
            raise InvalidCapacityError("slot_index must be a positive integer")
        self.id = validate_slot_id(
            self.id,
            parent_station_id=self.parent_station_id,
            slot_index=self.slot_index,
        )
        self.display_name = validate_non_empty_text(self.display_name, field_name="display_name")
        self.enabled = validate_bool(self.enabled, field_name=f"slot {self.id} enabled")
        if isinstance(self.capacity, bool) or not isinstance(self.capacity, int) or self.capacity < 0:
            raise InvalidCapacityError(
                f"slot {self.id!r} capacity must be a non-negative integer"
            )
        if self.pose_reference is not None:
            self.pose_reference = validate_identifier(
                self.pose_reference, field_name="pose_reference"
            )
        self.capabilities = normalize_identifiers(
            self.capabilities, field_name="slot capability"
        )
        self.metadata = dict(self.metadata)

    @property
    def occupant_ids(self) -> tuple[str, ...]:
        """Return an immutable ordered view of occupying sample identifiers."""
        return tuple(self._occupant_ids)

    @property
    def occupancy(self) -> int:
        """Return the number of samples in this exact slot."""
        return len(self._occupant_ids)

    @property
    def remaining_capacity(self) -> int:
        """Return the number of samples the slot can still accept."""
        return self.capacity - self.occupancy

    def contains_sample(self, sample_id: str) -> bool:
        """Return whether the sample occupies this slot."""
        return sample_id in self._occupant_ids

    def _add_occupant(self, sample_id: str) -> None:
        """Add a previously validated occupant; ``LabState`` only."""
        sample_id = validate_identifier(sample_id, field_name="sample_id")
        if sample_id in self._occupant_ids:
            raise LocationMismatchError(
                f"sample {sample_id!r} already occupies slot {self.id!r}"
            )
        if self.occupancy >= self.capacity:
            raise StationOccupiedError(
                f"slot {self.id!r} is full ({self.occupancy}/{self.capacity})"
            )
        self._occupant_ids.append(sample_id)

    def _remove_occupant(self, sample_id: str) -> None:
        """Remove a previously validated occupant; ``LabState`` only."""
        if sample_id not in self._occupant_ids:
            raise LocationMismatchError(
                f"sample {sample_id!r} does not occupy slot {self.id!r}"
            )
        self._occupant_ids.remove(sample_id)

    def _restore_occupants(self, occupant_ids: tuple[str, ...]) -> None:
        """Restore a LabState transaction snapshot after an exception."""
        self._occupant_ids[:] = occupant_ids

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/YAML-friendly slot state."""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "parent_station_id": self.parent_station_id,
            "slot_index": self.slot_index,
            "capacity": self.capacity,
            "occupant_ids": list(self.occupant_ids),
            "pose_reference": self.pose_reference,
            "enabled": self.enabled,
            "capabilities": list(self.capabilities),
            "metadata": dict(self.metadata),
        }
