"""Tests for SampleRegistry behavior."""

import pytest

from nautolab.core import DuplicateResourceError, ResourceNotFoundError, Sample
from nautolab.resources import SampleRegistry


def test_sample_registry_add_get_contains_and_list() -> None:
    registry = SampleRegistry()
    sample = Sample(id="sample_001", name="Sample")
    registry.add(sample)
    assert registry.get("sample_001") is sample
    assert registry.contains("sample_001")
    assert registry.list_all() == (sample,)


def test_sample_registry_rejects_duplicate_id() -> None:
    registry = SampleRegistry()
    registry.add(Sample(id="sample_001", name="One"))
    with pytest.raises(DuplicateResourceError):
        registry.add(Sample(id="sample_001", name="Two"))


def test_sample_registry_missing_and_remove_semantics() -> None:
    registry = SampleRegistry()
    with pytest.raises(ResourceNotFoundError):
        registry.get("missing")
    sample = Sample(id="sample_001", name="Sample")
    registry.add(sample)
    assert registry.remove("sample_001") is sample
    assert len(registry) == 0
