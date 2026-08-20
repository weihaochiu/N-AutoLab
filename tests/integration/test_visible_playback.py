from __future__ import annotations

from pathlib import Path
from threading import Event, Thread
from time import monotonic

from nautolab.application.services import RecipeService
from nautolab.core import Action, ActionType, Recipe, RecipeStep, WorkflowStatus, WorkflowStepStatus
from nautolab.resources import load_lab_config
from nautolab.safety import PreflightService
from nautolab.simulation import SimulationPlayback, SimulationTransporter
from nautolab.workflow import EventBus, WorkflowExecutor
from nautolab.workflow.events import SampleMoved, StepStarted


ROOT = Path(__file__).resolve().parents[2]


def _runtime(speed: str):
    lab = load_lab_config(ROOT / "config" / "demo_lab.yaml")
    events = EventBus(); workflow = PreflightService(lab, events).check(RecipeService.golden_path_recipe()).workflow
    assert workflow; workflow.transition(WorkflowStatus.READY)
    executor = WorkflowExecutor(
        SimulationTransporter(lab, events, playback=SimulationPlayback.from_label(speed)), events
    )
    return lab, events, workflow, executor


def test_20x_playback_is_observable_but_completes() -> None:
    lab, events, workflow, executor = _runtime("20×")
    for step in workflow.steps: step.duration_seconds = 1.0
    started = Event(); events.subscribe(lambda event: started.set() if isinstance(event, StepStarted) else None)
    thread = Thread(target=executor.run, args=(workflow,)); thread.start()
    assert started.wait(0.5)
    assert workflow.status is WorkflowStatus.RUNNING
    thread.join(2)
    assert workflow.status is WorkflowStatus.COMPLETED
    assert len([event for event in events.events if isinstance(event, SampleMoved)]) == 4
    assert lab.samples.get("sample_001").current_location == "storage_01.slot_01"


def test_pause_during_playback_applies_after_current_step() -> None:
    _lab, events, workflow, executor = _runtime("1×")
    for step in workflow.steps: step.duration_seconds = 0.2
    started = Event(); events.subscribe(lambda event: started.set() if isinstance(event, StepStarted) else None)
    thread = Thread(target=executor.run, args=(workflow,)); thread.start(); assert started.wait(0.5)
    executor.request_pause(workflow); thread.join(1)
    assert workflow.status is WorkflowStatus.PAUSED
    assert workflow.steps[0].status is WorkflowStepStatus.COMPLETED
    assert workflow.steps[1].status is WorkflowStepStatus.PENDING
    executor.resume(workflow)
    assert workflow.status is WorkflowStatus.COMPLETED


def test_abort_interrupts_visible_wait_and_preserves_source() -> None:
    lab, events, workflow, executor = _runtime("1×")
    workflow.steps[0].duration_seconds = 5
    started = Event(); events.subscribe(lambda event: started.set() if isinstance(event, StepStarted) else None)
    thread = Thread(target=executor.run, args=(workflow,)); thread.start(); assert started.wait(0.5)
    before = monotonic(); executor.request_abort(workflow); thread.join(1)
    assert monotonic() - before < 0.5
    assert workflow.status is WorkflowStatus.ABORTED
    assert workflow.steps[0].status is WorkflowStepStatus.ABORTED
    assert lab.samples.get("sample_001").current_location == "storage_01.slot_01"


def test_wait_action_uses_visible_playback_duration() -> None:
    lab = load_lab_config(ROOT / "config" / "demo_lab.yaml")
    recipe = Recipe("wait_recipe", "Wait", (
        RecipeStep("wait_step", 1, Action(
            "wait_action", ActionType.WAIT, parameters={"duration_seconds": 0.1}
        )),
    ))
    events = EventBus(); workflow = PreflightService(lab, events).check(recipe).workflow
    assert workflow; workflow.transition(WorkflowStatus.READY)
    executor = WorkflowExecutor(
        SimulationTransporter(lab, events, playback=SimulationPlayback.from_label("1×")), events
    )
    before = monotonic(); executor.run(workflow)
    assert monotonic() - before >= 0.08
    assert workflow.status is WorkflowStatus.COMPLETED


def test_abort_requested_during_final_step_wins_over_completion() -> None:
    lab = load_lab_config(ROOT / "config" / "demo_lab.yaml")
    recipe = Recipe("wait_recipe", "Wait", (
        RecipeStep("wait_step", 1, Action(
            "wait_action", ActionType.WAIT, parameters={"duration_seconds": 0.2}
        )),
    ))
    events = EventBus(); workflow = PreflightService(lab, events).check(recipe).workflow
    assert workflow; workflow.transition(WorkflowStatus.READY)
    executor = WorkflowExecutor(
        SimulationTransporter(lab, events, playback=SimulationPlayback.from_label("1×")), events
    )
    started = Event(); events.subscribe(lambda event: started.set() if isinstance(event, StepStarted) else None)
    thread = Thread(target=executor.run, args=(workflow,)); thread.start(); assert started.wait(0.5)
    executor.request_abort(workflow); thread.join(1)
    assert workflow.status is WorkflowStatus.ABORTED
