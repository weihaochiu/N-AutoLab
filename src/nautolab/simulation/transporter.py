"""Deterministic logical transport with no robot or real-time waiting."""

from __future__ import annotations

from nautolab.core import SimulationTransportError
from nautolab.resources import LabState
from nautolab.workflow.events import (
    EventBus, SampleMoved, SimulationTransportCompleted, SimulationTransportStarted,
)

from .playback import SimulationPlayback


class SimulationTransporter:
    implementation_state = "SIMULATED"
    connection_state = "SIMULATED"

    def __init__(
        self,
        lab: LabState,
        events: EventBus,
        *,
        playback: SimulationPlayback | None = None,
    ) -> None:
        self._lab = lab
        self._events = events
        self.playback = playback or SimulationPlayback()

    def wait(self, duration_seconds: float, abort_requested) -> None:
        """Apply the configured playback policy outside the Qt GUI thread."""
        self.playback.wait(duration_seconds, abort_requested)

    def move_sample(
        self,
        sample_id: str,
        source_slot_id: str,
        destination_slot_id: str,
        *,
        workflow_id: str,
        step_id: str,
        simulated_duration_seconds: float = 0.0,
        abort_requested=lambda: False,
    ) -> None:
        self._validate_runtime_resources(source_slot_id, destination_slot_id)
        self._events.publish(SimulationTransportStarted(
            workflow_id, step_id,
            f"SIMULATED transport {sample_id}: {source_slot_id} → {destination_slot_id} ({simulated_duration_seconds:g}s)",
        ))
        self.wait(simulated_duration_seconds, abort_requested)
        self._validate_runtime_resources(source_slot_id, destination_slot_id)
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

    def _validate_runtime_resources(self, source_slot_id: str, destination_slot_id: str) -> None:
        """Fail closed when resolved resources change after preflight."""
        try:
            source = self._lab.slots.get(source_slot_id)
            source_station = self._lab.stations.get(source.parent_station_id)
            destination = self._lab.slots.get(destination_slot_id)
            destination_station = self._lab.stations.get(destination.parent_station_id)
        except Exception as exc:
            raise SimulationTransportError(str(exc)) from exc
        if not source_station.enabled:
            raise SimulationTransportError(f"source station {source_station.id!r} is disabled")
        if not source.enabled:
            raise SimulationTransportError(f"source slot {source.id!r} is disabled")
        if not destination_station.enabled:
            raise SimulationTransportError(f"destination station {destination_station.id!r} is disabled")
        if not destination.enabled:
            raise SimulationTransportError(f"destination slot {destination.id!r} is disabled")
