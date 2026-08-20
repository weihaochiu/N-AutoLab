"""Tests for multi-instance StationRegistry queries."""

import pytest

from nautolab.core import DuplicateResourceError, ResourceNotFoundError, Station
from nautolab.resources import StationRegistry


def station(station_id: str, station_type: str) -> Station:
    return Station(id=station_id, display_name=station_id, station_type=station_type)


def test_station_registry_crud_and_canonical_order() -> None:
    registry = StationRegistry()
    registry.add(station("storage_02", "storage"))
    registry.add(station("storage_01", "storage"))
    assert [item.id for item in registry.list_all()] == ["storage_01", "storage_02"]
    assert registry.get("storage_01").id == "storage_01"
    assert registry.contains("storage_01")
    assert registry.remove("storage_01").id == "storage_01"


def test_station_registry_lists_same_type_deterministically() -> None:
    registry = StationRegistry()
    registry.add(station("hotplate_02", "hotplate"))
    registry.add(station("spin_coater_01", "spin_coater"))
    registry.add(station("hotplate_01", "hotplate"))
    assert [item.id for item in registry.list_by_type("hotplate")] == [
        "hotplate_01",
        "hotplate_02",
    ]


def test_station_registry_rejects_duplicate_and_missing_ids() -> None:
    registry = StationRegistry()
    registry.add(station("storage_01", "storage"))
    with pytest.raises(DuplicateResourceError):
        registry.add(station("storage_01", "storage"))
    with pytest.raises(ResourceNotFoundError):
        registry.get("missing")
    with pytest.raises(ResourceNotFoundError):
        registry.remove("missing")
