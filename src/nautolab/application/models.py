"""Immutable application read models consumed by presentation layers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SlotView:
    id: str; display_name: str; enabled: bool; occupancy: int; capacity: int
    occupant_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StationView:
    id: str; display_name: str; station_type: str; enabled: bool
    occupancy: int; capacity: int; device_id: str | None; slots: tuple[SlotView, ...]


@dataclass(frozen=True, slots=True)
class SampleView:
    id: str; name: str; sample_type: str | None; status: str
    current_location: str | None; history: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DeviceView:
    id: str; display_name: str; device_type: str; implementation_state: str
    connection_state: str; capabilities: tuple[str, ...]; backend: str


@dataclass(frozen=True, slots=True)
class WorkflowStepView:
    step_id: str; action: str; sample_id: str | None; source: str | None
    destination: str | None; status: str; error: str | None


@dataclass(frozen=True, slots=True)
class WorkflowView:
    workflow_id: str; recipe: str; status: str; current_step: str
    progress: float; steps: tuple[WorkflowStepView, ...]; error: str | None


@dataclass(frozen=True, slots=True)
class LogEventView:
    timestamp: str; category: str; event_type: str; message: str
