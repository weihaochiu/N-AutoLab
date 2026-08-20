"""Deterministic logical transport with no robot or real-time waiting."""

from __future__ import annotations

from nautolab.core import SimulationTransportError
from nautolab.resources import LabState
from nautolab.workflow.events import (
    EventBus, SampleMoved, SimulationTransportCompleted, SimulationTransportStarted,
)


class SimulationTransporter:
    implementation_state = "SIMULATED"
    connection_state = "SIMULATED"

    def __init__(self, lab: LabState, events: EventBus, *, duration_scale: float = 0.0) -> None:
        if duration_scale < 0:
            raise ValueError("duration_scale must be non-negative")
        self._lab = lab
        self._events = events
        self.duration_scale = duration_scale

    def move_sample(
        self,
        sample_id: str,
        source_slot_id: str,
        destination_slot_id: str,
        *,
        workflow_id: str,
        step_id: str,
        simulated_duration_seconds: float = 0.0,
    ) -> None:
        self._events.publish(SimulationTransportStarted(
            workflow_id, step_id,
            f"SIMULATED transport {sample_id}: {source_slot_id} → {destination_slot_id} ({simulated_duration_seconds:g}s)",
        ))
        try:
            self._lab.relocate_sample(
                sample_id, source_slot_id, destination_slot_id,
                note="Simulation transport",
                metadata={"workflow_id": workflow_id, "step_id": step_id, "implementation": "SIMULATED"},
            )
        except Exception as exc:
            raise SimulationTransportError(str(exc)) from exc
        self._events.publish(SampleMoved(
            workflow_id, step_id, f"{sample_id} moved {source_slot_id} → {destination_slot_id}"
        ))
        self._events.publish(SimulationTransportCompleted(
            workflow_id, step_id, f"SIMULATED transport completed: {sample_id}"
        ))
