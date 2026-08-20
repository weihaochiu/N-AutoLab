# Reference Architecture

Inspection date: 2026-08-20 (Asia/Taipei)

This document records the exact public revisions inspected for the N-AutoLab Phase 0 architecture contract. Reference projects provide concepts, not runtime dependencies. No third-party source was copied into N-AutoLab.

## Reference A — PyLabRobot

| Field | Value |
| --- | --- |
| Repository | <https://github.com/PyLabRobot/pylabrobot> |
| Branch | `main` |
| Commit inspected | [`158a0a9001edcfd200edbb6818233b2d6f945f39`](https://github.com/PyLabRobot/pylabrobot/tree/158a0a9001edcfd200edbb6818233b2d6f945f39) |
| License | MIT |
| Relevant files/directories | `pylabrobot/legacy/machines/machine.py`, `pylabrobot/legacy/machines/backend.py`, `pylabrobot/legacy/liquid_handling/liquid_handler.py`, `pylabrobot/legacy/liquid_handling/backends/backend.py`, `pylabrobot/legacy/liquid_handling/backends/chatterbox.py`, `pylabrobot/resources/resource.py`, `pylabrobot/resources/deck.py`, `pylabrobot/serializer.py`, `pylabrobot/visualizer/`, `docs/user_guide/machine-agnostic-features/` |

### Architecture observed

- A machine frontend owns a backend abstraction and delegates lifecycle/operations to it.
- Device-family backends provide a hardware-independent API while vendor implementations handle device communication.
- `Resource` forms a parent/child hierarchy with relative and absolute locations; `Deck` indexes the assigned resource tree.
- Resource layout and state are serializable; assignment and state changes can feed a visualizer.
- Chatterbox-style backends and a visualizer support protocol development without physical equipment.
- Layout can be kept separate from protocol intent.

The inspected revision currently exposes `pylabrobot.machines` as a deprecated re-export to `pylabrobot.legacy.machines`; this does not change the architectural concept being studied.

### Concepts adopted

| N-AutoLab component | PyLabRobot concept adapted | N-AutoLab decision |
| --- | --- | --- |
| `Device` + `Backend` | Machine frontend/backend separation | A device expresses capabilities; simulation and real vendor backends implement them. |
| Lifecycle state | Backend setup/stop and frontend setup guard | Future devices expose implementation and connection state separately and fail closed. |
| `Resource` / `Station` | Resource tree, deck assignment, location relationships | Use general stations/resources and pose references, not a liquid-handler-specific deck. |
| Persistence | Resource/layout/state serialization | Future portable schemas separate definitions, runtime state, and machine-local calibration. |
| Simulation | Chatterbox/device-free development and visualizer state | Simulated backends and visible station/resource state precede real hardware when practical. |
| Protocol portability | Layout separate from protocol and backend-independent calls | Recipes/workflows reference logical resources/capabilities, not coordinates or vendor calls. |

### Intentionally not adopted

- PyLabRobot is not added as a Phase 0 dependency.
- N-AutoLab does not inherit the liquid-handling deck/labware taxonomy as its universal domain model.
- The browser-based visualizer implementation is not copied and does not determine the planned Qt UI architecture.
- Serialization code, class discovery, and machine implementations are not copied.
- Vendor drivers remain future license and integration decisions.

## Reference B — Orca

| Field | Value |
| --- | --- |
| Repository | <https://github.com/Cheshire-Labs/orca> |
| Branch | `main` |
| Commit inspected | [`9cd52e3eac0f365a4f153010dea334ea5b84340d`](https://github.com/Cheshire-Labs/orca/tree/9cd52e3eac0f365a4f153010dea334ea5b84340d) |
| License | AGPL-3.0-only |
| Relevant files/directories | `src/orca/system/resource_registry.py`, `src/orca/system/system_map.py`, `src/orca/system/executors.py`, `src/orca/resource_models/transporter_interface.py`, `src/orca/resource_models/transporter.py`, `src/orca/workflow_models/action_template.py`, `src/orca/workflow_models/method.py`, `src/orca/workflow_models/actions/move_action.py`, `src/orca/workflow_models/workflows/`, `src/orca/events/event_bus.py` |

### Architecture observed

- `ResourceRegistry` provides named resources, typed views, resource pools, initialization, and registry notifications.
- `SystemMap` represents locations and transporter-connected routes as a graph and resolves available paths.
- A `Transporter` owns pick/place behavior and teach points as a resource role distinct from general devices.
- Actions, methods, workflows, executing workflows, and executors separate definitions from runtime execution state.
- Status transitions and event emission support orchestration and observers.
- Resource locking, reservations, routing, and availability are explicit scheduling concerns.

### Concepts adopted

| N-AutoLab component | Orca concept adapted | N-AutoLab decision |
| --- | --- | --- |
| `StationRegistry`, `DeviceRegistry`, `SampleRegistry` | Resource registry and typed lookup | Separate registries with unique identities and explicit ownership; implementation begins in Phase 1. |
| `StationMap`, `TransportGraph` | System map and route graph | Represent logical locations and possible transport independently of raw robot coordinates. |
| `Transporter` | Transporter as resource role | A robot may fulfill transport; workflows request `MoveSample`, not robot primitives. |
| `Action`, `Workflow`, `WorkflowExecutor` | Definition/runtime separation and execution orchestration | Validate/resolve user recipes into executable workflows with explicit states. |
| Event system | Event-driven status transitions | Publish workflow/device/safety state without coupling the GUI to the executor. |
| Scheduling concerns | Resource pools, locks, reservations, route availability | Treat resource capacity and conflicts as explicit future concerns, not hidden sleeps or GUI state. |

### Intentionally not adopted

- **No Orca source implementation is copied.** Its AGPL-3.0-only license requires particular care.
- Orca is not added as a dependency and its data model is not imported.
- N-AutoLab does not assume plate/labware-only workflows.
- NetworkX, Matplotlib, Orca driver packages, and Orca scheduling algorithms are not Phase 0 dependencies.
- Detailed reservation and scheduling algorithms are deferred until requirements and licenses are reviewed.

## Reference C — IvoryOS

| Field | Value |
| --- | --- |
| Repository | <https://github.com/AccelerationConsortium/ivoryOS> |
| Branch | `main` |
| Commit inspected | [`ba3e5940d1aea7faf0b42c8ad8003e4c45b40b7c`](https://github.com/AccelerationConsortium/ivoryOS/tree/ba3e5940d1aea7faf0b42c8ad8003e4c45b40b7c) |
| License | MIT |
| Relevant files/directories | `README.md`, `ivoryos/routes/design/templates/experiment_builder.html`, `ivoryos/routes/design/templates/components/instruments_panel.html`, `ivoryos/routes/design/templates/components/canvas*.html`, `ivoryos/routes/execute/templates/experiment_run.html`, `ivoryos/routes/execute/templates/components/progress_panel.html`, `ivoryos/routes/execute/templates/components/logging_panel.html`, `ivoryos/runtime/script_runner_workflow.py`, `ivoryos/runtime/script_runner_queue.py`, `ivoryos/routes/data/templates/workflow_database.html`, `ivoryos/routes/data/templates/workflow_view.html` |

### Architecture and UX observed

- Existing Python instrument functions can be surfaced for direct control.
- A categorized instrument/action panel and canvas support workflow construction.
- Execution setup is separated from workflow design.
- Progress, iteration details, logs, pause/resume, and stop/abort controls are visible during execution.
- Historic workflow runs expose steps, timelines, logs, and downloadable result data.
- Human intervention and input are represented as explicit workflow behavior.

### Concepts adopted

| N-AutoLab GUI area | IvoryOS UX concept adapted | N-AutoLab decision |
| --- | --- | --- |
| Devices Page | Instrument visibility/direct control | Show device, backend, implementation state, connection state, capabilities, errors, and safe commands. |
| Recipe Editors | Workflow builder and separate execution setup | Begin with a table editor; allow a future flow editor over the same recipe model. |
| Workflow Monitor | Live progress and execution controls | Show current workflow/step plus pending, running, completed, failed, paused, and aborted states. |
| Runtime controls | Pause/resume and abort controls | Plan `Validate`, `Run`, `Pause`, `Resume`, `Abort`, and `Reset` with explicit semantics. |
| Logs / Results | Per-run logs, step history, and output visibility | Make workflow, device, safety, error, and result information directly visible. |

### Intentionally not adopted

- N-AutoLab remains a planned desktop Qt application; it is not changed to Flask or a web application.
- IvoryOS templates, JavaScript, routes, database models, and runner code are not copied.
- Flask, Socket.IO, SQLAlchemy, optimizers, and web deployment are not Phase 0 dependencies.
- GUI representation does not define or own the recipe/workflow engine.

## N-AutoLab Reference Allocation

| N-AutoLab concern | Primary reference | Secondary reference | Contract outcome |
| --- | --- | --- | --- |
| Device/backend boundary | PyLabRobot | N-AutoProv V1 behavior | General device capability with simulation/real backends; vendor code isolated. |
| Station/resource model | PyLabRobot | Orca | General station/resource relationships plus registry and transport graph concepts. |
| Transport | Orca | N-AutoProv V1 robot behavior | Robot is one possible transporter; logical moves precede motion primitives. |
| Recipe/workflow/execution | Orca | IvoryOS UX | Recipe intent resolves to executable workflows with visible status. |
| Event visibility | Orca | IvoryOS UX | Event-driven status outside widgets, presented clearly in desktop GUI. |
| Simulation/visual state | PyLabRobot | IvoryOS UX | No-hardware development with truthful simulated state and operator visibility. |
| Hardware safety/migration | N-AutoProv V1 | N-AutoLab contract | Study and selectively rewrite validated behavior; do not inherit V1 architecture. |

## Phase 1A Architecture Realization

Phase 1A turns the previously recorded concepts into original N-AutoLab code:

| N-AutoLab implementation | Reference concept | Phase 1A boundary |
| --- | --- | --- |
| `Sample`, `Station`, `Device` | PyLabRobot resource/device separation | General-purpose pure Python data and invariants; no PyLabRobot dependency or copied taxonomy. |
| `SampleRegistry`, `StationRegistry`, `DeviceRegistry` | Orca registry/lookup concept | Small owned in-memory registries with unique ids; no Orca source, scheduling, or AGPL implementation. |
| `LabState` atomic placement | Resource orchestration concepts | Original canonical state API preserving sample/station agreement; no workflow execution or transport. |
| `Action`, `Recipe`, `RecipeStep` | Orca definition/runtime separation | Declarations only; no executor, event system, or device calls. |
| Serialized `to_dict` views | PyLabRobot serialization concept | Simple explicit domain views; no class discovery or third-party serializer. |
| Future GUI-facing state | IvoryOS visibility UX | Models expose truthful states, but Phase 1A adds no GUI or web technology. |

The new runtime dependency is only PyYAML for the portable demo configuration;
none of the reference projects is installed as a dependency.

## Phase 1A.1 Resource Hierarchy Realization

Phase 1A.1 extends the original N-AutoLab implementation without copying source
from either reference project:

| N-AutoLab implementation | Reference concept | N-AutoLab decision |
| --- | --- | --- |
| `Station` → `StationSlot` | PyLabRobot parent/child Resource hierarchy and resource position abstraction | Model general station instances and exact sample-holding slots, not liquid-handling labware or deck classes. |
| Slot `pose_reference` | PyLabRobot relative/resource position concept | Store semantic identifiers only; no third-party positioning code or real coordinates. |
| `StationSlotRegistry` | Orca ResourceRegistry identity/lookup concept | Validate parent existence and unique station-local slot index with original small in-memory code. |
| Multi-instance Station queries | Orca SystemMap/resource availability concepts | Deterministically list Stations by type and available Slots by Station/type; no graph, scheduler, reservation, or Orca implementation. |
| Slot-level canonical state | N-AutoLab ADRs 0006–0007 | Store Sample location at exact Slot and derive parent Station aggregates without duplicate occupancy state. |

The planned Phase 1B Resource Resolver will distinguish exact Slot, exact
Station/auto Slot, and Station type/auto Station+Slot intent. Phase 1A.1 defines
only the serializable intent and sorted read queries.

## License Boundary

Architecture ideas and publicly documented behavior were studied. Implementations will be original N-AutoLab code unless a later dependency or source reuse decision records license compatibility, attribution, distribution obligations, and approval. Orca's AGPL-3.0-only implementation is specifically excluded from copying.
