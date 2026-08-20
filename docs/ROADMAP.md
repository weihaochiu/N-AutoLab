# N-AutoLab Development Roadmap

The roadmap is capability-gated. A later phase does not begin until the preceding phase's acceptance criteria, safety evidence, tests, documentation, and operator visibility are complete.

## Phase 0 — Foundation & Architecture Contract

- Establish the Python `src` layout and package boundaries.
- Define architecture, dependency, safety, development, Git, and backup contracts.
- Pin and map PyLabRobot, Orca, IvoryOS, and N-AutoProv V1 references.
- Establish structural tests, Windows setup, and a truthful status launcher.
- Perform no hardware access and implement no Phase 1 runtime capability.

## Phase 1 — Core + Simulation GUI

Phase 1 is divided into reviewable increments. Completion of one increment does
not authorize work in the next.

### Phase 1A — Core Domain + Registry + Demo Lab Configuration (Complete)

- Implement general-purpose `Sample`, `Station`, `Device`, `Action`, `Recipe`,
  and `RecipeStep` declarations.
- Implement owned in-memory `SampleRegistry`, `StationRegistry`, and
  `DeviceRegistry` collections.
- Establish `LabState` as the canonical, atomic location/occupancy mutation API.
- Load a portable YAML demo lab with truthful `NOT_IMPLEMENTED` devices.
- Add unit, integration, configuration, and architecture boundary tests.
- Perform no workflow execution, simulation transport, GUI, or hardware access.

### Phase 1A.1 — Station Instance + Slot Resource Hierarchy (Complete)

- Establish `Lab → Station instance → StationSlot → Sample`.
- Store canonical sample location and occupancy at exact Slot level.
- Derive parent Station capacity and occupancy from child slots.
- Support multiple same-type Stations, variable slot counts, deterministic
  Station-type/Slot availability queries, and semantic Slot poses.
- Migrate the demo to schema version 2 with two independent Hot Plates.
- Define declarative exact-Slot, exact-Station, and Station-type destination
  intent without resolving or executing it.
- Perform no resource resolution, workflow execution, scheduling, simulation,
  GUI, or hardware access.

### Phase 1B — Resource Resolution + Workflow + Simulation

- Resolve exactly one of: exact Slot, exact Station/auto Slot, or Station
  type/auto Station+Slot using explicit deterministic policy.
- Define resolved `Workflow` and step lifecycle state separately from `Recipe`.
- Implement an event system and preflight validation.
- Implement `SimulationTransporter` over an explicit station/transport model.
- Implement `WorkflowExecutor` only after the above contracts are accepted.
- Validate the simulation-only golden path:

```text
Storage:S1
→ HotPlate
→ SpinCoater
→ HotPlate
→ Storage:S1
```

### Phase 1C — Minimal Desktop Qt Visibility

Provide application-backed desktop views for:

```text
Dashboard
Station Map
Samples
Devices
Recipe
Workflow
Logs
```

Widgets display state and issue application commands; they do not own registry,
workflow, simulation, or safety logic.

No real hardware is authorized anywhere in Phase 1.

## Phase 2 — Robot Integration

References:

- PyLabRobot: device/backend architecture.
- Orca: transporter role.
- N-AutoProv V1: robot, gripper, motion, teach-point, and safety behavior.

Sequence:

1. Specify transporter and robot capabilities.
2. Implement and test `SimulationRobotBackend`.
3. Audit V1 behavior and vendor licensing/API requirements.
4. Implement `RealRobotBackend` behind explicit configuration and preflight.
5. Validate with an approved, staged hardware test plan.

## Phase 3 — Transport + Station Hardware Validation

- Validate physical station pose references, Safe-Z/approach policies, occupancy, transfer recovery, and transport graph edges.
- Add guarded calibration and verification UX.
- Prove the transporter never turns missing or stale calibration into a fake success.

## Phase 4 — Spin Coater Integration

- Define device capability and explicit simulation backend.
- Obtain and document the actual vendor protocol.
- Implement and validate a real backend, stop behavior, fault reporting, and GUI visibility.
- V1 does not contain a completed vendor command protocol.

## Phase 5 — Hot Plate Integration

- Define temperature-control capabilities and explicit simulator.
- Study V1 Modbus behavior and fail-closed safety rules.
- Implement a real backend with independent limits, connection status, standby, and abort/shutdown semantics.

## Phase 6 — Production Recipe Workflow

- Promote validated actions into production workflows.
- Add recipe versioning/migration, resource conflict handling, recovery, audit history, and production preflight.
- Validate an end-to-end workflow without GUI-owned logic.

## Phase 7 — D405 Vision-Guided Pick

- Add a camera backend and calibrated coordinate relationship.
- Implement vision-guided station pick correction with confidence, bounds, and operator-visible evidence.
- Keep vision failure from silently degrading to uncorrected motion.

## Phase 8 — Spectrometer Integration

- Complete OtO SDK/license review and 64-bit runtime compatibility plan.
- Implement explicit simulation and real spectrometer backends.
- Add acquisition, metadata, calibration, file/provenance, error, and result visibility.

## Phase 9 — Measurement / Analysis / Data Provenance

- Introduce experiment, sample, action, raw-data, result, calibration, and software-version provenance.
- Support analysis without coupling instruments to one material system.
- Add export and traceability tests.

## Phase 10 — Closed-Loop / Autonomous Experiment Optimization

- Define optimization objectives and constraints over stable workflow/data contracts.
- Add safe proposal, validation, approval, execution, and result-feedback loops.
- Evaluate optimizers only after deterministic execution, provenance, abort, and recovery are production-ready.

## Explicitly Deferred Complexity

Databases, Docker, REST services, Flask/FastAPI, MQTT, Redis, Celery, microservices, plugin frameworks, cloud backends, AI agents, and Bayesian optimization are not introduced without a future requirement and ADR.
