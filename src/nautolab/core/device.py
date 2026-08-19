"""Hardware-independent device description."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._validation import normalize_identifiers, validate_identifier, validate_non_empty_text
from .enums import DeviceConnectionState, DeviceImplementationState


@dataclass(slots=True)
class Device:
    """Declarative device identity and capability state without backend behavior."""

    id: str
    display_name: str
    device_type: str
    implementation_state: DeviceImplementationState = DeviceImplementationState.NOT_IMPLEMENTED
    connection_state: DeviceConnectionState = DeviceConnectionState.DISCONNECTED
    capabilities: tuple[str, ...] = ()
    backend_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.id = validate_identifier(self.id)
        self.display_name = validate_non_empty_text(self.display_name, field_name="display_name")
        self.device_type = validate_identifier(self.device_type, field_name="device_type")
        self.implementation_state = DeviceImplementationState(self.implementation_state)
        self.connection_state = DeviceConnectionState(self.connection_state)
        self.capabilities = normalize_identifiers(
            self.capabilities, field_name="device capability"
        )
        if self.backend_name is not None:
            self.backend_name = validate_identifier(self.backend_name, field_name="backend_name")
        self.metadata = dict(self.metadata)

    def has_capability(self, capability: str) -> bool:
        """Return whether this device declares a capability identifier."""
        return capability in self.capabilities

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/YAML-friendly device data."""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "device_type": self.device_type,
            "implementation_state": self.implementation_state.value,
            "connection_state": self.connection_state.value,
            "capabilities": list(self.capabilities),
            "backend_name": self.backend_name,
            "metadata": dict(self.metadata),
        }
