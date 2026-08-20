"""Tests for declarative Action destination intents."""

import pytest

from nautolab.core import (
    Action,
    ActionDefinitionState,
    AllocationMode,
    InvalidActionError,
    MoveDestination,
)


def test_move_sample_exact_slot_declaration() -> None:
    action = Action(
        id="move_001",
        action_type="MOVE_SAMPLE",
        sample_id="sample_001",
        source_slot_id="storage_01.slot_01",
        destination=MoveDestination(exact_slot_id="hotplate_02.slot_03"),
    )
    assert action.definition_state is ActionDefinitionState.DEFINED
    assert action.destination is not None
    assert action.destination.allocation_mode is AllocationMode.EXACT_SLOT
    assert not hasattr(action, "execute")
    assert not hasattr(action, "run")


@pytest.mark.parametrize(
    ("destination", "mode"),
    [
        (MoveDestination(exact_station_id="hotplate_02"), AllocationMode.EXACT_STATION),
        (MoveDestination(station_type="hotplate"), AllocationMode.STATION_TYPE),
    ],
)
def test_future_auto_allocation_intent_is_declarative_only(
    destination: MoveDestination, mode: AllocationMode
) -> None:
    assert destination.allocation_mode is mode
    assert not hasattr(destination, "resolve")


def test_destination_rejects_ambiguous_declaration() -> None:
    with pytest.raises(InvalidActionError, match="exactly one"):
        MoveDestination(
            exact_slot_id="hotplate_02.slot_03",
            station_type="hotplate",
        )


def test_move_sample_requires_all_references() -> None:
    with pytest.raises(InvalidActionError, match="destination"):
        Action(
            id="move_001",
            action_type="MOVE_SAMPLE",
            sample_id="sample_001",
            source_slot_id="storage_01.slot_01",
        )


def test_move_sample_requires_distinct_exact_slots() -> None:
    with pytest.raises(InvalidActionError, match="must differ"):
        Action(
            id="move_001",
            action_type="MOVE_SAMPLE",
            sample_id="sample_001",
            source_slot_id="storage_01.slot_01",
            destination=MoveDestination(exact_slot_id="storage_01.slot_01"),
        )


@pytest.mark.parametrize("duration", [-1, True, "five"])
def test_wait_rejects_invalid_duration(duration: object) -> None:
    with pytest.raises(InvalidActionError):
        Action(id="wait_001", action_type="WAIT", parameters={"duration_seconds": duration})


def test_future_action_is_explicitly_not_implemented() -> None:
    action = Action(id="heat_001", action_type="HEAT", parameters={"temperature_c": 100})
    assert action.definition_state is ActionDefinitionState.NOT_IMPLEMENTED


def test_action_serializes_destination_without_resolution() -> None:
    action = Action(
        id="move_001",
        action_type="MOVE_SAMPLE",
        sample_id="sample_001",
        source_slot_id="storage_01.slot_01",
        destination=MoveDestination(exact_station_id="hotplate_02"),
    )
    assert action.to_dict()["destination"] == {
        "allocation_mode": "EXACT_STATION",
        "exact_slot_id": None,
        "exact_station_id": "hotplate_02",
        "station_type": None,
    }
