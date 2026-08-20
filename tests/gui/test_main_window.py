from __future__ import annotations

import os
from pathlib import Path
from time import monotonic, sleep

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nautolab.application import LabApplication
from nautolab.gui import MainWindow
from nautolab.workflow.events import Event


ROOT = Path(__file__).resolve().parents[2]


def _window() -> tuple[QApplication, MainWindow]:
    qt = QApplication.instance() or QApplication([])
    window = MainWindow(LabApplication.load_demo(ROOT / "config" / "demo_lab.yaml"))
    window.show(); qt.processEvents()
    return qt, window


def _wait_until(qt: QApplication, predicate, timeout: float = 2.0) -> bool:
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        qt.processEvents()
        if predicate(): return True
        sleep(0.01)
    return False


def _displayed_sample_location(window: MainWindow, sample_id: str) -> str | None:
    for station_index in range(window.station_map.tree.topLevelItemCount()):
        station = window.station_map.tree.topLevelItem(station_index)
        for slot_index in range(station.childCount()):
            slot = station.child(slot_index)
            if sample_id in slot.text(3).split(", "):
                return slot.text(1)
    return None


def test_main_window_smoke_and_page_navigation() -> None:
    qt, window = _window()
    assert window.windowTitle().startswith("N-AutoLab")
    assert window.navigation.count() == 7
    for index, name in enumerate(window.PAGE_NAMES):
        window.navigation.setCurrentRow(index); qt.processEvents()
        assert window.stack.currentIndex() == index
        assert window.navigation.currentItem().text() == name
    window.close()


def test_station_hierarchy_sample_devices_and_truthful_state_render() -> None:
    _qt, window = _window()
    assert window.station_map.tree.topLevelItemCount() == 5
    hotplate = next(window.station_map.tree.topLevelItem(i) for i in range(5) if window.station_map.tree.topLevelItem(i).text(1) == "hotplate_01")
    assert hotplate.childCount() == 3
    assert hotplate.child(0).text(3) == "sample_002"
    assert window.samples.table.rowCount() == 4
    implementation_values = {window.devices.table.item(row, 2).text() for row in range(window.devices.table.rowCount())}
    connection_values = {window.devices.table.item(row, 3).text() for row in range(window.devices.table.rowCount())}
    assert implementation_values == {"NOT_IMPLEMENTED"}
    assert connection_values == {"DISCONNECTED"}
    window.close()


def test_recipe_validation_workflow_occupancy_and_logs_update() -> None:
    qt, window = _window()
    window.recipe.validate(); qt.processEvents()
    assert "PASSED" in window.recipe.errors.toPlainText()
    assert window.workflow.run_button.isEnabled()
    window.application.run_simulation(); window.refresh_all(); qt.processEvents()
    assert "COMPLETED" in window.workflow.summary.text()
    assert "WorkflowCompleted" in window.logs.text.toPlainText()
    storage = next(window.station_map.tree.topLevelItem(i) for i in range(5) if window.station_map.tree.topLevelItem(i).text(1) == "storage_01")
    assert storage.child(0).text(3) == "sample_001"
    window.close()


def test_recipe_validation_error_uses_border_and_error_panel() -> None:
    qt, window = _window()
    window.recipe.table.item(0, 6).setText("unknown_station_type")
    window.recipe.validate(); qt.processEvents()
    assert "FAILED" in window.recipe.errors.toPlainText()
    assert "border" in window.recipe.table.styleSheet()
    assert window.recipe.table.toolTip()
    window.close()


def test_close_unsubscribes_and_late_event_is_harmless() -> None:
    qt, window = _window()
    window.close(); qt.processEvents()
    window.application.events.publish(Event(message="late event after close"))
    qt.processEvents()
    assert not window.isVisible()


def test_golden_template_auto_source_round_trip_and_speed_choices() -> None:
    _qt, window = _window()
    assert [window.recipe.table.item(row, 4).text() for row in range(4)] == ["AUTO"] * 4
    assert all(step.action.source_slot_id is None for step in window.recipe.to_recipe().steps)
    assert [window.workflow.speed.itemText(index) for index in range(window.workflow.speed.count())] == [
        "Instant", "20×", "10×", "5×", "1×",
    ]
    assert window.workflow.speed.currentText() == "10×"
    window.close()


def test_visible_playback_updates_running_station_map_and_logs_incrementally() -> None:
    qt, window = _window()
    for row in range(window.recipe.table.rowCount()): window.recipe.table.item(row, 7).setText("2")
    window.recipe.validate(); window.workflow.speed.setCurrentText("20×")
    observed_locations = {_displayed_sample_location(window, "sample_001")}
    observed_log_counts = {len(window.application.events.events)}
    window.run_simulation()
    running_seen = False
    deadline = monotonic() + 3
    while monotonic() < deadline and window.worker and window.worker.isRunning():
        qt.processEvents(); running_seen |= "RUNNING" in window.workflow.summary.text()
        observed_locations.add(_displayed_sample_location(window, "sample_001"))
        observed_log_counts.add(len(window.application.events.events)); sleep(0.01)
    assert window.worker is not None; window.worker.wait(1000); qt.processEvents()
    observed_locations.add(_displayed_sample_location(window, "sample_001"))
    assert running_seen
    assert {"storage_01.slot_01", "hotplate_01.slot_03", "spin_coater_01.slot_01"} <= observed_locations
    assert len(observed_log_counts) >= 3
    assert "WorkflowCompleted" in window.logs.text.toPlainText()
    window.close()


def test_gui_close_aborts_visible_playback_promptly() -> None:
    qt, window = _window()
    for row in range(window.recipe.table.rowCount()): window.recipe.table.item(row, 7).setText("5")
    window.recipe.validate(); window.workflow.speed.setCurrentText("1×"); window.run_simulation()
    assert _wait_until(qt, lambda: window.application.current_workflow.status.value == "RUNNING")
    before = monotonic(); window.close(); qt.processEvents()
    assert monotonic() - before < 1
    assert window.worker is not None and not window.worker.isRunning()
    assert window.application.current_workflow.status.value == "ABORTED"
