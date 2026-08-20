"""User-defined recipe and recipe-step domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from ._validation import validate_bool, validate_identifier, validate_non_empty_text
from .action import Action
from .errors import InvalidRecipeError


@dataclass(frozen=True, slots=True)
class RecipeStep:
    """An ordered recipe row independent of GUI representation."""

    step_id: str
    order: int
    action: Action
    enabled: bool = True
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_id", validate_identifier(self.step_id, field_name="step_id"))
        if isinstance(self.order, bool) or not isinstance(self.order, int) or self.order < 0:
            raise InvalidRecipeError("recipe step order must be a non-negative integer")
        if not isinstance(self.action, Action):
            raise InvalidRecipeError("recipe step action must be an Action")
        object.__setattr__(
            self,
            "enabled",
            validate_bool(self.enabled, field_name=f"recipe step {self.step_id} enabled"),
        )
        object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/YAML-friendly recipe-step data."""
        return {
            "step_id": self.step_id,
            "order": self.order,
            "action": self.action.to_dict(),
            "enabled": self.enabled,
            "description": self.description,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class Recipe:
    """A user-defined experiment description with no execution behavior."""

    id: str
    name: str
    steps: Sequence[RecipeStep] = ()
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.id = validate_identifier(self.id)
        self.name = validate_non_empty_text(self.name, field_name="name")
        self.description = self.description.strip()
        self.metadata = dict(self.metadata)
        self.steps = self._validated_steps(self.steps)

    @staticmethod
    def _validated_steps(steps: Sequence[RecipeStep]) -> tuple[RecipeStep, ...]:
        normalized = tuple(steps)
        if not all(isinstance(step, RecipeStep) for step in normalized):
            raise InvalidRecipeError("all recipe steps must be RecipeStep instances")
        step_ids = [step.step_id for step in normalized]
        if len(step_ids) != len(set(step_ids)):
            raise InvalidRecipeError("recipe step identifiers must be unique")
        orders = [step.order for step in normalized]
        if len(orders) != len(set(orders)):
            raise InvalidRecipeError("recipe step order values must be unique")
        return tuple(sorted(normalized, key=lambda step: step.order))

    def add_step(self, step: RecipeStep) -> None:
        """Append a step while preserving identifier/order invariants."""
        self.steps = self._validated_steps((*self.steps, step))

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/YAML-friendly recipe data."""
        return {
            "id": self.id,
            "name": self.name,
            "steps": [step.to_dict() for step in self.steps],
            "description": self.description,
            "metadata": dict(self.metadata),
        }
