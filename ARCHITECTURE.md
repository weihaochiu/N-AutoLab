# N-AutoLab Architecture Contract

Status: Accepted; Phase 1 implementation recorded
Scope: Mandatory direction for all implementation

## 1. Platform Boundary

N-AutoLab is a modular laboratory automation and experiment orchestration platform. Its core is independent of materials, recipes, equipment vendors, robot models, and laboratory layouts. Domain names must remain general-purpose: `Sample`, `Recipe`, `Station`, `Device`, `Action`, `Workflow`, `Transporter`, and `Resource`.

Core types such as `PerovskiteSample`, `PerovskiteRecipe`, or `PerovskiteStationMap` are forbidden. Material- or process-specific information belongs in configuration, metadata, recipe content, or later extension packages—not in the core architecture.

The core must not assume:

- every sample is glass;
- every process is perovskite-related;
- a robot exists;
- a spin coater exists;
- a hot plate exists;
- one fixed station layout or coordinate system exists.

## 2. Dependency Direction

```text
GUI
 ↓
Application
 ↓
Workflow
 ↓
Core / Resources
 ↓
Device / Transport
 ↓
Backend
 ↓
Hardware
```

Allowed dependencies:

- GUI → Application use cases and read models
- Application → Workflow services
- Workflow → Core and resource models
- Workflow → Device and Transporter abstractions
- Device → Backend abstraction
- Transporter → Backend abstraction
- Real Backend → vendor SDK, serial protocol, TCP protocol, or vendor DLL
- Simulation Backend → deterministic simulation support

Higher layers may depend on abstractions exposed by lower layers. Lower layers must never import or call presentation code.

## 3. Forbidden Dependencies

The following are prohibited:

```text
GUI → vendor SDK
GUI → serial
GUI → robot SDK
GUI → spectrometer DLL

Recipe → vendor SDK
Recipe → robot SDK

Workflow → PyQt widgets

Core → GUI
Core → hardware SDK
```

Direct GUI-to-driver shortcuts are also prohibited even if they appear convenient. Commands pass through application use cases so that validation, safety, status, logging, and tests remain consistent.

## 4. Layer Responsibilities

### GUI

The future desktop Qt GUI displays state, accepts user commands, shows status, and shows errors. It does not own hardware logic, workflow logic, sample state, station state, or business rules.

N-AutoLab follows **backend-first architecture + GUI-visible development**: when a major backend capability is completed, a minimal GUI-visible entry must expose its status and safe controls. This requirement improves observability; it does not move logic into the GUI.

### Application

Application services coordinate user intent, validation, workflow preparation, commands, and query/read models. They form the stable boundary used by GUI or future non-GUI entry points.

### Workflow

Workflow code validates and resolves recipes, acquires resources, coordinates actions and transport, reports state, and delegates actual device operations through abstractions. It contains no widget code and no vendor calls.

### Core / Resources

Core contains stable, general-purpose domain concepts and invariants. Resources describe stations, capacity, occupancy, location references, and capabilities without knowing GUI or hardware SDK details.

### Device / Transport

Devices express domain capabilities. A transporter moves samples/resources between logical locations. A robot may implement the `Transporter` role, but the robot is not the center of the platform.

### Backend / Hardware

Backends translate device capabilities into simulation or vendor-specific behavior. Real hardware is reachable only here. A real backend must fail closed, expose connection and implementation state truthfully, and never silently fall back to simulation.

## 5. Device / Backend Contract

The future pattern is:

```text
RobotDevice
 ├─ SimulationRobotBackend
 └─ RealRobotBackend

HotPlateDevice
 ├─ SimulationHotPlateBackend
 └─ RealHotPlateBackend
```

The same separation applies to spin coaters, spectrometers, cameras, SMUs, pumps, ovens, and unknown future devices. Reference projects are not runtime dependencies.

Phase 1A `Device` description:

```text
id
display_name
device_type
implementation_state
connection_state
capabilities
backend
```

Implementation state vocabulary:

```text
NOT_IMPLEMENTED
SIMULATED
REAL_AVAILABLE
ERROR
```

`READY` must never be used to hide missing implementation, missing hardware, or a failed connection. Connection state is separate from implementation state.

## 6. Resource and Station Contract

N-AutoLab adapts hierarchical resource and deck concepts into its own model. It
does not copy a liquid-handling deck taxonomy or implementation.

