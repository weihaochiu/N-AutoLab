"""Tests for StationSlotRegistry parent and ordering invariants."""

import pytest

from nautolab.core import (
    DuplicateResourceError,
    DuplicateSlotIndexError,
    ResourceNotFoundError,
    Station,
    StationOccupiedError,
    StationSlot,
)
from nautolab.resources import StationRegistry, StationSlotRegistry


def slot(slot_id: str, index: int, parent: str = "hotplate_01") -> StationSlot:
    return StationSlot(
        id=slot_id,
        display_name=slot_id,
        parent_station_id=parent,
        slot_index=index,
    )


def registry() -> StationSlotRegistry:
    stations = StationRegistry()
    stations.add(Station(id="hotplate_01", display_name="HP01", station_type="hotplate"))
    stations.add(Station(id="hotplate_02", display_name="HP02", station_type="hotplate"))
    return StationSlotRegistry(stations)


def test_slot_registry_crud_list_and_station_ordering() -> None:
    slots = registry()
    second = slot("hotplate_01.slot_02", 2)
    first = slot("hotplate_01.slot_01", 1)
    other = slot("hotplate_02.slot_01", 1, "hotplate_02")
    slots.add(second)
    slots.add(other)
    slots.add(first)
    assert slots.get(first.id) is first
    assert slots.contains(first.id)
    assert slots.list_by_station("hotplate_01") == (first, second)
    assert slots.list_all() == (first, second, other)
    assert slots.remove(first.id) is first


def test_slot_registry_rejects_duplicate_slot_id() -> None:
    slots = registry()
    slots.add(slot("hotplate_01.slot_01", 1))
    with pytest.raises(DuplicateResourceError):
        slots.add(slot("hotplate_01.slot_01", 1))


def test_slot_registry_rejects_duplicate_index_with_distinct_valid_id() -> None:
    slots = registry()
    slots.add(slot("hotplate_01.slot_01", 1))
    with pytest.raises(DuplicateSlotIndexError):
        slots.add(slot("hotplate_01.slot_001", 1))


def test_slot_registry_rejects_missing_parent() -> None:
    slots = registry()
    with pytest.raises(ResourceNotFoundError, match="station"):
        slots.add(slot("storage_01.slot_01", 1, "storage_01"))


def test_slot_registry_missing_slot_is_explicit() -> None:
    slots = registry()
    with pytest.raises(ResourceNotFoundError, match="station slot"):
        slots.get("hotplate_01.slot_99")
    with pytest.raises(ResourceNotFoundError, match="station slot"):
        slots.remove("hotplate_01.slot_99")


def test_slot_registry_rejects_occupied_slot_removal() -> None:
    slots = registry()
    occupied = slot("hotplate_01.slot_01", 1)
    occupied._add_occupant("sample_001")
    slots.add(occupied)
    with pytest.raises(StationOccupiedError, match="occupied slot"):
        slots.remove(occupied.id)
