"""Small shared validators for pure domain objects."""

from __future__ import annotations

import re

from .errors import InvalidBooleanError, InvalidIdentifierError


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_STATION_INSTANCE_PATTERN = re.compile(
    r"^(?P<station_type>[a-z][a-z0-9]*(?:_[a-z0-9]+)*)_(?P<instance>[0-9]{2,})$"
)
_SLOT_ID_PATTERN = re.compile(
    r"^(?P<parent>[a-z][a-z0-9]*(?:_[a-z0-9]+)*_[0-9]{2,})"
    r"\.slot_(?P<slot_index>[0-9]{2,})$"
)


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


def validate_bool(value: bool, *, field_name: str) -> bool:
    """Return an actual Boolean and reject truthy/falsy substitutes."""
    if type(value) is not bool:
        raise InvalidBooleanError(
            f"{field_name} must be a Boolean true/false value; got {value!r}"
        )
    return value


def normalize_identifiers(values: tuple[str, ...] | list[str], *, field_name: str) -> tuple[str, ...]:
    """Validate identifiers while preserving input order and removing duplicates."""
    normalized: list[str] = []
    for value in values:
        identifier = validate_identifier(value, field_name=field_name)
        if identifier not in normalized:
            normalized.append(identifier)
    return tuple(normalized)


def validate_station_instance_id(value: str, *, station_type: str | None = None) -> str:
    """Validate ``<station_type>_<instance_number>`` canonical identity."""
    if not isinstance(value, str):
        raise InvalidIdentifierError(f"station id must be text; got {value!r}")
    match = _STATION_INSTANCE_PATTERN.fullmatch(value)
    if match is None:
        raise InvalidIdentifierError(
            "station id must use <station_type>_<instance_number> with a "
            f"two-or-more digit instance number; got {value!r}"
        )
    if station_type is not None and match.group("station_type") != station_type:
        raise InvalidIdentifierError(
            f"station id {value!r} does not match station_type {station_type!r}"
        )
    return value


def validate_slot_id(
    value: str,
    *,
    parent_station_id: str | None = None,
    slot_index: int | None = None,
) -> str:
    """Validate ``<station_id>.slot_<NN>`` canonical identity."""
    if not isinstance(value, str):
        raise InvalidIdentifierError(f"slot id must be text; got {value!r}")
    match = _SLOT_ID_PATTERN.fullmatch(value)
    if match is None:
        raise InvalidIdentifierError(
            f"slot id must use <station_id>.slot_<NN>; got {value!r}"
        )
    if parent_station_id is not None and match.group("parent") != parent_station_id:
        raise InvalidIdentifierError(
            f"slot id {value!r} does not belong to station {parent_station_id!r}"
        )
    if slot_index is not None and int(match.group("slot_index")) != slot_index:
        raise InvalidIdentifierError(
            f"slot id {value!r} does not match slot_index {slot_index}"
        )
    return value