The official sample-holding hierarchy is:

```text
Lab
 └── Station instance
      └── StationSlot
           └── Sample
```

`Station` is an identifiable physical/logical work-station instance such as
`hotplate_01`. Its `station_type` remains independently queryable, so multiple
instances such as `hotplate_01` and `hotplate_02` can coexist.

`StationSlot` is an exact sample position such as
`hotplate_02.slot_03`. It owns capacity, occupants, enabled state, capabilities,
and the semantic pick/place `pose_reference`. Every station that can hold a
sample exposes at least one explicit slot; single-position equipment has
`slot_01` rather than a special case.

Phase 1A.1 `Station` instance specification:

```text
id
display_name
station_type
pose_reference
capabilities
enabled
metadata
device_id
display_prefix
```

Phase 1A.1 `StationSlot` specification:

```text
id
display_name
parent_station_id
slot_index
capacity
occupant_ids
pose_reference
enabled
capabilities
metadata
```

Robot coordinates must not be distributed through workflow code. Slot
`pose_reference` is the semantic sample pick/place reference; backend- and
site-specific configuration will resolve it later. A parent Station may retain
an optional service/calibration pose, but it is not a sample location pose.

Phase 1A implements `StationRegistry`, `DeviceRegistry`, and `SampleRegistry` as
deterministic in-memory collections. `StationMap` and `TransportGraph` remain
deferred.

### Canonical slot-level location and occupancy state

`Sample.current_location` stores one exact canonical Slot ID. It never stores a
parent Station ID. `Sample.current_location` and `StationSlot.occupant_ids` are
two read-only public views of one relationship. `resources.LabState` owns the supported
mutation operations:

```text
place_sample
remove_sample
relocate_sample
```

Each operation resolves all resources and validates source agreement, parent
Station enabled state, Slot enabled state, duplicate occupancy, and Slot
capacity before changing either object. A rejected operation leaves both views
and sample history unchanged. The in-memory transaction also restores its
snapshots if an unexpected exception occurs after a private mutation hook has
started changing state.

Relational deletion belongs to `LabState`, not arbitrary caller sequencing. A
placed Sample resource cannot be deleted until it is explicitly removed from
its Slot. A Station cannot be deleted while any child Slot exists; empty Slots
must be removed explicitly first, and occupied Slots remain protected by the
Slot registry. Specialized registry guards prevent the exposed mutable
registries from bypassing this boundary without introducing Registry →
`LabState` callbacks or circular ownership.

When registries are injected into `LabState`, their object identity is
preserved—including empty registries—and the Slot registry is bound to that
same final Station registry instance.

Parent Station occupancy is never stored as a second mutable list. `LabState`
derives total capacity, occupancy, available capacity, and aggregate occupant
IDs from child slots. It also exposes deterministic read-only queries for
available slots by exact Station or Station type. These queries do not reserve,
schedule, resolve workflow intent, or mutate state.

`StationRegistry.list_by_type()` orders Station instances by canonical ID;
`StationSlotRegistry.list_by_station()` orders slots by `slot_index`.
Registries are owned instances, not process-global mutable state.

`Station.enabled`, `StationSlot.enabled`, and any equivalent declarative enable
flag are strict Booleans: only `True` and `False` are valid. Strings, integers,
`None`, and other truthy/falsy substitutes are rejected. For a Slot nested in a
Station configuration, the outer Station owns the parent relationship. An
optional explicit `parent_station_id` is accepted only when it equals the outer
Station ID, and the canonical Slot ID must match that parent and its Slot index.

Device association is a separate relationship: a Station may reference zero or
one primary `device_id`; architecture permits a Device to serve one or more
Stations without adding a reverse-list graph in Phase 1A.1. Station, Slot, and
Device identities are never interchangeable.

This is an in-memory domain transaction boundary, not a resource resolver,
workflow executor, transporter, scheduler, reservation, database transaction,
or hardware command.

## 7. Sample Contract

The Phase 1A sample model supports, without a hard-coded sample-type enum:

```text
id
name
sample_type
current_location
status
metadata
history
```

Possible sample types include substrate, thin film, device, electrode, solution, and custom types. These examples do not form a fixed exhaustive enum in Phase 1.

## 8. Action, Recipe, and Workflow

These terms are not interchangeable:

