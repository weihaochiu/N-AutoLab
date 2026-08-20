"""Adversarial rollback tests for LabState location transactions."""

import pytest

from nautolab.core import Sample, Station, StationSlot
from nautolab.resources import LabState


def make_state() -> tuple[LabState, Sample, StationSlot, StationSlot]:
    state = LabState()
    state.stations.add(
        Station(id="storage_01", display_name="Storage", station_type="storage")
    )
    source = StationSlot(
        id="storage_01.slot_01",
        display_name="ST01-S01",
        parent_station_id="storage_01",
        slot_index=1,
    )
    destination = StationSlot(
        id="storage_01.slot_02",
        display_name="ST01-S02",
        parent_station_id="storage_01",
        slot_index=2,
    )
    state.slots.add(source)
    state.slots.add(destination)
    sample = Sample(id="sample_001", name="Sample")
    state.samples.add(sample)
    return state, sample, source, destination


def test_place_rolls_back_when_history_recording_fails_after_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, sample, source, _ = make_state()
    original_record = Sample._record_location_transition

    def fail_after_record(self: Sample, **kwargs: object) -> None:
        original_record(self, **kwargs)  # type: ignore[arg-type]
        raise RuntimeError("injected post-history failure")

    monkeypatch.setattr(Sample, "_record_location_transition", fail_after_record)
    with pytest.raises(RuntimeError, match="post-history"):
        state.place_sample(sample.id, source.id)

    assert source.occupant_ids == ()
    assert sample.current_location is None
    assert sample.history == ()


def test_remove_rolls_back_when_history_recording_fails_after_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, sample, source, _ = make_state()
    state.place_sample(sample.id, source.id)
    location_before = sample.current_location
    history_before = sample.history
    original_record = Sample._record_location_transition

    def fail_after_record(self: Sample, **kwargs: object) -> None:
        original_record(self, **kwargs)  # type: ignore[arg-type]
        raise RuntimeError("injected post-history failure")

    monkeypatch.setattr(Sample, "_record_location_transition", fail_after_record)
    with pytest.raises(RuntimeError, match="post-history"):
        state.remove_sample(sample.id)

    assert source.occupant_ids == (sample.id,)
    assert sample.current_location == location_before
    assert sample.history == history_before


def test_relocate_rolls_back_when_destination_fails_after_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, sample, source, destination = make_state()
    state.place_sample(sample.id, source.id)
    history_before = sample.history
    original_add = StationSlot._add_occupant

    def fail_after_add(self: StationSlot, sample_id: str) -> None:
        original_add(self, sample_id)
        if self.id == destination.id:
            raise RuntimeError("injected post-add failure")

    monkeypatch.setattr(StationSlot, "_add_occupant", fail_after_add)
    with pytest.raises(RuntimeError, match="post-add"):
        state.relocate_sample(sample.id, source.id, destination.id)

    assert source.occupant_ids == (sample.id,)
    assert destination.occupant_ids == ()
    assert sample.current_location == source.id
    assert sample.history == history_before
