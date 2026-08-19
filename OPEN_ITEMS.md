# N-AutoLab Open Items

This is the canonical, categorized backlog. Items describe deliverables and acceptance evidence; source files must not accumulate untracked TODO lists. Phase 0 records these items only and implements none of them.

Status vocabulary: `OPEN`, `IN_PROGRESS`, `BLOCKED`, `DONE`, `DROPPED`.

## Architecture

### NAL-ARCH-001 — Review Phase 1 architecture boundaries

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Confirm package ownership and dependency tests before domain implementation expands.
- **Reference:** `ARCHITECTURE.md`; ADRs 0001–0005
- **Dependencies:** Phase 0 acceptance
- **Acceptance Criteria:** Agreed module map; import rules encoded as tests; documents updated for approved changes.
- **Tests:** Architecture dependency tests.
- **Notes:** This is a review gate, not permission to redesign the formal direction silently.

## Core Domain

### NAL-CORE-001 — Implement Sample model

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Add a general sample identity, type label, location, status, metadata, and history model.
- **Reference:** `ARCHITECTURE.md` §7
- **Dependencies:** NAL-ARCH-001
- **Acceptance Criteria:** No fixed material enum; location/history invariants defined; serialization contract versioned.
- **Tests:** Unit tests for identity, transitions, metadata, history, and invalid state.
- **Notes:** Must support substrate, thin film, device, electrode, solution, and future custom types without core rewrites.

### NAL-CORE-002 — Implement Station model

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Add general station identity, type, capacity, occupancy, pose reference, capabilities, enabled state, and metadata.
- **Reference:** PyLabRobot resource concepts; `ARCHITECTURE.md` §6
- **Dependencies:** NAL-ARCH-001
- **Acceptance Criteria:** Capacity/occupancy invariants are explicit; coordinates are not embedded in workflow code.
- **Tests:** Unit tests for occupancy, capacity, enable/disable, metadata, and invalid transitions.
- **Notes:** No process-specific station class in Core.

### NAL-CORE-003 — Implement Device abstraction

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Define device identity, type, backend, capabilities, implementation state, and connection state.
- **Reference:** PyLabRobot machine/backend pattern; ADR 0002
- **Dependencies:** NAL-ARCH-001
- **Acceptance Criteria:** Simulation and real implementations share a capability contract; no fake `READY` state.
- **Tests:** Unit/contract tests for states, backend compatibility, capability lookup, and failures.
- **Notes:** Do not add vendor SDK dependencies.

## Resources / Station

### NAL-RES-001 — Implement StationRegistry

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Provide unique station registration and lookup independent of GUI.
- **Reference:** Orca `ResourceRegistry` concept
- **Dependencies:** NAL-CORE-002
- **Acceptance Criteria:** Duplicate ids fail; typed/query behavior is deterministic; ownership is clear.
- **Tests:** Registry unit tests plus dependency tests.
- **Notes:** Do not copy Orca implementation.

### NAL-RES-002 — Implement SampleRegistry

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Provide unique sample registration, lookup, and controlled location/status updates.
- **Reference:** Orca registry concept; N-AutoLab sample contract
- **Dependencies:** NAL-CORE-001
- **Acceptance Criteria:** No duplicate ids; mutation paths preserve history and invariants.
- **Tests:** Registry and state-transition unit tests.
- **Notes:** Registry must not become global mutable state.

## Workflow

### NAL-WF-001 — Implement Action / Recipe model

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Represent atomic actions and user recipe intent independently of GUI and hardware.
- **Reference:** Orca action/method concepts; `ARCHITECTURE.md` §8
- **Dependencies:** NAL-CORE-001, NAL-CORE-002, NAL-CORE-003
- **Acceptance Criteria:** `Action`, `Recipe`, and resolved `Workflow` have distinct contracts; versioned validation exists.
- **Tests:** Schema, validation, serialization, and representation-independence tests.
- **Notes:** Recipe must not call devices or vendor APIs.

