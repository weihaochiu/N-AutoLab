"""GUI-safe Phase 1 application boundary and query services."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from nautolab.core import (
    Action, ActionType, ExecutionMode, MoveDestination, Recipe, RecipeStep,
    WorkflowStatus, WorkflowStepStatus,
)
from nautolab.resources import LabState, load_lab_config
from nautolab.safety import PreflightReport, PreflightService
from nautolab.simulation import SimulationPlayback, SimulationTransporter
from nautolab.workflow import EventBus, Workflow, WorkflowExecutor

from .models import (
    DeviceView, LogEventView, SampleView, SlotView, StationView,
    WorkflowStepView, WorkflowView,
)


class RecipeService:
    """Own user-facing recipes/templates while keeping Recipe canonical."""

    def __init__(self) -> None:
        self.current_recipe = self.golden_path_recipe()
        self._templates: dict[str, Recipe] = {"Golden Path": deepcopy(self.current_recipe)}

    @staticmethod
    def golden_path_recipe() -> Recipe:
        destinations = (
            MoveDestination(station_type="hotplate"),
            MoveDestination(station_type="spin_coater"),
            MoveDestination(station_type="hotplate"),
            MoveDestination(exact_slot_id="storage_01.slot_01"),
        )
        return Recipe("golden_path", "Golden Path", tuple(
            RecipeStep(f"step_{index:02d}", index, Action(
                f"move_{index:02d}", ActionType.MOVE_SAMPLE, "sample_001", None, destination,
                parameters={"duration_seconds": 30},
            )) for index, destination in enumerate(destinations, 1)
        ))

    def set_current(self, recipe: Recipe) -> None:
        self.current_recipe = recipe

    def template_names(self) -> tuple[str, ...]:
        return tuple(sorted(self._templates))

    def save_template(self, name: str, recipe: Recipe) -> None:
        if not name.strip(): raise ValueError("template name is required")
        self._templates[name.strip()] = deepcopy(recipe)

    def load_template(self, name: str) -> Recipe:
        self.current_recipe = deepcopy(self._templates[name])
        return self.current_recipe

    def duplicate_template(self, name: str, duplicate_name: str) -> None:
        self.save_template(duplicate_name, self._templates[name])


class LabApplication:
    """One application facade; widgets never mutate registry internals."""

    def __init__(self, lab: LabState) -> None:
        self.lab = lab
        self.events = EventBus()
        self.recipes = RecipeService()
        self.current_workflow: Workflow | None = None
        self.last_preflight: PreflightReport | None = None
        self._executor: WorkflowExecutor | None = None

    @classmethod
    def load_demo(cls, path: Path | None = None) -> "LabApplication":
        if path is None:
            path = Path(__file__).resolve().parents[3] / "config" / "demo_lab.yaml"
        return cls(load_lab_config(path))

    def validate_recipe(self, recipe: Recipe | None = None) -> PreflightReport:
        if recipe is not None: self.recipes.set_current(recipe)
        self.last_preflight = PreflightService(self.lab, self.events).check(
            self.recipes.current_recipe, ExecutionMode.SIMULATION
        )
        self.current_workflow = self.last_preflight.workflow
        if self.current_workflow:
            self.current_workflow.transition(WorkflowStatus.READY)
        return self.last_preflight

    def run_simulation(self, speed: str = "Instant") -> Workflow:
        if self.current_workflow is None or self.current_workflow.status is not WorkflowStatus.READY:
            report = self.validate_recipe()
            if not report.passed or self.current_workflow is None:
                raise RuntimeError(report.format())
        playback = SimulationPlayback.from_label(speed)
        self._executor = WorkflowExecutor(
            SimulationTransporter(self.lab, self.events, playback=playback), self.events
        )
        return self._executor.run(self.current_workflow)

    def pause(self) -> None:
        if not self._executor or not self.current_workflow: raise RuntimeError("no active workflow")
        self._executor.request_pause(self.current_workflow)

    def resume(self) -> Workflow:
        if not self._executor or not self.current_workflow: raise RuntimeError("no paused workflow")
        return self._executor.resume(self.current_workflow)

    def abort(self) -> None:
        if not self._executor or not self.current_workflow: raise RuntimeError("no active workflow")
        self._executor.request_abort(self.current_workflow)

    def station_views(self) -> tuple[StationView, ...]:
        return tuple(StationView(
            station.id, station.display_name, station.station_type, station.enabled,
            self.lab.station_occupancy(station.id), self.lab.station_total_capacity(station.id), station.device_id,
            tuple(SlotView(slot.id, slot.display_name, slot.enabled, slot.occupancy, slot.capacity, slot.occupant_ids)
                  for slot in self.lab.slots.list_by_station(station.id)),
        ) for station in self.lab.stations.list_all())

    def sample_views(self) -> tuple[SampleView, ...]:
        return tuple(SampleView(
            sample.id, sample.name, sample.sample_type, sample.status.value, sample.current_location,
            tuple(f"{entry.event_type.value}: {entry.source or '-'} → {entry.destination or '-'}" for entry in sample.history),
        ) for sample in self.lab.samples.list_all())

    def device_views(self) -> tuple[DeviceView, ...]:
        return tuple(DeviceView(
            device.id, device.display_name, device.device_type,
            device.implementation_state.value, device.connection_state.value,
            device.capabilities, device.backend_name or "NOT IMPLEMENTED",
        ) for device in self.lab.devices.list_all())

    def workflow_view(self) -> WorkflowView | None:
        workflow = self.current_workflow
        if not workflow: return None
        running = next((s.recipe_step_id for s in workflow.steps if s.status is WorkflowStepStatus.RUNNING), "—")
        return WorkflowView(
            workflow.workflow_id, workflow.recipe_name, workflow.status.value, running,
            workflow.progress, tuple(WorkflowStepView(
                s.step_id, s.action_type.value, s.sample_id, s.source_slot_id,
                s.destination_slot_id, s.status.value, s.error,
            ) for s in workflow.steps), workflow.error,
        )

    def log_views(self) -> tuple[LogEventView, ...]:
        result = [LogEventView(
            event.timestamp.astimezone().strftime("%H:%M:%S"), event.category,
            type(event).__name__, event.message,
        ) for event in self.events.events]
        result.extend(LogEventView(
            error.event.timestamp.astimezone().strftime("%H:%M:%S"), "ERROR",
            "SubscriberError", f"{error.subscriber_name}: {error.error}",
        ) for error in self.events.subscriber_errors)
        return tuple(result)
