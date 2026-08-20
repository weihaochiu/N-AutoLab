"""Integration tests for the multi-station, multi-slot demo laboratory."""

from pathlib import Path

from nautolab.core import DeviceConnectionState, DeviceImplementationState
from nautolab.resources import load_lab_config


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def load_demo():
    return load_lab_config(REPOSITORY_ROOT / "config" / "demo_lab.yaml")


def test_demo_lab_loads_expected_hierarchy() -> None:
    state = load_demo()
    assert [station.id for station in state.stations.list_all()] == [
        "hotplate_01",
        "hotplate_02",
        "spectrometer_01",
        "spin_coater_01",
        "storage_01",
    ]
    assert len(state.slots) == 12
    assert len(state.devices) == 6
    assert len(state.samples) == 4
    assert len(state.slots.list_by_station("storage_01")) == 4
    assert len(state.slots.list_by_station("hotplate_01")) == 3
    assert len(state.slots.list_by_station("spin_coater_01")) == 1


def test_demo_initial_slot_state_and_station_aggregates_are_consistent() -> None:
    state = load_demo()
    expected = {
        "sample_001": "storage_01.slot_01",
        "sample_002": "hotplate_01.slot_01",
        "sample_003": "hotplate_01.slot_02",
        "sample_004": "hotplate_02.slot_01",
    }
    for sample_id, slot_id in expected.items():
        assert state.samples.get(sample_id).current_location == slot_id
        assert state.slots.get(slot_id).occupant_ids == (sample_id,)
    assert state.station_occupancy("hotplate_01") == 2
    assert state.station_total_capacity("hotplate_01") == 3
    assert state.station_occupancy("hotplate_02") == 1


def test_demo_has_two_independent_hotplate_instances() -> None:
    state = load_demo()
    assert [station.id for station in state.stations.list_by_type("hotplate")] == [
        "hotplate_01",
        "hotplate_02",
    ]
    assert [slot.id for slot in state.slots.list_by_station("hotplate_01")] == [
        "hotplate_01.slot_01",
        "hotplate_01.slot_02",
        "hotplate_01.slot_03",
    ]
    assert [slot.id for slot in state.slots.list_by_station("hotplate_02")] == [
        "hotplate_02.slot_01",
        "hotplate_02.slot_02",
        "hotplate_02.slot_03",
    ]


def test_demo_devices_never_claim_ready_or_connected() -> None:
    state = load_demo()
    for device in state.devices:
        assert device.implementation_state is DeviceImplementationState.NOT_IMPLEMENTED
        assert device.connection_state is DeviceConnectionState.DISCONNECTED


def test_demo_uses_slot_semantic_poses_and_display_shorthand() -> None:
    state = load_demo()
    for slot in state.slots:
        assert slot.pose_reference is not None
        assert slot.pose_reference.endswith(f"slot_{slot.slot_index:02d}")
        assert "." not in slot.display_name


def test_demo_exact_slot_move_preserves_other_hotplate() -> None:
    state = load_demo()
    state.relocate_sample(
        "sample_001", "storage_01.slot_01", "hotplate_02.slot_03"
    )
    assert state.samples.get("sample_001").current_location == "hotplate_02.slot_03"
    assert state.station_occupant_ids("hotplate_01") == ("sample_002", "sample_003")
    assert state.station_occupant_ids("hotplate_02") == ("sample_004", "sample_001")


def test_demo_availability_queries_match_current_state() -> None:
    state = load_demo()
    assert [slot.id for slot in state.available_slots_for_station("hotplate_01")] == [
        "hotplate_01.slot_03"
    ]
    assert [
        slot.id for slot in state.available_slots_for_station_type("hotplate")
    ] == [
        "hotplate_01.slot_03",
        "hotplate_02.slot_02",
        "hotplate_02.slot_03",
    ]
