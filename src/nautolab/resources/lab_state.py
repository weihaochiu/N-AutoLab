"""Canonical laboratory resource state and atomic mutations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from nautolab.core import (
    LocationMismatchError,
    SampleHistoryEventType,
    StationDisabledError,
    StationOccupiedError,
)

from .device_registry import DeviceRegistry
from .sample_registry import SampleRegistry
from .station_registry import StationRegistry


@dataclass(slots=True)
class LabState:
    """Own registries and preserve cross-resource state invariants.

    All validations that can fail are performed before either side of a
    location transition is changed. Callers cannot directly assign sample
    locations or station occupancy through the public model API.
    """

    samples: SampleRegistry = field(default_factory=SampleRegistry)
    stations: StationRegistry = field(default_factory=StationRegistry)
    devices: DeviceRegistry = field(default_factory=DeviceRegistry)

    def place_sample(
        self,
        sample_id: str,
        station_id: str,
        *,
        note: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Place an unlocated sample at a station as one atomic transition."""
        transition_metadata = dict(metadata or {})
        sample = self.samples.get(sample_id)
        station = self.stations.get(station_id)

        if sample.current_location is not None:
            raise LocationMismatchError(
                f"sample {sample_id!r} is already located at {sample.current_location!r}"
            )
        self._validate_destination(station_id, sample_id)

        station._add_occupant(sample_id)
        sample._record_location_transition(
            event_type=SampleHistoryEventType.PLACED,
            source=None,
            destination=station_id,
            note=note,
            metadata=transition_metadata,
        )

    def remove_sample(
        self,
        sample_id: str,
        station_id: str | None = None,
        *,
        note: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Remove a located sample from its station atomically."""
        transition_metadata = dict(metadata or {})
        sample = self.samples.get(sample_id)
        source_id = station_id or sample.current_location
        if source_id is None:
            raise LocationMismatchError(f"sample {sample_id!r} is not located at a station")
        station = self.stations.get(source_id)
        self._validate_source(sample_id, source_id)

        station._remove_occupant(sample_id)
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
        source_station_id: str,
        destination_station_id: str,
        *,
        note: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Move a sample between stations without performing hardware motion."""
        transition_metadata = dict(metadata or {})
        if source_station_id == destination_station_id:
            raise LocationMismatchError("source and destination stations must differ")

        sample = self.samples.get(sample_id)
        source = self.stations.get(source_station_id)
        destination = self.stations.get(destination_station_id)
        self._validate_source(sample_id, source_station_id)
        self._validate_destination(destination_station_id, sample_id)

        source._remove_occupant(sample_id)
        destination._add_occupant(sample_id)
        sample._record_location_transition(
            event_type=SampleHistoryEventType.RELOCATED,
            source=source_station_id,
            destination=destination_station_id,
            note=note,
            metadata=transition_metadata,
        )

    def _validate_source(self, sample_id: str, station_id: str) -> None:
        sample = self.samples.get(sample_id)
        station = self.stations.get(station_id)
        if sample.current_location != station_id or not station.contains_sample(sample_id):
            raise LocationMismatchError(
                f"sample {sample_id!r} and station {station_id!r} do not agree on location"
            )

    def _validate_destination(self, station_id: str, sample_id: str) -> None:
        station = self.stations.get(station_id)
        if not station.enabled:
            raise StationDisabledError(f"station {station_id!r} is disabled")
        if station.contains_sample(sample_id):
            raise LocationMismatchError(
                f"station {station_id!r} already contains sample {sample_id!r}"
            )
        if station.occupancy >= station.capacity:
            raise StationOccupiedError(
                f"station {station_id!r} is full ({station.occupancy}/{station.capacity})"
            )
