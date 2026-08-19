# N-AutoLab Architecture Contract

Status: Accepted for Phase 0
Scope: Mandatory direction for all future implementation

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

Future `Device` specification:

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

N-AutoLab adapts hierarchical resource and deck concepts into its own `Resource`, `Station`, and `StationMap` model. It does not copy a liquid-handling deck model.

Future `Station` specification:

```text
id
display_name
station_type
capacity
occupancy
pose_reference
capabilities
enabled
metadata
```

Robot coordinates must not be distributed through workflow code. A station holds a `pose_reference`; backend- and site-specific configuration resolves that reference. Occupancy and capacity must be explicit and independently testable.

`StationRegistry`, `DeviceRegistry`, `SampleRegistry`, `StationMap`, and `TransportGraph` are Phase 1 or later work. Phase 0 defines only their boundaries and names.

## 7. Sample Contract

The future sample concept must support, without a hard-coded closed enum:

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

## 9. Events and Execution Visibility

A future `EventBus` or `EventDispatcher` decouples workflow/device status publication from GUI presentation. It is not a hidden path for bypassing application or safety policy.

The runtime model must eventually expose:

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

Planned controls are `Validate`, `Run`, `Pause`, `Resume`, `Abort`, and `Reset`. Workflow, device, safety, error, log, and result information must be visible to operators.

## 10. Simulation Contract

Workflow development must be possible with no real hardware. Simulation implementations use the same device/transporter abstractions as real backends and report `SIMULATED` explicitly. Simulation must never be an automatic fallback from failed real hardware.

Whenever practical, simulation is implemented and tested before a real backend. The Phase 1 golden path is simulation-only.

## 11. Safety and Failure Contract

- Phase 0 performs zero hardware access.
- Real commands require explicit real backends, capability checks, connection checks, and preflight.
- Hardware and transport failures propagate as visible errors; they are not rewritten as success.
- Abort and shutdown semantics must be device-aware and fail closed.
- Vendor SDKs, DLLs, addresses, ports, and calibration remain outside Core and Workflow.
- Hardware access tests require a separate, explicit authorization and environment; ordinary tests are hardware-safe.

## 12. Architecture Governance

Major changes must update this document, [docs/REFERENCE_ARCHITECTURE.md](docs/REFERENCE_ARCHITECTURE.md), the relevant ADR, [docs/CAPABILITY_MATRIX.md](docs/CAPABILITY_MATRIX.md), and [OPEN_ITEMS.md](OPEN_ITEMS.md). Third-party implementation cannot be copied without explicit license review.

Phase 0 ends at documentation, package boundaries, launchers, and tests. It does not authorize Phase 1 implementation.
