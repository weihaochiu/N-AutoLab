"""Tests for declarative Action schemas."""

import pytest

from nautolab.core import (
    Action,
    ActionDefinitionState,
    ActionType,
    InvalidActionError,
)


def test_move_sample_action_declares_intent() -> None:
    action = Action(
        id="move_001",
        action_type=ActionType.MOVE_SAMPLE,
        sample_id="sample_001",
        source_station_id="storage_s1",
        destination_station_id="hotplate",
    )
    assert action.definition_state is ActionDefinitionState.DEFINED
    assert not hasattr(action, "execute")
    assert not hasattr(action, "run")


def test_move_sample_requires_all_references() -> None:
    with pytest.raises(InvalidActionError, match="destination_station_id"):
        Action(
            id="move_001",
            action_type="MOVE_SAMPLE",
            sample_id="sample_001",
            source_station_id="storage_s1",
        )


def test_move_sample_requires_distinct_stations() -> None:
    with pytest.raises(InvalidActionError, match="must differ"):
        Action(
            id="move_001",
            action_type="MOVE_SAMPLE",
            sample_id="sample_001",
            source_station_id="storage_s1",
            destination_station_id="storage_s1",
        )


@pytest.mark.parametrize("duration", [-1, True, "five"])
def test_wait_rejects_invalid_duration(duration: object) -> None:
    with pytest.raises(InvalidActionError):
        Action(id="wait_001", action_type="WAIT", parameters={"duration_seconds": duration})


def test_future_action_is_explicitly_not_implemented() -> None:
    action = Action(id="heat_001", action_type="HEAT", parameters={"temperature_c": 100})
    assert action.definition_state is ActionDefinitionState.NOT_IMPLEMENTED


def test_action_to_dict_is_gui_independent() -> None:
    data = Action(id="wait_001", action_type="WAIT", parameters={"duration_seconds": 2}).to_dict()
    assert data["action_type"] == "WAIT"
    assert data["parameters"] == {"duration_seconds": 2}
