from __future__ import annotations

import os
from pathlib import Path

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
