"""Declarative recipe action model with no execution behavior."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._validation import validate_identifier
from .enums import ActionDefinitionState, ActionType
from .errors import InvalidActionError


_PHASE_1A_DEFINED_TYPES = frozenset({ActionType.MOVE_SAMPLE, ActionType.WAIT})


@dataclass(slots=True)
class Action:
    """A serialization-friendly declaration of experimental intent.

    Actions deliberately have no ``execute`` or ``run`` method.
    """

    id: str
    action_type: ActionType
    sample_id: str | None = None
    source_station_id: str | None = None
    destination_station_id: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.id = validate_identifier(self.id)
        self.action_type = ActionType(self.action_type)
        for field_name in ("sample_id", "source_station_id", "destination_station_id"):
            value = getattr(self, field_name)
            if value is not None:
                setattr(self, field_name, validate_identifier(value, field_name=field_name))
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
            required = {
                "sample_id": self.sample_id,
                "source_station_id": self.source_station_id,
                "destination_station_id": self.destination_station_id,
            }
            missing = [name for name, value in required.items() if value is None]
            if missing:
                raise InvalidActionError(
                    f"MOVE_SAMPLE action {self.id!r} is missing: {', '.join(missing)}"
                )
            if self.source_station_id == self.destination_station_id:
                raise InvalidActionError("MOVE_SAMPLE source and destination must differ")
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
            "source_station_id": self.source_station_id,
            "destination_station_id": self.destination_station_id,
            "parameters": dict(self.parameters),
            "metadata": dict(self.metadata),
        }
