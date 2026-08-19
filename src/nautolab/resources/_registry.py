"""Shared in-memory registry mechanics for Phase 1A resources."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Generic, Protocol, TypeVar

from nautolab.core import DuplicateResourceError, ResourceNotFoundError


class IdentifiedResource(Protocol):
    """Structural contract required by a registry."""

    id: str


ResourceT = TypeVar("ResourceT", bound=IdentifiedResource)


class ResourceRegistry(Generic[ResourceT]):
    """Small deterministic in-memory registry keyed by stable identifiers."""

    resource_label = "resource"

    def __init__(self) -> None:
        self._items: dict[str, ResourceT] = {}

    def add(self, resource: ResourceT) -> None:
        """Register a resource, rejecting duplicate identifiers."""
        if resource.id in self._items:
            raise DuplicateResourceError(
                f"{self.resource_label} {resource.id!r} is already registered"
            )
        self._items[resource.id] = resource

    def get(self, resource_id: str) -> ResourceT:
        """Return a registered resource or raise an explicit domain error."""
        try:
            return self._items[resource_id]
        except KeyError as exc:
            raise ResourceNotFoundError(
                f"{self.resource_label} {resource_id!r} is not registered"
            ) from exc

    def remove(self, resource_id: str) -> ResourceT:
        """Remove and return a registered resource."""
        try:
            return self._items.pop(resource_id)
        except KeyError as exc:
            raise ResourceNotFoundError(
                f"{self.resource_label} {resource_id!r} is not registered"
            ) from exc

    def contains(self, resource_id: str) -> bool:
        """Return whether an identifier is registered."""
        return resource_id in self._items

    def list_all(self) -> tuple[ResourceT, ...]:
        """Return resources in deterministic insertion order."""
        return tuple(self._items.values())

    def __contains__(self, resource_id: object) -> bool:
        return isinstance(resource_id, str) and self.contains(resource_id)

    def __iter__(self) -> Iterator[ResourceT]:
        return iter(self._items.values())

    def __len__(self) -> int:
        return len(self._items)