### NAL-WF-002 — Implement WorkflowExecutor

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Execute validated simulation workflows with explicit lifecycle and action status.
- **Reference:** Orca workflow/executor concepts
- **Dependencies:** NAL-WF-001, NAL-WF-003, NAL-SAFE-001, NAL-SIM-001
- **Acceptance Criteria:** Pending/running/completed/failed/paused/aborted transitions are deterministic and visible.
- **Tests:** Unit and integration tests for success, failure, pause/resume, abort, cleanup, and resource conflicts.
- **Notes:** Phase 1 execution is simulation-only.

### NAL-WF-003 — Implement Event system

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Publish typed domain/application events without coupling executor, devices, and GUI.
- **Reference:** Orca EventBus concept
- **Dependencies:** NAL-ARCH-001
- **Acceptance Criteria:** Typed events, ordering/error policy, subscription lifecycle, and test adapter are defined.
- **Tests:** Delivery, unsubscribe, handler-failure, ordering, and dependency-boundary tests.
- **Notes:** Events must not bypass safety or hide hardware command ownership.

## Simulation

### NAL-SIM-001 — Implement SimulationTransporter

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Move samples across the simulation station graph with truthful state updates.
- **Reference:** Orca transporter concept; PyLabRobot device-free development
- **Dependencies:** NAL-CORE-001, NAL-CORE-002, NAL-RES-001, NAL-RES-002
- **Acceptance Criteria:** Phase 1 golden path completes without hardware; occupancy/history remain consistent; state is labeled `SIMULATED`.
- **Tests:** Transport success, unavailable route, occupied destination, rollback/failure, and golden-path integration tests.
- **Notes:** No robot motion primitives.

## GUI

### NAL-GUI-001 — Implement V2 Dashboard

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Provide a minimal Qt overview of system, workflow, device, sample, and safety state.
- **Reference:** IvoryOS visibility UX; ADR 0004
- **Dependencies:** NAL-WF-003 and application read models
- **Acceptance Criteria:** No business logic in widgets; all incomplete capabilities are visibly truthful.
- **Tests:** GUI smoke tests and presentation/application boundary tests.
- **Notes:** Desktop Qt, not a web migration.

### NAL-GUI-002 — Implement Station Map GUI

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Visualize and edit the simulation station map through application services.
- **Reference:** PyLabRobot visual resource state; IvoryOS visibility UX
- **Dependencies:** NAL-CORE-002, NAL-RES-001, NAL-WF-003
- **Acceptance Criteria:** Capacity, occupancy, enabled state, and logical links are visible; no raw robot coordinates in widgets.
- **Tests:** GUI model tests, invalid edit tests, and simulation update integration test.
- **Notes:** Real calibration controls are deferred.

### NAL-GUI-003 — Implement Recipe Table Editor

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Provide the first recipe editor over the shared recipe model.
- **Reference:** IvoryOS builder UX; `ARCHITECTURE.md` §8
- **Dependencies:** NAL-WF-001
- **Acceptance Criteria:** Validate before run; round-trip data without GUI-specific semantics; show actionable errors.
- **Tests:** Model/view tests, validation errors, round trip, and representation-independence tests.
- **Notes:** A future flow editor must not require rewriting the recipe engine.

### NAL-GUI-004 — Implement Workflow Monitor

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Show workflow/step state, logs, errors, and safe runtime controls.
- **Reference:** IvoryOS execution UX
- **Dependencies:** NAL-WF-002, NAL-WF-003
- **Acceptance Criteria:** Current, pending, running, completed, failed, paused, and aborted states are visible; controls reflect actual support.
- **Tests:** Event-to-view tests and control-state GUI tests.
- **Notes:** Reset semantics must be defined before the button is enabled.

## Robot

### NAL-ROBOT-001 — Audit N-AutoProv V1 Robot implementation

- **Status:** OPEN
- **Phase:** 2
- **Goal:** Convert V1 connection, motion, gripper, teach-point, Safe-Z, shutdown, and C22 behavior into reviewed requirements.
- **Reference:** `docs/V1_REFERENCE_MAP.md`; N-AutoProv V1 `0f1d14e`
- **Dependencies:** Phase 1 stable transporter/device contracts
- **Acceptance Criteria:** Behavior matrix, license/API review, hazards, unknowns, and approved hardware validation plan exist.
- **Tests:** Static contract tests plus simulator scenarios; no hardware test without explicit approval.
- **Notes:** V1 is not the architecture template.

