"""Tests for the general-purpose Sample model."""

import pytest

from nautolab.core import InvalidIdentifierError, Sample, SampleStatus


def test_sample_defaults_are_hardware_independent() -> None:
    sample = Sample(id="sample_001", name="Sample 001")
    assert sample.current_location is None
    assert sample.status is SampleStatus.READY
    assert sample.history == ()


def test_sample_accepts_open_ended_type_and_metadata() -> None:
    sample = Sample(
        id="solution_a",
        name="Solution A",
        sample_type="solution",
        metadata={"concentration": "0.1 M"},
    )
    assert sample.sample_type == "solution"
    assert sample.metadata["concentration"] == "0.1 M"


def test_sample_location_has_no_public_setter() -> None:
    sample = Sample(id="sample_001", name="Sample 001")
    with pytest.raises(AttributeError):
        sample.current_location = "storage_01.slot_01"  # type: ignore[misc]


def test_sample_rename_preserves_identity() -> None:
    sample = Sample(id="sample_001", name="Old")
    sample.rename("New")
    assert sample.id == "sample_001"
    assert sample.name == "New"


def test_sample_status_change_is_recorded() -> None:
    sample = Sample(id="sample_001", name="Sample 001")
    sample.set_status(SampleStatus.IN_PROCESS, note="Preparation started")
    assert sample.status is SampleStatus.IN_PROCESS
    assert sample.history[-1].source == "READY"
    assert sample.history[-1].destination == "IN_PROCESS"


@pytest.mark.parametrize("identifier", ["Sample-1", "1_sample", "sample space", ""])
def test_sample_rejects_unstable_identifiers(identifier: str) -> None:
    with pytest.raises(InvalidIdentifierError):
        Sample(id=identifier, name="Sample")


def test_sample_to_dict_is_serializable_shape() -> None:
    data = Sample(id="sample_001", name="Sample 001").to_dict()
    assert data["id"] == "sample_001"
    assert data["current_location"] is None
    assert data["history"] == []
