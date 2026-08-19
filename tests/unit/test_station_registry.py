"""Tests for StationRegistry behavior."""

import pytest

from nautolab.core import DuplicateResourceError, ResourceNotFoundError, Station
from nautolab.resources import StationRegistry


def station(station_id: str) -> Station:
    return Station(id=station_id, display_name=station_id, station_type="storage", capacity=1)


def test_station_registry_is_deterministic() -> None:
    registry = StationRegistry()
    registry.add(station("station_a"))
    registry.add(station("station_b"))
    assert [item.id for item in registry] == ["station_a", "station_b"]
    assert "station_a" in registry
    assert registry.get("station_a").id == "station_a"
    removed = registry.remove("station_a")
    assert removed.id == "station_a"
    assert not registry.contains("station_a")


def test_station_registry_rejects_duplicate_id() -> None:
    registry = StationRegistry()
    registry.add(station("station_a"))
    with pytest.raises(DuplicateResourceError):
        registry.add(station("station_a"))


def test_station_registry_remove_missing_is_explicit() -> None:
    registry = StationRegistry()
    with pytest.raises(ResourceNotFoundError, match="station"):
        registry.remove("missing")
    with pytest.raises(ResourceNotFoundError, match="station"):
        registry.get("missing")
