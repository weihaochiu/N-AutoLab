"""Integration tests for the portable demo laboratory configuration."""

from pathlib import Path

from nautolab.core import DeviceConnectionState, DeviceImplementationState
from nautolab.resources import load_lab_config


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_demo_lab_loads_expected_resources() -> None:
    state = load_lab_config(REPOSITORY_ROOT / "config" / "demo_lab.yaml")
    assert {station.id for station in state.stations.list_all()} == {
        "storage_s1",
        "hotplate",
        "spin_coater",
        "spectrometer",
    }
    assert len(state.devices) == 5
    assert len(state.samples) == 1


def test_demo_sample_initial_state_is_consistent() -> None:
    state = load_lab_config(REPOSITORY_ROOT / "config" / "demo_lab.yaml")
    sample = state.samples.get("sample_001")
    assert sample.current_location == "storage_s1"
    assert state.stations.get("storage_s1").occupant_ids == ("sample_001",)
    assert state.stations.get("hotplate").occupant_ids == ()
    assert state.stations.get("spin_coater").occupant_ids == ()
    assert state.stations.get("spectrometer").occupant_ids == ()


def test_demo_devices_never_claim_ready_or_connected() -> None:
    state = load_lab_config(REPOSITORY_ROOT / "config" / "demo_lab.yaml")
    for device in state.devices:
        assert device.implementation_state is DeviceImplementationState.NOT_IMPLEMENTED
        assert device.connection_state is DeviceConnectionState.DISCONNECTED


def test_demo_config_uses_semantic_pose_references_only() -> None:
    state = load_lab_config(REPOSITORY_ROOT / "config" / "demo_lab.yaml")
    for station in state.stations:
        assert station.pose_reference is not None
        assert station.pose_reference.endswith("_pose")


def test_demo_sample_can_relocate_twice_through_canonical_state_api() -> None:
    state = load_lab_config(REPOSITORY_ROOT / "config" / "demo_lab.yaml")
    state.relocate_sample("sample_001", "storage_s1", "hotplate")
    assert state.samples.get("sample_001").current_location == "hotplate"
    assert state.stations.get("storage_s1").occupant_ids == ()
    assert state.stations.get("hotplate").occupant_ids == ("sample_001",)

    state.relocate_sample("sample_001", "hotplate", "spin_coater")
    assert state.samples.get("sample_001").current_location == "spin_coater"
    assert state.stations.get("hotplate").occupant_ids == ()
    assert state.stations.get("spin_coater").occupant_ids == ("sample_001",)