### NAL-ROBOT-002 — Implement SimulationRobotBackend

- **Status:** OPEN
- **Phase:** 2
- **Goal:** Model robot/transporter capabilities and faults without hardware.
- **Reference:** PyLabRobot backend pattern; Orca transporter concept
- **Dependencies:** NAL-SIM-001, NAL-ROBOT-001
- **Acceptance Criteria:** Same capability contract as planned real backend; simulated position/tool/error state is visible and deterministic.
- **Tests:** Backend contract, transport, injected fault, abort, and recovery tests.
- **Notes:** Must report `SIMULATED`.

### NAL-ROBOT-003 — Implement RealRobotBackend

- **Status:** OPEN
- **Phase:** 2
- **Goal:** Integrate the approved robot SDK behind device/transporter abstractions.
- **Reference:** PyLabRobot pattern; V1 behavior requirements
- **Dependencies:** NAL-ROBOT-001, NAL-ROBOT-002, safety approval
- **Acceptance Criteria:** Explicit real selection, connection/preflight, command serialization, motion/gripper safety, abort/shutdown, and GUI state pass staged validation.
- **Tests:** Contract tests, mocked SDK tests, and separately approved hardware validation.
- **Notes:** No automatic fallback to simulation.

## Hot Plate

### NAL-HOT-001 — Implement hot plate backends

- **Status:** OPEN
- **Phase:** 5
- **Goal:** Add explicit simulation and real temperature-control backends with fail-closed safety.
- **Reference:** PyLabRobot backend pattern; V1 hot-plate behavior
- **Dependencies:** Stable Device/Workflow/Safety contracts
- **Acceptance Criteria:** Connection, limits, read/write, standby, abort, and shutdown behavior are visible and tested.
- **Tests:** Backend contract, simulator, mocked protocol, safety-limit, communication-loss, and approved hardware tests.
- **Notes:** Study V1; do not silently inherit its register assumptions.

## Spin Coater

### NAL-SPIN-001 — Implement spin coater backends

- **Status:** OPEN
- **Phase:** 4
- **Goal:** Define spin capabilities and implement simulation before the verified vendor protocol.
- **Reference:** PyLabRobot pattern; V1 incomplete spin shell
- **Dependencies:** Stable Device/Workflow/Safety contracts; vendor protocol
- **Acceptance Criteria:** Program/start/stop/fault semantics are defined; real readiness requires verified commands.
- **Tests:** Simulator, validation, mocked protocol, stop/fault, and approved hardware tests.
- **Notes:** `NOT_IMPLEMENTED_IN_V1` for real command execution.

## Vision

### NAL-VISION-001 — Vision-guided station pick correction

- **Status:** OPEN
- **Phase:** 7
- **Goal:** Apply bounded, calibrated D405-derived correction to station pick operations.
- **Reference:** V1 D405 behavior; N-AutoLab transporter contract
- **Dependencies:** NAL-ROBOT-003, camera backend, calibration/provenance model
- **Acceptance Criteria:** Confidence/bounds, calibration version, evidence, operator visibility, and fail-closed behavior are defined and validated.
- **Tests:** Recorded-data tests, calibration/error simulations, and separately approved hardware tests.
- **Notes:** Vision failure must not silently produce uncorrected motion.

## Spectrometer

### NAL-SPEC-001 — OtO spectrometer integration

- **Status:** OPEN
- **Phase:** 8
- **Goal:** Add simulation and real acquisition backends with licensed SDK placement and result provenance.
- **Reference:** V1 OtO planning documents only
- **Dependencies:** Device contract, data provenance, SDK/license review
- **Acceptance Criteria:** SDK compatibility, acquisition, calibration, metadata, files, errors, GUI, and shutdown are validated.
- **Tests:** Simulator, mocked DLL boundary, data contract, error, and approved hardware tests.
- **Notes:** `NOT_IMPLEMENTED_IN_V1`.

