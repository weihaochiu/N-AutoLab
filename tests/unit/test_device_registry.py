"""Tests for DeviceRegistry behavior."""

import pytest

from nautolab.core import Device, DuplicateResourceError, ResourceNotFoundError
from nautolab.resources import DeviceRegistry


def device(device_id: str) -> Device:
    return Device(id=device_id, display_name=device_id, device_type="generic_device")


def test_device_registry_crud_contract() -> None:
    registry = DeviceRegistry()
    item = device("device_01")
    registry.add(item)
    assert registry.get("device_01") is item
    assert registry.list_all() == (item,)
    assert registry.contains("device_01")
    assert registry.remove("device_01") is item
    assert not registry.contains("device_01")


def test_device_registry_rejects_duplicate_id() -> None:
    registry = DeviceRegistry()
    registry.add(device("device_01"))
    with pytest.raises(DuplicateResourceError):
        registry.add(device("device_01"))


def test_device_registry_get_missing_is_explicit() -> None:
    with pytest.raises(ResourceNotFoundError, match="device"):
        DeviceRegistry().get("missing")
    with pytest.raises(ResourceNotFoundError, match="device"):
        DeviceRegistry().remove("missing")
