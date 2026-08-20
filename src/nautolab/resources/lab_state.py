"""Canonical slot-level laboratory state and atomic mutations."""

from __future__ import annotations

from typing import Any, Mapping

from nautolab.core import (
    LocationMismatchError,
    SampleHistoryEventType,
    SlotDisabledError,
    StationDisabledError,
    StationOccupiedError,
    StationSlot,
)

from .device_registry import DeviceRegistry
from .sample_registry import SampleRegistry
from .station_registry import StationRegistry
from .station_slot_registry import StationSlotRegistry


class LabState:
    """Own registries and preserve sample/slot state invariants.

    Stations are descriptive parents. Exact occupancy lives only on slots, and
    every station aggregate is calculated from its child slots.
    """

    def __init__(
        self,
        *,
        samples: SampleRegistry | None = None,
        stations: StationRegistry | None = None,
        devices: DeviceRegistry | None = None,
    ) -> None:
        self.samples = samples or SampleRegistry()
        self.stations = stations or StationRegistry()
        self.devices = devices or DeviceRegistry()
        self.slots = StationSlotRegistry(self.stations)

    def place_sample(
        self,
        sample_id: str,
        slot_id: str,
        *,
        note: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Place an unlocated sample in an exact slot atomically."""
        transition_metadata = dict(metadata or {})
        sample = self.samples.get(sample_id)
        slot = self.slots.get(slot_id)
        if sample.current_location is not None:
            raise LocationMismatchError(
                f"sample {sample_id!r} is already located at {sample.current_location!r}"
            )
        self._validate_destination(slot, sample_id)

        slot._add_occupant(sample_id)
        sample._record_location_transition(
            event_type=SampleHistoryEventType.PLACED,
            source=None,
            destination=slot_id,
            note=note,
            metadata=transition_metadata,
        )

    def remove_sample(
        self,
        sample_id: str,
        slot_id: str | None = None,
        *,
        note: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Remove a located sample from its exact slot atomically."""
        transition_metadata = dict(metadata or {})
        sample = self.samples.get(sample_id)
        source_id = slot_id or sample.current_location
        if source_id is None:
            raise LocationMismatchError(f"sample {sample_id!r} is not located in a slot")
        source = self.slots.get(source_id)
        self._validate_source(sample_id, source)

        source._remove_occupant(sample_id)
        sample._record_location_transition(
            event_type=SampleHistoryEventType.REMOVED,
            source=source_id,
            destination=None,
            note=note,
            metadata=transition_metadata,
        )

    def relocate_sample(
        self,
        sample_id: str,
        source_slot_id: str,
        destination_slot_id: str,
        *,
        note: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Change exact slot state without simulating or commanding transport."""
        transition_metadata = dict(metadata or {})
        if source_slot_id == destination_slot_id:
            raise LocationMismatchError("source and destination slots must differ")

        sample = self.samples.get(sample_id)
        source = self.slots.get(source_slot_id)
        destination = self.slots.get(destination_slot_id)
        self._validate_source(sample_id, source)
        self._validate_destination(destination, sample_id)

        source._remove_occupant(sample_id)
        destination._add_occupant(sample_id)
        sample._record_location_transition(
            event_type=SampleHistoryEventType.RELOCATED,
            source=source_slot_id,
            destination=destination_slot_id,
            note=note,
            metadata=transition_metadata,
        )

    def station_total_capacity(self, station_id: str) -> int:
        """Return the sum of all child-slot capacities."""
        self.stations.get(station_id)
        return sum(slot.capacity for slot in self.slots.list_by_station(station_id))

    def station_occupancy(self, station_id: str) -> int:
        """Return aggregate occupancy calculated only from child slots."""
        self.stations.get(station_id)
        return sum(slot.occupancy for slot in self.slots.list_by_station(station_id))

    def station_available_capacity(self, station_id: str) -> int:
        """Return total capacity minus aggregate occupancy."""
        return self.station_total_capacity(station_id) - self.station_occupancy(station_id)

    def station_occupant_ids(self, station_id: str) -> tuple[str, ...]:
        """Return occupants aggregated in deterministic slot order."""
        self.stations.get(station_id)
        return tuple(
            sample_id
            for slot in self.slots.list_by_station(station_id)
            for sample_id in slot.occupant_ids
        )

    def available_slots_for_station(self, station_id: str) -> tuple[StationSlot, ...]:
        """Return enabled, non-full slots for one enabled station."""
        station = self.stations.get(station_id)
        if not station.enabled:
            return ()
        return tuple(
            slot
            for slot in self.slots.list_by_station(station_id)
            if slot.enabled and slot.remaining_capacity > 0
        )

    def available_slots_for_station_type(self, station_type: str) -> tuple[StationSlot, ...]:
        """Return deterministic available slots across same-type stations."""
        return tuple(
            slot
            for station in self.stations.list_by_type(station_type)
            for slot in self.available_slots_for_station(station.id)
        )

    def _validate_source(self, sample_id: str, slot: StationSlot) -> None:
        sample = self.samples.get(sample_id)
        if sample.current_location != slot.id or not slot.contains_sample(sample_id):
            raise LocationMismatchError(
                f"sample {sample_id!r} and slot {slot.id!r} do not agree on location"
            )

    def _validate_destination(self, slot: StationSlot, sample_id: str) -> None:
        station = self.stations.get(slot.parent_station_id)
        if not station.enabled:
            raise StationDisabledError(f"station {station.id!r} is disabled")
        if not slot.enabled:
            raise SlotDisabledError(f"station slot {slot.id!r} is disabled")
        if slot.contains_sample(sample_id):
            raise LocationMismatchError(
                f"slot {slot.id!r} already contains sample {sample_id!r}"
            )
        if slot.occupancy >= slot.capacity:
            raise StationOccupiedError(
                f"slot {slot.id!r} is full ({slot.occupancy}/{slot.capacity})"
            )
