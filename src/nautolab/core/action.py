"""Declarative recipe action model with no execution behavior."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._validation import (
    validate_identifier,
    validate_slot_id,
    validate_station_instance_id,
)
from .enums import ActionDefinitionState, ActionType, AllocationMode
from .errors import InvalidActionError


_PHASE_1A_DEFINED_TYPES = frozenset({ActionType.MOVE_SAMPLE, ActionType.WAIT})


@dataclass(frozen=True, slots=True)
class MoveDestination:
    """One unambiguous destination intent for future resource resolution."""

    exact_slot_id: str | None = None
    exact_station_id: str | None = None
    station_type: str | None = None

    def __post_init__(self) -> None:
        specified = tuple(
            value
            for value in (self.exact_slot_id, self.exact_station_id, self.station_type)
            if value is not None
        )
        if len(specified) != 1:
            raise InvalidActionError(
                "move destination must specify exactly one of exact_slot_id, "
                "exact_station_id, or station_type"
            )
        if self.exact_slot_id is not None:
            object.__setattr__(self, "exact_slot_id", validate_slot_id(self.exact_slot_id))
        if self.exact_station_id is not None:
            object.__setattr__(
                self,
                "exact_station_id",
                validate_station_instance_id(self.exact_station_id),
            )
        if self.station_type is not None:
            object.__setattr__(
                self,
                "station_type",
                validate_identifier(self.station_type, field_name="station_type"),
            )

    @property
    def allocation_mode(self) -> AllocationMode:
        """Return the declared resolution level without resolving resources."""
        if self.exact_slot_id is not None:
            return AllocationMode.EXACT_SLOT
        if self.exact_station_id is not None:
            return AllocationMode.EXACT_STATION
        return AllocationMode.STATION_TYPE

    def to_dict(self) -> dict[str, str | None]:
        """Return a serialization-friendly destination declaration."""
        return {
            "allocation_mode": self.allocation_mode.value,
            "exact_slot_id": self.exact_slot_id,
            "exact_station_id": self.exact_station_id,
            "station_type": self.station_type,
        }


@dataclass(slots=True)
class Action:
    """A serialization-friendly declaration of experimental intent.

    Actions deliberately have no ``execute`` or ``run`` method. Destination
    intent is declared here; resource resolution remains Phase 1B work.
    """

    id: str
    action_type: ActionType
    sample_id: str | None = None
    source_slot_id: str | None = None
    destination: MoveDestination | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.id = validate_identifier(self.id)
        self.action_type = ActionType(self.action_type)
        if self.sample_id is not None:
            self.sample_id = validate_identifier(self.sample_id, field_name="sample_id")
        if self.source_slot_id is not None:
            self.source_slot_id = validate_slot_id(self.source_slot_id)
        self.parameters = dict(self.parameters)
        self.metadata = dict(self.metadata)
        self._validate_declaration()

    @property
    def definition_state(self) -> ActionDefinitionState:
        """Report schema support, never runtime executability."""
        if self.action_type in _PHASE_1A_DEFINED_TYPES:
            return ActionDefinitionState.DEFINED
        return ActionDefinitionState.NOT_IMPLEMENTED

    def _validate_declaration(self) -> None:
        if self.action_type is ActionType.MOVE_SAMPLE:
            missing: list[str] = []
            if self.sample_id is None:
                missing.append("sample_id")
            if self.destination is None:
                missing.append("destination")
            if missing:
                raise InvalidActionError(
                    f"MOVE_SAMPLE action {self.id!r} is missing: {', '.join(missing)}"
                )
            if not isinstance(self.destination, MoveDestination):
                raise InvalidActionError("MOVE_SAMPLE destination must be MoveDestination")
            if (
                self.source_slot_id is not None
                and self.destination.exact_slot_id == self.source_slot_id
            ):
                raise InvalidActionError("MOVE_SAMPLE source and exact destination must differ")
        elif self.destination is not None:
            raise InvalidActionError("destination is valid only for MOVE_SAMPLE actions")

        if self.action_type is ActionType.WAIT and "duration_seconds" in self.parameters:
            duration = self.parameters["duration_seconds"]
            if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration < 0:
                raise InvalidActionError("WAIT duration_seconds must be a non-negative number")

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/YAML-friendly action data."""
        return {
            "id": self.id,
            "action_type": self.action_type.value,
            "definition_state": self.definition_state.value,
            "sample_id": self.sample_id,
            "source_slot_id": self.source_slot_id,
            "destination": self.destination.to_dict() if self.destination else None,
            "parameters": dict(self.parameters),
            "metadata": dict(self.metadata),
        }
