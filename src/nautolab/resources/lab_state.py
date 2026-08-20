"""Canonical slot-level laboratory state and atomic mutations."""

from __future__ import annotations

from typing import Any, Mapping

from nautolab.core import (
    LocationMismatchError,
    ResourceInUseError,
    Sample,
    SampleHistoryEventType,
    SlotDisabledError,
    Station,
    StationDisabledError,
    StationOccupiedError,
    StationSlot,
)
from nautolab.core._validation import validate_identifier

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
        self.samples = samples if samples is not None else SampleRegistry()
        self.stations = stations if stations is not None else StationRegistry()
        self.devices = devices if devices is not None else DeviceRegistry()
        self.stations._manage_relational_removal()
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
        validate_identifier(sample_id, field_name="sample_id")
        sample = self.samples.get(sample_id)
        slot = self.slots.get(slot_id)
        if sample.current_location is not None:
            raise LocationMismatchError(
                f"sample {sample_id!r} is already located at {sample.current_location!r}"
            )
        self._validate_destination(slot, sample_id)

        self._apply_location_transition(
            sample=sample,
            source=None,
            destination=slot,
            event_type=SampleHistoryEventType.PLACED,
            source_id=None,
            destination_id=slot_id,
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
        validate_identifier(sample_id, field_name="sample_id")
        sample = self.samples.get(sample_id)
        source_id = slot_id or sample.current_location
        if source_id is None:
            raise LocationMismatchError(f"sample {sample_id!r} is not located in a slot")
        source = self.slots.get(source_id)
        self._validate_source(sample_id, source)

        self._apply_location_transition(
            sample=sample,
            source=source,
            destination=None,
            event_type=SampleHistoryEventType.REMOVED,
            source_id=source_id,
            destination_id=None,
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
        validate_identifier(sample_id, field_name="sample_id")
        if source_slot_id == destination_slot_id:
            raise LocationMismatchError("source and destination slots must differ")

        sample = self.samples.get(sample_id)
        source = self.slots.get(source_slot_id)
        destination = self.slots.get(destination_slot_id)
        self._validate_source(sample_id, source)
        self._validate_destination(destination, sample_id)

        self._apply_location_transition(
            sample=sample,
            source=source,
            destination=destination,
            event_type=SampleHistoryEventType.RELOCATED,
            source_id=source_slot_id,
            destination_id=destination_slot_id,
            note=note,
            metadata=transition_metadata,
        )

    def remove_sample_resource(self, sample_id: str) -> Sample:
        """Remove an unplaced Sample resource without changing location state."""
        return self.samples.remove(sample_id)

    def remove_station_resource(self, station_id: str) -> Station:
        """Remove a Station only after all child Slots were explicitly removed."""
        station = self.stations.get(station_id)
        child_slots = self.slots.list_by_station(station_id)
        if child_slots:
            child_ids = ", ".join(slot.id for slot in child_slots)
            raise ResourceInUseError(
                f"cannot remove station {station_id!r}: child slots still exist: "
                f"{child_ids}; remove empty slots first"
            )
        return self.stations._remove_from_lab_state(station.id)

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

    @staticmethod
    def _apply_location_transition(
        *,
        sample: Sample,
        source: StationSlot | None,
        destination: StationSlot | None,
        event_type: SampleHistoryEventType,
        source_id: str | None,
        destination_id: str | None,
        note: str | None,
        metadata: Mapping[str, Any],
    ) -> None:
        """Apply a prevalidated transition and roll back unexpected exceptions."""
        sample_location_before = sample.current_location
        sample_history_before = sample.history
        source_occupants_before = source.occupant_ids if source is not None else None
        destination_occupants_before = (
            destination.occupant_ids if destination is not None else None
        )
        try:
            if source is not None:
                source._remove_occupant(sample.id)
            if destination is not None:
                destination._add_occupant(sample.id)
            sample._record_location_transition(
                event_type=event_type,
                source=source_id,
                destination=destination_id,
                note=note,
                metadata=metadata,
            )
        except Exception:
            if source is not None and source_occupants_before is not None:
                source._restore_occupants(source_occupants_before)
            if destination is not None and destination_occupants_before is not None:
                destination._restore_occupants(destination_occupants_before)
            sample._restore_location_state(sample_location_before, sample_history_before)
            raise