## Safety

### NAL-SAFE-001 — Implement Preflight validation

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Validate workflow, capability, station, occupancy, implementation state, and connection requirements before execution.
- **Reference:** N-AutoLab safety contract; V1 preflight lessons
- **Dependencies:** NAL-CORE-001, NAL-CORE-002, NAL-CORE-003, NAL-WF-001
- **Acceptance Criteria:** Simulation-only and future real modes are explicit; failures are aggregated and operator-visible; no side effects occur.
- **Tests:** Missing capability/station, disabled resource, occupied station, state mismatch, and no-side-effect tests.
- **Notes:** Passing simulation preflight never implies real hardware readiness.

## Data

### NAL-DATA-001 — Experiment / sample provenance model

- **Status:** OPEN
- **Phase:** 9
- **Goal:** Trace samples, recipes, workflows, actions, devices, calibration, software, raw data, and results.
- **Reference:** IvoryOS result visibility UX; N-AutoLab domain contract
- **Dependencies:** Stable workflow and device event contracts
- **Acceptance Criteria:** Identifiers, timestamps, versions, links, export, and immutable audit expectations are specified and tested.
- **Tests:** Round-trip, linkage, versioning, missing-data, and export tests.
- **Notes:** Storage technology remains an explicit later decision.

## Testing

### NAL-TEST-001 — Enforce architecture dependency rules

- **Status:** OPEN
- **Phase:** 1
- **Goal:** Prevent forbidden imports and vendor/GUI leakage through automated tests.
- **Reference:** `ARCHITECTURE.md` §§2–3
- **Dependencies:** NAL-ARCH-001
- **Acceptance Criteria:** Tests detect representative forbidden dependencies and run in the normal suite.
- **Tests:** Architecture tests against package import graph.
- **Notes:** Keep the mechanism small; no new framework without need.

## Migration

### NAL-MIG-001 — Define V1 data migration plan

- **Status:** OPEN
- **Phase:** 2–6
- **Goal:** Version and transform approved V1 teach points, station maps, configuration, and recipes.
- **Reference:** `docs/V1_REFERENCE_MAP.md`
- **Dependencies:** Corresponding N-AutoLab schemas
- **Acceptance Criteria:** Dry-run, backup, validation, conflict/error reporting, provenance, and rollback are specified per data family.
- **Tests:** Fixture-based transformation and rejection tests; no access to live V1 config during normal tests.
- **Notes:** Migration is selective and never makes V1 native architecture authoritative.

## Closed Loop

### NAL-CL-001 — Define closed-loop safety and optimization contract

- **Status:** OPEN
- **Phase:** 10
- **Goal:** Specify safe proposal, constraint validation, approval, execution, measurement, and feedback boundaries.
- **Reference:** N-AutoLab roadmap
- **Dependencies:** Production workflow, provenance, measurement, abort, and recovery capabilities
- **Acceptance Criteria:** Hazard boundaries, human override, constraints, reproducibility, and audit trail are approved before optimizer selection.
- **Tests:** Simulation scenarios for invalid proposals, aborts, missing data, and recovery.
- **Notes:** No optimizer, AI agent, or cloud backend is selected in Phase 0.

## Infrastructure

### NAL-INFRA-001 — Implement pre-push backup and safety gate

- **Status:** OPEN
- **Phase:** 1 or later
- **Goal:** Create a small, tested gate that backs up the exact commit and prevents accidental push of unsafe/local artifacts.
- **Reference:** `docs/BACKUP_STRATEGY.md`; V1 backup behavior as a study reference
- **Dependencies:** Stable repository workflow and user-selected backup location
- **Acceptance Criteria:** Exact-commit verification, exclusions, restore test, hook installation, failure behavior, and remote SHA verification are documented and tested.
- **Tests:** Isolated temporary-repository tests for success, exclusion, failure, and restore.
- **Notes:** Phase 0 intentionally provides specification only.
