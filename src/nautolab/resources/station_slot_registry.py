"""Registry for exact sample-holding station slots."""

from nautolab.core import (
    DuplicateResourceError,
    DuplicateSlotIndexError,
    StationOccupiedError,
    StationSlot,
)

from ._registry import ResourceRegistry
from .station_registry import StationRegistry


class StationSlotRegistry(ResourceRegistry[StationSlot]):
    """Validate and index station slots with explicit parent ownership."""

    resource_label = "station slot"

    def __init__(self, stations: StationRegistry) -> None:
        super().__init__()
        self._stations = stations

    def add(self, slot: StationSlot) -> None:
        """Add a slot after validating its parent, id, and station-local index."""
        self._stations.get(slot.parent_station_id)
        if self.contains(slot.id):
            raise DuplicateResourceError(f"station slot {slot.id!r} is already registered")
        if any(
            existing.slot_index == slot.slot_index
            for existing in self.list_by_station(slot.parent_station_id)
        ):
            raise DuplicateSlotIndexError(
                f"station {slot.parent_station_id!r} already has slot_index "
                f"{slot.slot_index}"
            )
        super().add(slot)

    def remove(self, resource_id: str) -> StationSlot:
        """Remove an empty slot; occupied slot removal would orphan state."""
        slot = self.get(resource_id)
        if slot.occupancy:
            raise StationOccupiedError(
                f"cannot remove occupied slot {resource_id!r}"
            )
        return super().remove(resource_id)

    def list_all(self) -> tuple[StationSlot, ...]:
        """Return slots ordered by parent station id and slot index."""
        return tuple(
            sorted(
                self._items.values(),
                key=lambda slot: (slot.parent_station_id, slot.slot_index, slot.id),
            )
        )

    def list_by_station(self, parent_station_id: str) -> tuple[StationSlot, ...]:
        """Return one station's slots in deterministic slot-index order."""
        self._stations.get(parent_station_id)
        return tuple(
            slot
            for slot in self.list_all()
            if slot.parent_station_id == parent_station_id
        )
