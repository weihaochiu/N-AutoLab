from __future__ import annotations

from copy import deepcopy

import pytest

from nautolab.core import MoveDestination, ResourceResolutionError, Sample, Station, StationSlot
from nautolab.resources import LabState, ResourceResolver


def _lab() -> LabState:
    lab = LabState()
    for station in (
        Station("hotplate_02", "HP2", "hotplate"),
        Station("hotplate_01", "HP1", "hotplate"),
    ):
        lab.stations.add(station)
        for index in range(1, 4):
            lab.slots.add(StationSlot(
                f"{station.id}.slot_{index:02d}", f"S{index}", station.id, index
            ))
    return lab


def test_modes_are_deterministic_and_side_effect_free() -> None:
    lab = _lab()
    lab.samples.add(Sample("sample_001", "One"))
    lab.place_sample("sample_001", "hotplate_01.slot_01")
    before = deepcopy([(s.id, s.occupant_ids) for s in lab.slots.list_all()])
    resolver = ResourceResolver(lab)
    assert resolver.resolve(MoveDestination(exact_slot_id="hotplate_02.slot_03")).id == "hotplate_02.slot_03"
    assert resolver.resolve(MoveDestination(exact_station_id="hotplate_01")).id == "hotplate_01.slot_02"
    assert resolver.resolve(MoveDestination(station_type="hotplate")).id == "hotplate_01.slot_02"
    assert [(s.id, s.occupant_ids) for s in lab.slots.list_all()] == before


@pytest.mark.parametrize("kind", ["disabled_slot", "disabled_station", "full", "missing"])
def test_exact_slot_fails_closed_without_substitution(kind: str) -> None:
    lab = _lab()
    target = "hotplate_01.slot_01"
    if kind == "disabled_slot": lab.slots.get(target).enabled = False
    if kind == "disabled_station": lab.stations.get("hotplate_01").enabled = False
    if kind == "full":
        lab.samples.add(Sample("sample_001", "One")); lab.place_sample("sample_001", target)
    if kind == "missing": target = "hotplate_09.slot_01"
    with pytest.raises(ResourceResolutionError):
        ResourceResolver(lab).resolve(MoveDestination(exact_slot_id=target))


def test_capacity_greater_than_one_is_available_until_full() -> None:
    lab = LabState()
    lab.stations.add(Station("storage_01", "Storage", "storage"))
    lab.slots.add(StationSlot("storage_01.slot_01", "S1", "storage_01", 1, capacity=2))
    lab.samples.add(Sample("sample_001", "One")); lab.place_sample("sample_001", "storage_01.slot_01")
    assert ResourceResolver(lab).resolve(MoveDestination(exact_slot_id="storage_01.slot_01")).remaining_capacity == 1
    lab.samples.add(Sample("sample_002", "Two")); lab.place_sample("sample_002", "storage_01.slot_01")
    with pytest.raises(ResourceResolutionError):
        ResourceResolver(lab).resolve(MoveDestination(exact_slot_id="storage_01.slot_01"))


def test_unknown_type_and_full_station_fail() -> None:
    lab = _lab()
    resolver = ResourceResolver(lab)
    with pytest.raises(ResourceResolutionError, match="not registered"):
        resolver.resolve(MoveDestination(station_type="unknown"))
    occupancy = {slot.id: slot.capacity for slot in lab.slots.list_all()}
    with pytest.raises(ResourceResolutionError, match="no available"):
        resolver.resolve(MoveDestination(exact_station_id="hotplate_01"), occupancy=occupancy)
