"""Small, stable state vocabularies used by Phase 1A domain models."""

from enum import StrEnum


class SampleStatus(StrEnum):
    """High-level lifecycle state of a sample."""

    READY = "READY"
    IN_PROCESS = "IN_PROCESS"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    DISABLED = "DISABLED"


class SampleHistoryEventType(StrEnum):
    """Canonical sample history event types created by the resource layer."""

    PLACED = "PLACED"
    RELOCATED = "RELOCATED"
    REMOVED = "REMOVED"
    STATUS_CHANGED = "STATUS_CHANGED"


class DeviceImplementationState(StrEnum):
    """Truthful implementation availability independent of connection state."""

    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    SIMULATED = "SIMULATED"
    REAL_AVAILABLE = "REAL_AVAILABLE"
    ERROR = "ERROR"


class DeviceConnectionState(StrEnum):
    """Connection lifecycle independent of implementation availability."""

    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"


class ActionType(StrEnum):
    """Declarative action vocabulary; no member is executable in Phase 1A."""

    MOVE_SAMPLE = "MOVE_SAMPLE"
    WAIT = "WAIT"
    HEAT = "HEAT"
    SPIN = "SPIN"
    ACQUIRE_SPECTRUM = "ACQUIRE_SPECTRUM"
    CAPTURE_IMAGE = "CAPTURE_IMAGE"
    MEASURE_IV = "MEASURE_IV"
    VISION_LOCATE = "VISION_LOCATE"


class ActionDefinitionState(StrEnum):
    """Whether Phase 1A formally supports an action's declaration schema."""

    DEFINED = "DEFINED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class AllocationMode(StrEnum):
    """Declarative destination intent; resolution is deferred to Phase 1B."""

    EXACT_SLOT = "EXACT_SLOT"
    EXACT_STATION = "EXACT_STATION"
    STATION_TYPE = "STATION_TYPE"


class WorkflowStatus(StrEnum):
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class WorkflowStepStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ABORTED = "ABORTED"


class ExecutionMode(StrEnum):
    SIMULATION = "SIMULATION"
    REAL = "REAL"
