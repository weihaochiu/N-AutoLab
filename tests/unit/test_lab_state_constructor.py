"""Regression tests for LabState registry dependency injection."""

from nautolab.core import Device, Sample, Station
from nautolab.resources import (
    DeviceRegistry,
    LabState,
    SampleRegistry,
    StationRegistry,
)


def test_empty_injected_registries_preserve_identity() -> None:
    samples = SampleRegistry()
    stations = StationRegistry()
    devices = DeviceRegistry()
    state = LabState(samples=samples, stations=stations, devices=devices)
    assert state.samples is samples
    assert state.stations is stations
    assert state.devices is devices
    assert state.slots.station_registry is stations


def test_prepopulated_injected_registries_preserve_identity_and_resources() -> None:
    samples = SampleRegistry()
    samples.add(Sample(id="sample_001", name="Sample 001"))
    stations = StationRegistry()
    stations.add(Station(id="storage_01", display_name="Storage", station_type="storage"))
    devices = DeviceRegistry()
    devices.add(Device(id="device_01", display_name="Device", device_type="generic_device"))

    state = LabState(samples=samples, stations=stations, devices=devices)

    assert state.samples is samples
    assert state.samples.get("sample_001").name == "Sample 001"
    assert state.stations is stations
    assert state.stations.get("storage_01").station_type == "storage"
    assert state.devices is devices
    assert state.devices.get("device_01").device_type == "generic_device"
    assert state.slots.station_registry is stations
