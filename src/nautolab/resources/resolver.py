"""Deterministic, side-effect-free recipe destination resolution."""

from __future__ import annotations

from collections.abc import Mapping

from nautolab.core import (
    MoveDestination,
    ResourceNotFoundError,
    ResourceResolutionError,
)
from nautolab.core.station_slot import StationSlot

from .lab_state import LabState


class ResourceResolver:
    """Resolve destination intent to one exact slot without reserving or mutating."""

    def __init__(self, lab_state: LabState) -> None:
        self._lab_state = lab_state

    def resolve(
        self,
        destination: MoveDestination,
        *,
        occupancy: Mapping[str, int] | None = None,
    ) -> StationSlot:
        occupancy = occupancy or {}
        if destination.exact_slot_id is not None:
            try:
                slot = self._lab_state.slots.get(destination.exact_slot_id)
            except ResourceNotFoundError as exc:
                raise ResourceResolutionError(str(exc)) from exc
            self._require_available(slot, occupancy)
            return slot

        if destination.exact_station_id is not None:
            try:
                station = self._lab_state.stations.get(destination.exact_station_id)
            except ResourceNotFoundError as exc:
                raise ResourceResolutionError(str(exc)) from exc
            if not station.enabled:
                raise ResourceResolutionError(f"station {station.id!r} is disabled")
            return self._first_available(
                self._lab_state.slots.list_by_station(station.id), occupancy,
                failure=f"station {station.id!r} has no available slot",
            )

        station_type = destination.station_type
        assert station_type is not None
        stations = self._lab_state.stations.list_by_type(station_type)
        if not stations:
            raise ResourceResolutionError(f"station type {station_type!r} is not registered")
        candidates = tuple(
            slot
            for station in stations
            if station.enabled
            for slot in self._lab_state.slots.list_by_station(station.id)
        )
        return self._first_available(
            candidates, occupancy,
            failure=f"station type {station_type!r} has no available slot",
        )

    def _require_available(self, slot: StationSlot, occupancy: Mapping[str, int]) -> None:
        try:
            station = self._lab_state.stations.get(slot.parent_station_id)
        except ResourceNotFoundError as exc:
            raise ResourceResolutionError(str(exc)) from exc
        if not station.enabled:
            raise ResourceResolutionError(f"station {station.id!r} is disabled")
        if not slot.enabled:
            raise ResourceResolutionError(f"station slot {slot.id!r} is disabled")
        used = occupancy.get(slot.id, slot.occupancy)
        if used >= slot.capacity:
            raise ResourceResolutionError(f"station slot {slot.id!r} is full ({used}/{slot.capacity})")

    def _first_available(
        self,
        candidates: tuple[StationSlot, ...],
        occupancy: Mapping[str, int],
        *,
        failure: str,
    ) -> StationSlot:
        for slot in candidates:
            try:
                self._require_available(slot, occupancy)
            except ResourceResolutionError:
                continue
            return slot
        raise ResourceResolutionError(failure)
