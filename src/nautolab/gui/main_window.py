"""Phase 1 Qt operator interface backed only by application services."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QFormLayout, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QMainWindow,
    QMessageBox, QPushButton, QProgressBar, QStackedWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from nautolab.application import LabApplication
from nautolab.core import Action, ActionType, MoveDestination, Recipe, RecipeStep, WorkflowStatus


class EventBridge(QObject):
    received = Signal(object)


class SimulationWorker(QThread):
    succeeded = Signal()
    failed = Signal(str)

    def __init__(self, application: LabApplication) -> None:
        super().__init__(); self.application = application

    def run(self) -> None:
        try:
            self.application.run_simulation()
        except Exception as exc:
            self.failed.emit(str(exc))
        else:
            self.succeeded.emit()


class StationMapPage(QWidget):
    def __init__(self, application: LabApplication) -> None:
        super().__init__(); self.application = application
        layout = QVBoxLayout(self); layout.addWidget(QLabel("Station Map — canonical Station / Slot occupancy"))
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(["Resource", "Canonical ID", "State", "Occupants", "Device"])
        layout.addWidget(self.tree); self.refresh()

    def refresh(self) -> None:
        self.tree.clear()
        for station in self.application.station_views():
            parent = QTreeWidgetItem([
                station.display_name, station.id,
                f"{'ENABLED' if station.enabled else 'DISABLED'} · {station.occupancy}/{station.capacity}",
                "", station.device_id or "NOT IMPLEMENTED",
            ])
            self.tree.addTopLevelItem(parent)
            for slot in station.slots:
                parent.addChild(QTreeWidgetItem([
                    slot.display_name, slot.id,
                    f"{'ENABLED' if slot.enabled else 'DISABLED'} · {slot.occupancy}/{slot.capacity}",
                    ", ".join(slot.occupant_ids) or "EMPTY", "",
                ]))
            parent.setExpanded(True)
        for column in range(5): self.tree.resizeColumnToContents(column)


class SamplesPage(QWidget):
    def __init__(self, application: LabApplication) -> None:
        super().__init__(); self.application = application
        layout = QVBoxLayout(self); layout.addWidget(QLabel("Samples"))
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["Sample Name", "Sample ID", "Type", "Status", "Current Location"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._show_history)
        self.history = QTextEdit(); self.history.setReadOnly(True); self.history.setPlaceholderText("Select a sample to inspect canonical history")
        layout.addWidget(self.table); layout.addWidget(QLabel("History")); layout.addWidget(self.history); self.refresh()

    def refresh(self) -> None:
        samples = self.application.sample_views(); self.table.setRowCount(len(samples))
        for row, sample in enumerate(samples):
            for col, value in enumerate((sample.name, sample.id, sample.sample_type or "—", sample.status, sample.current_location or "UNLOCATED")):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._show_history()

    def _show_history(self) -> None:
        row = self.table.currentRow()
        samples = self.application.sample_views()
        self.history.setPlainText("\n".join(samples[row].history) if 0 <= row < len(samples) else "")


class DevicesPage(QWidget):
    def __init__(self, application: LabApplication) -> None:
        super().__init__(); self.application = application
        layout = QVBoxLayout(self); layout.addWidget(QLabel("Devices — truthful Phase 1 hardware state"))
        self.table = QTableWidget(); layout.addWidget(self.table); self.refresh()

    def refresh(self) -> None:
        devices = self.application.device_views(); self.table.setRowCount(len(devices)); self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Device", "Type", "Implementation State", "Connection State", "Capabilities", "Backend"])
        for row, device in enumerate(devices):
            values = (device.display_name, device.device_type, device.implementation_state, device.connection_state, ", ".join(device.capabilities), device.backend)
            for col, value in enumerate(values): self.table.setItem(row, col, QTableWidgetItem(value))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)


class RecipePage(QWidget):
    COLUMNS = ("#", "Enabled", "Action", "Sample", "Source", "Destination Mode", "Destination", "Duration", "Notes")

    def __init__(self, application: LabApplication, validated_callback) -> None:
        super().__init__(); self.application = application; self.validated_callback = validated_callback
        layout = QVBoxLayout(self)
        header = QHBoxLayout(); header.addWidget(QLabel("Recipe Table Editor (view only; Recipe model is canonical)")); header.addStretch()
        for label, callback in (("Add Step", self.add_row), ("Remove Step", self.remove_row), ("Templates", self.templates), ("Validate", self.validate)):
            button = QPushButton(label); button.clicked.connect(callback); header.addWidget(button)
        layout.addLayout(header)
        self.table = QTableWidget(0, len(self.COLUMNS)); self.table.setHorizontalHeaderLabels(self.COLUMNS); layout.addWidget(self.table)
        self.errors = QTextEdit(); self.errors.setReadOnly(True); self.errors.setMaximumHeight(110); self.errors.setPlaceholderText("Validation results")
        layout.addWidget(self.errors); self.load_recipe(application.recipes.current_recipe)

    def load_recipe(self, recipe: Recipe) -> None:
        self.table.setRowCount(0)
        for step in recipe.steps:
            action = step.action; row = self.table.rowCount(); self.table.insertRow(row)
            mode = action.destination.allocation_mode.value if action.destination else "EXACT_SLOT"
            destination = ""
            if action.destination:
                destination = action.destination.exact_slot_id or action.destination.exact_station_id or action.destination.station_type or ""
            values = (str(step.order), "Yes" if step.enabled else "No", action.action_type.value, action.sample_id or "", action.source_slot_id or "", mode, destination, str(action.parameters.get("duration_seconds", 0)), step.description)
            for col, value in enumerate(values): self.table.setItem(row, col, QTableWidgetItem(value))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def add_row(self) -> None:
        row = self.table.rowCount(); self.table.insertRow(row)
        defaults = (str(row + 1), "Yes", "MOVE_SAMPLE", "sample_001", "", "STATION_TYPE", "hotplate", "0", "")
        for col, value in enumerate(defaults): self.table.setItem(row, col, QTableWidgetItem(value))

    def remove_row(self) -> None:
        if self.table.currentRow() >= 0: self.table.removeRow(self.table.currentRow())

    def _text(self, row: int, column: int) -> str:
        item = self.table.item(row, column); return item.text().strip() if item else ""

    def to_recipe(self) -> Recipe:
        steps = []
        for row in range(self.table.rowCount()):
            action_type = ActionType(self._text(row, 2))
            destination = None
            if action_type is ActionType.MOVE_SAMPLE:
                mode, value = self._text(row, 5), self._text(row, 6)
                destination = {
                    "EXACT_SLOT": lambda: MoveDestination(exact_slot_id=value),
                    "EXACT_STATION": lambda: MoveDestination(exact_station_id=value),
                    "STATION_TYPE": lambda: MoveDestination(station_type=value),
                }[mode]()
            parameters = {"duration_seconds": float(self._text(row, 7) or 0)}
            action = Action(f"gui_action_{row + 1:03d}", action_type, self._text(row, 3) or None, self._text(row, 4) or None, destination, parameters)
            steps.append(RecipeStep(f"gui_step_{row + 1:03d}", row + 1, action, self._text(row, 1).lower() not in {"no", "false", "0"}, self._text(row, 8)))
        return Recipe("gui_recipe", "GUI Recipe", steps)

    def validate(self) -> None:
        self.table.setStyleSheet("")
        try:
            report = self.application.validate_recipe(self.to_recipe())
        except Exception as exc:
            self._show_invalid(str(exc)); return
        if report.passed:
            self.errors.setStyleSheet("color: #18794e;"); self.errors.setPlainText("✓ Preflight PASSED — resolved workflow READY")
        else: self._show_invalid(report.format())
        self.validated_callback()

    def _show_invalid(self, message: str) -> None:
        # Error red is independent of future experimental-grouping backgrounds.
        self.table.setStyleSheet("QTableWidget { border: 2px solid #c62828; }")
        self.table.setToolTip(message); self.errors.setStyleSheet("color: #c62828;"); self.errors.setPlainText("⚠ " + message)

    def templates(self) -> None:
        dialog = QDialog(self); dialog.setWindowTitle("Recipe Templates"); form = QFormLayout(dialog)
        combo = QComboBox(); combo.addItems(self.application.recipes.template_names()); name = QLineEdit(); name.setPlaceholderText("New template name")
        form.addRow("Template", combo); form.addRow("Name", name)
        buttons = QHBoxLayout()
        load = QPushButton("Load"); save = QPushButton("Save"); duplicate = QPushButton("Duplicate")
        buttons.addWidget(load); buttons.addWidget(save); buttons.addWidget(duplicate); form.addRow(buttons)
        load.clicked.connect(lambda: (self.load_recipe(self.application.recipes.load_template(combo.currentText())), dialog.accept()))
        def save_now():
            self.application.recipes.save_template(name.text() or "Saved Recipe", self.to_recipe()); dialog.accept()
        save.clicked.connect(save_now)
        def duplicate_now():
            self.application.recipes.duplicate_template(combo.currentText(), name.text() or combo.currentText() + " Copy"); dialog.accept()
        duplicate.clicked.connect(duplicate_now); dialog.exec()


class WorkflowPage(QWidget):
    run_requested = Signal(); pause_requested = Signal(); resume_requested = Signal(); abort_requested = Signal()

    def __init__(self, application: LabApplication) -> None:
        super().__init__(); self.application = application; layout = QVBoxLayout(self)
        controls = QHBoxLayout(); self.summary = QLabel("No workflow validated"); controls.addWidget(self.summary); controls.addStretch()
        self.run_button = QPushButton("Run Simulation"); self.pause_button = QPushButton("Pause"); self.resume_button = QPushButton("Resume"); self.abort_button = QPushButton("Abort"); self.reset_button = QPushButton("Reset (NOT IMPLEMENTED)"); self.reset_button.setEnabled(False)
        for button, signal in ((self.run_button, self.run_requested), (self.pause_button, self.pause_requested), (self.resume_button, self.resume_requested), (self.abort_button, self.abort_requested)):
            button.clicked.connect(signal.emit); controls.addWidget(button)
        controls.addWidget(self.reset_button); layout.addLayout(controls)
        self.progress = QProgressBar(); layout.addWidget(self.progress)
        self.table = QTableWidget(); layout.addWidget(self.table); self.refresh()

    def refresh(self) -> None:
        view = self.application.workflow_view()
        if not view:
            self.summary.setText("No workflow validated"); self.table.setRowCount(0); self.run_button.setEnabled(False); self.pause_button.setEnabled(False); self.resume_button.setEnabled(False); self.abort_button.setEnabled(False); return
        self.summary.setText(f"{view.workflow_id} · {view.recipe} · {view.status} · Current: {view.current_step}")
        self.progress.setValue(round(view.progress * 100)); self.table.setRowCount(len(view.steps)); self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["State", "Step ID", "Action", "Sample", "Source", "Destination", "Error"])
        icons = {"COMPLETED": "✓", "RUNNING": "●", "PENDING": "○", "FAILED": "✕", "ABORTED": "⊘"}
        for row, step in enumerate(view.steps):
            values = (f"{icons.get(step.status, '○')} {step.status}", step.step_id, step.action, step.sample_id or "—", step.source or "—", step.destination or "—", step.error or "")
            for col, value in enumerate(values): self.table.setItem(row, col, QTableWidgetItem(value))
        status = WorkflowStatus(view.status)
        self.run_button.setEnabled(status is WorkflowStatus.READY)
        self.pause_button.setEnabled(status is WorkflowStatus.RUNNING)
        self.resume_button.setEnabled(status is WorkflowStatus.PAUSED)
        self.abort_button.setEnabled(status in {WorkflowStatus.READY, WorkflowStatus.RUNNING, WorkflowStatus.PAUSED})
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)


class LogsPage(QWidget):
    def __init__(self, application: LabApplication) -> None:
        super().__init__(); self.application = application; layout = QVBoxLayout(self)
        row = QHBoxLayout(); row.addWidget(QLabel("Event Timeline")); self.filter = QComboBox(); self.filter.addItems(["ALL", "WORKFLOW", "RESOURCE", "SAMPLE", "SIMULATION", "SAFETY", "ERROR"]); self.filter.currentTextChanged.connect(self.refresh); row.addWidget(self.filter); row.addStretch(); layout.addLayout(row)
        self.text = QTextEdit(); self.text.setReadOnly(True); layout.addWidget(self.text); self.refresh()

    def refresh(self) -> None:
        selected = self.filter.currentText() or "ALL"
        self.text.setPlainText("\n".join(
            f"{event.timestamp} {event.category:<10} {event.event_type}: {event.message}"
            for event in self.application.log_views() if selected == "ALL" or event.category == selected
        ))


class DashboardPage(QWidget):
    def __init__(self, application: LabApplication) -> None:
        super().__init__(); self.application = application; self.layout = QVBoxLayout(self); self.refresh()

    def refresh(self) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        workflow = self.application.workflow_view(); devices = self.application.device_views(); logs = self.application.log_views()
        values = (
            ("System Mode", "SIMULATION ONLY"), ("Simulation State", "SIMULATED · no hardware access"),
            ("Workflow State", workflow.status if workflow else "NOT VALIDATED"),
            ("Sample Count", str(len(self.application.sample_views()))),
            ("Device Summary", f"{len(devices)} NOT_IMPLEMENTED / DISCONNECTED"),
            ("Warnings", str(sum(e.category == 'SAFETY' for e in logs))), ("Errors", str(sum(e.category == 'ERROR' for e in logs))),
        )
        for label, value in values:
            card = QLabel(f"{label}\n{value}"); card.setFrameStyle(QFrame.Shape.StyledPanel); card.setMinimumHeight(56); self.layout.addWidget(card)
        self.layout.addWidget(QLabel("Recent Events\n" + "\n".join(f"{e.timestamp} {e.event_type}: {e.message}" for e in logs[-5:])))
        self.layout.addStretch()


class MainWindow(QMainWindow):
    PAGE_NAMES = ("Dashboard", "Station Map", "Samples", "Recipe", "Workflow", "Devices", "Logs")

    def __init__(self, application: LabApplication | None = None) -> None:
        super().__init__(); self.application = application or LabApplication.load_demo(); self.setWindowTitle("N-AutoLab — SIMULATION"); self.resize(1260, 780)
        root = QWidget(); self.setCentralWidget(root); outer = QVBoxLayout(root)
        banner = QLabel("N-AutoLab     SIMULATION     Hardware: NOT CONNECTED"); banner.setStyleSheet("font-size: 18px; font-weight: 600; padding: 10px; background: #17324d; color: white;"); outer.addWidget(banner)
        body = QHBoxLayout(); outer.addLayout(body, 1); self.navigation = QListWidget(); self.navigation.addItems(self.PAGE_NAMES); self.navigation.setFixedWidth(150); body.addWidget(self.navigation)
        self.stack = QStackedWidget(); body.addWidget(self.stack, 1)
        self.dashboard = DashboardPage(self.application); self.station_map = StationMapPage(self.application); self.samples = SamplesPage(self.application)
        self.recipe = RecipePage(self.application, self.refresh_all); self.workflow = WorkflowPage(self.application); self.devices = DevicesPage(self.application); self.logs = LogsPage(self.application)
        for page in (self.dashboard, self.station_map, self.samples, self.recipe, self.workflow, self.devices, self.logs): self.stack.addWidget(page)
        self.navigation.currentRowChanged.connect(self.stack.setCurrentIndex); self.navigation.setCurrentRow(0)
        self.statusBar().showMessage("SIMULATION | Workflow: NOT VALIDATED | Warning: 0 | Error: 0")
        self.workflow.run_requested.connect(self.run_simulation); self.workflow.pause_requested.connect(self._pause); self.workflow.resume_requested.connect(self._resume); self.workflow.abort_requested.connect(self._abort)
        self.bridge = EventBridge(); self.bridge.received.connect(self._on_event); self._unsubscribe = self.application.events.subscribe(self.bridge.received.emit)
        self.worker: SimulationWorker | None = None

    @Slot(object)
    def _on_event(self, _event) -> None: self.refresh_all()

    def refresh_all(self) -> None:
        self.dashboard.refresh(); self.station_map.refresh(); self.samples.refresh(); self.devices.refresh(); self.workflow.refresh(); self.logs.refresh()
        workflow = self.application.workflow_view(); errors = sum(e.category == "ERROR" for e in self.application.log_views())
        self.statusBar().showMessage(f"SIMULATION | Workflow: {workflow.status if workflow else 'NOT VALIDATED'} | Warning: 0 | Error: {errors}")

    def run_simulation(self) -> None:
        if self.worker and self.worker.isRunning(): return
        self.worker = SimulationWorker(self.application); self.worker.succeeded.connect(self.refresh_all); self.worker.failed.connect(self._show_error); self.worker.start()

    def _pause(self) -> None: self._command(self.application.pause)
    def _resume(self) -> None: self._command(self.application.resume)
    def _abort(self) -> None: self._command(self.application.abort)
    def _command(self, command) -> None:
        try: command()
        except Exception as exc: self._show_error(str(exc))
        self.refresh_all()

    @Slot(str)
    def _show_error(self, message: str) -> None:
        self.statusBar().showMessage("ERROR | " + message); QMessageBox.critical(self, "N-AutoLab Error", message)

    def closeEvent(self, event) -> None:
        self._unsubscribe()
        if self.worker and self.worker.isRunning():
            if self.application.current_workflow and self.application.current_workflow.status in {WorkflowStatus.RUNNING, WorkflowStatus.PAUSED}:
                try: self.application.abort()
                except Exception as exc: self.statusBar().showMessage(f"Abort during close failed: {exc}")
            self.worker.wait(2000)
        super().closeEvent(event)
