"""Small shared validators for pure domain objects."""

from __future__ import annotations

import re

from .errors import InvalidIdentifierError


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


def validate_identifier(value: str, *, field_name: str = "id") -> str:
    """Return a valid lowercase snake_case identifier or raise a domain error."""
    if not isinstance(value, str) or not _IDENTIFIER_PATTERN.fullmatch(value):
        raise InvalidIdentifierError(
            f"{field_name} must be a lowercase snake_case identifier; got {value!r}"
        )
    return value


def validate_non_empty_text(value: str, *, field_name: str) -> str:
    """Return stripped non-empty text or raise a domain error."""
    if not isinstance(value, str) or not value.strip():
        raise InvalidIdentifierError(f"{field_name} must be non-empty text")
    return value.strip()


def normalize_identifiers(values: tuple[str, ...] | list[str], *, field_name: str) -> tuple[str, ...]:
    """Validate identifiers while preserving input order and removing duplicates."""
    normalized: list[str] = []
    for value in values:
        identifier = validate_identifier(value, field_name=field_name)
        if identifier not in normalized:
            normalized.append(identifier)
    return tuple(normalized)
