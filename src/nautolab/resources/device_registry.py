"""Device registry."""

from nautolab.core import Device

from ._registry import ResourceRegistry


class DeviceRegistry(ResourceRegistry[Device]):
    """Authoritative lookup collection for device descriptions."""

    resource_label = "device"