- **Action:** the smallest atomic domain operation, such as `MoveSample`, `Wait`, `Heat`, `Spin`, `AcquireSpectrum`, `CaptureImage`, or `MeasureIV`.
- **Recipe:** a user-defined description of experimental steps and parameters. A recipe declares intent and must not control hardware directly.
- **Workflow:** the executable form produced after recipe validation, capability resolution, station/resource resolution, and preflight. The future executor receives a workflow, not raw GUI state.

The recipe engine must remain independent of editor representation. A table editor and a future flow editor must produce the same recipe model and must not require different workflow engines.

Workflows request `MoveSample`; they do not issue `robot.move_joint`, `robot.move_line`, or `gripper.open` commands.

Phase 1A.1 represents MOVE_SAMPLE destinations as exactly one declarative
intent:

```text
EXACT_SLOT      hotplate_02.slot_03
EXACT_STATION   hotplate_02          (future auto-slot)
STATION_TYPE    hotplate             (future auto-station + auto-slot)
```

Ambiguous combinations are invalid. This declaration does not perform resource
resolution; Phase 1B consumes deterministic availability queries using the
documented canonical Station ID and Slot-index selection policy.

`MOVE_SAMPLE.source_slot_id` is optional Recipe intent. `None` means AUTO:
planning uses the Sample's current resolved location. A supplied source is an
explicit assertion and fails with `SOURCE_MISMATCH` when it differs. Every
resolved `WorkflowStep.source_slot_id` is an exact Slot, including when Recipe
source is AUTO. Destination auto-allocation therefore never requires a later
Recipe step to predict an earlier Resolver result.

## 9. Events and Execution Visibility

`EventBus` decouples workflow status publication from GUI presentation. Domain
state changes are authoritative; subscriber exceptions are captured as
observable errors and never roll back or corrupt a completed domain transition.
Events are not a hidden path for bypassing application or safety policy.

The Phase 1 runtime model exposes:

```text
Current workflow
Current step
Pending
Running
Completed
Failed
Paused
Aborted
```

Implemented controls are `Validate`, `Run Simulation`, boundary-safe `Pause`,
`Resume`, and `Abort`. `Reset` remains disabled because its semantics are not
defined. Workflow, device, safety, error, and log information is visible.

## 10. Simulation Contract

Workflow development must be possible with no real hardware. Simulation implementations use the same device/transporter abstractions as real backends and report `SIMULATED` explicitly. Simulation must never be an automatic fallback from failed real hardware.

Whenever practical, simulation is implemented and tested before a real backend. The Phase 1 golden path is simulation-only.

Automated simulation defaults to Instant. GUI demonstration may select 20×,
10×, 5×, or 1× accelerated playback without changing Recipe duration. Playback
waits occur only in the worker thread and poll abort at short intervals. Pause
remains a step-boundary request. Preflight requires location readiness only for
Samples referenced by enabled steps; unrelated unlocated Samples are allowed,
while any contradictory canonical location/occupancy state remains global and
fail-closed.

## 11. Safety and Failure Contract

- Phase 1 performs zero hardware access.
- Real commands require explicit real backends, capability checks, connection checks, and preflight.
- Hardware and transport failures propagate as visible errors; they are not rewritten as success.
- Abort and shutdown semantics must be device-aware and fail closed.
- Vendor SDKs, DLLs, addresses, ports, and calibration remain outside Core and Workflow.
- Hardware access tests require a separate, explicit authorization and environment; ordinary tests are hardware-safe.

## 12. Architecture Governance

Major changes must update this document, [docs/REFERENCE_ARCHITECTURE.md](docs/REFERENCE_ARCHITECTURE.md), the relevant ADR, [docs/CAPABILITY_MATRIX.md](docs/CAPABILITY_MATRIX.md), and [OPEN_ITEMS.md](OPEN_ITEMS.md). Third-party implementation cannot be copied without explicit license review.

Phase 1 adds deterministic side-effect-free resource resolution, separate
Recipe and resolved Workflow models, typed observer events, aggregate
simulation preflight, atomic logical transport through `LabState`, workflow
lifecycle execution, application read models, and a PySide6 operator GUI.
Reservation frameworks, production scheduling, real device backends, and all
hardware access remain deferred. The table editor is a Phase 1 representation,
not the canonical Recipe model; future step/flow/timeline views adapt the same
domain model without storing row, column, color, or node position as semantics.
