"""Tests for hardware-independent Device descriptions."""

from nautolab.core import (
    Device,
    DeviceConnectionState,
    DeviceImplementationState,
)


def test_device_truthfully_defaults_to_not_implemented() -> None:
    device = Device(id="robot_01", display_name="Robot", device_type="robot")
    assert device.implementation_state is DeviceImplementationState.NOT_IMPLEMENTED
    assert device.connection_state is DeviceConnectionState.DISCONNECTED


def test_device_capabilities_are_declarative() -> None:
    device = Device(
        id="hotplate_01",
        display_name="Hot Plate",
        device_type="hot_plate",
        capabilities=("heat", "heat"),
    )
    assert device.capabilities == ("heat",)
    assert device.has_capability("heat")


def test_device_accepts_simulated_state_without_backend_execution() -> None:
    device = Device(
        id="camera_01",
        display_name="Camera",
        device_type="camera",
        implementation_state="SIMULATED",
        backend_name="demo_camera_backend",
    )
    assert device.implementation_state is DeviceImplementationState.SIMULATED
    assert device.backend_name == "demo_camera_backend"
    assert not hasattr(device, "connect")


def test_device_accepts_real_available_and_connected_states_as_data() -> None:
    device = Device(
        id="smu_01",
        display_name="SMU",
        device_type="smu",
        implementation_state="REAL_AVAILABLE",
        connection_state="CONNECTED",
    )
    assert device.implementation_state is DeviceImplementationState.REAL_AVAILABLE
    assert device.connection_state is DeviceConnectionState.CONNECTED
    assert not hasattr(device, "measure")


def test_device_serialization_uses_state_values() -> None:
    data = Device(id="smu_01", display_name="SMU", device_type="smu").to_dict()
    assert data["implementation_state"] == "NOT_IMPLEMENTED"
    assert data["connection_state"] == "DISCONNECTED"
