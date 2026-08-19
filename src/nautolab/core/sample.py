"""General-purpose sample domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from ._validation import validate_identifier, validate_non_empty_text
from .enums import SampleHistoryEventType, SampleStatus


@dataclass(frozen=True, slots=True)
class SampleHistoryEntry:
    """Lightweight record of a sample state or location transition."""

    event_type: SampleHistoryEventType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str | None = None
    destination: str | None = None
    note: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/YAML-friendly history data."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "destination": self.destination,
            "note": self.note,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class Sample:
    """A material-agnostic laboratory sample.

    ``current_location`` is read-only to callers. The resource layer updates it
    together with station occupancy through ``LabState`` operations.
    """

    id: str
    name: str
    sample_type: str | None = None
    status: SampleStatus = SampleStatus.READY
    metadata: dict[str, Any] = field(default_factory=dict)
    _current_location: str | None = field(default=None, init=False, repr=False)
    _history: list[SampleHistoryEntry] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.id = validate_identifier(self.id)
        self.name = validate_non_empty_text(self.name, field_name="name")
        if self.sample_type is not None:
            self.sample_type = validate_identifier(self.sample_type, field_name="sample_type")
        self.status = SampleStatus(self.status)
        self.metadata = dict(self.metadata)

    @property
    def current_location(self) -> str | None:
        """Return the canonical station identifier, or ``None`` when unplaced."""
        return self._current_location

    @property
    def history(self) -> tuple[SampleHistoryEntry, ...]:
        """Return an immutable view of sample history."""
        return tuple(self._history)

    def rename(self, name: str) -> None:
        """Change the display name without changing stable identity."""
        self.name = validate_non_empty_text(name, field_name="name")

    def set_status(
        self,
        status: SampleStatus,
        *,
        note: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Set sample status and append a lightweight history entry."""
        new_status = SampleStatus(status)
        old_status = self.status
        self.status = new_status
        self._history.append(
            SampleHistoryEntry(
                event_type=SampleHistoryEventType.STATUS_CHANGED,
                source=old_status.value,
                destination=new_status.value,
                note=note,
                metadata=dict(metadata or {}),
            )
        )

    def _record_location_transition(
        self,
        *,
        event_type: SampleHistoryEventType,
        source: str | None,
        destination: str | None,
        note: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Update location after resource-layer validation.

        This is intentionally private. ``LabState`` is the canonical caller.
        """
        self._current_location = destination
        self._history.append(
            SampleHistoryEntry(
                event_type=event_type,
                source=source,
                destination=destination,
                note=note,
                metadata=dict(metadata or {}),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/YAML-friendly sample data."""
        return {
            "id": self.id,
            "name": self.name,
            "sample_type": self.sample_type,
            "current_location": self.current_location,
            "status": self.status.value,
            "metadata": dict(self.metadata),
            "history": [entry.to_dict() for entry in self.history],
        }
