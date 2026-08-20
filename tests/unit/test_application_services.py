from pathlib import Path

from nautolab.application import LabApplication
from nautolab.core import WorkflowStatus


ROOT = Path(__file__).resolve().parents[2]


def test_application_read_models_hide_mutable_domain_internals() -> None:
    app = LabApplication.load_demo(ROOT / "config" / "demo_lab.yaml")
    stations = app.station_views(); samples = app.sample_views(); devices = app.device_views()
    assert stations[0].slots
    assert not hasattr(stations[0].slots[0], "_occupant_ids")
    assert samples[0].current_location
    assert all(device.implementation_state == "NOT_IMPLEMENTED" for device in devices)
    assert all(device.connection_state == "DISCONNECTED" for device in devices)


def test_application_validates_runs_and_exposes_event_views() -> None:
    app = LabApplication.load_demo(ROOT / "config" / "demo_lab.yaml")
    report = app.validate_recipe()
    assert report.passed and app.current_workflow
    assert app.current_workflow.status is WorkflowStatus.READY
    workflow = app.run_simulation()
    assert workflow.status is WorkflowStatus.COMPLETED
    assert app.lab.samples.get("sample_001").current_location == "storage_01.slot_01"
    assert app.workflow_view().progress == 1.0
    assert {event.category for event in app.log_views()} >= {"WORKFLOW", "RESOURCE", "SAMPLE", "SIMULATION"}


def test_recipe_templates_are_independent_copies() -> None:
    app = LabApplication.load_demo(ROOT / "config" / "demo_lab.yaml")
    recipe = app.recipes.load_template("Golden Path")
    app.recipes.save_template("Copy", recipe)
    assert app.recipes.load_template("Copy") is not recipe
