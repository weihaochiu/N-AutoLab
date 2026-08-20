# N-AutoLab

Modular Laboratory Automation and Experiment Orchestration Platform

**Current Development Stage:** Phase 1 Complete — Core + Simulation Qt GUI

**Hardware Execution:** Not implemented / disabled

N-AutoLab is a new, general-purpose laboratory automation platform. It is not a simple rewrite of N-AutoProv V1 and does not assume a particular material system, sample shape, process, robot, or instrument.

## Project Vision

The project will provide reusable concepts for samples, stations, devices, actions, recipes, workflows, transport, resources, simulation, safety, and experiment provenance. The same core should eventually support thin-film processing, solution handling, electrochemistry, characterization, closed-loop experiments, and devices or processes that are not known today.

## Architecture Overview

The allowed dependency direction is:

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

High-level code depends on abstractions. Vendor SDKs remain behind backend implementations. The GUI displays state and accepts commands but does not own hardware, workflow, sample, station, or business logic. See [ARCHITECTURE.md](ARCHITECTURE.md).

The canonical sample-holding hierarchy is:

```text
Lab → Station instance → StationSlot → Sample
```

Devices remain a separate association and are never interchangeable with a
Station or Slot.

## Reference Projects

- [PyLabRobot](https://github.com/PyLabRobot/pylabrobot): device/backend separation, hierarchical resources, deck relationships, serialization, and hardware-independent development.
- [Orca](https://github.com/Cheshire-Labs/orca): registries, system maps, transporters, actions, workflows, executors, events, and orchestration concepts. Orca is AGPL-3.0-only; N-AutoLab studies concepts and does not copy its implementation.
- [IvoryOS](https://github.com/AccelerationConsortium/ivoryOS): direct-control, workflow-builder, execution-monitoring, runtime-control, logs, and results UX. N-AutoLab remains a planned desktop Qt application.

Exact branches, inspected commits, files, licenses, adopted concepts, and exclusions are recorded in [docs/REFERENCE_ARCHITECTURE.md](docs/REFERENCE_ARCHITECTURE.md).

## Relationship to N-AutoProv V1

[N-AutoProv V1](https://github.com/weihaochiu/N-AutoProv) is a hardware-behavior and migration reference, not the architecture template for N-AutoLab. Hardware behavior, saved data, safety lessons, and incomplete components are mapped in [docs/V1_REFERENCE_MAP.md](docs/V1_REFERENCE_MAP.md).

## Repository Structure

```text
src/nautolab/       Python package, Phase 1A domain models, and registries
tests/              Unit, integration, architecture, and GUI test areas
config/             Portable configuration examples and schemas
docs/               Reference, roadmap, rules, backup, and ADR documents
scripts/            Hardware-safe diagnostics and future maintenance scripts
```

All Python code uses the `nautolab` package and a `src` layout.

## Development Status

Phase 1 provides the full no-hardware path: load the schema-v2 demo laboratory,
edit and validate a canonical Recipe, resolve exact Slot/Station/type intent,
build a typed Workflow, pass aggregate preflight, and execute logical movement
with a `SIMULATED` transporter. The PySide6 interface exposes Dashboard,
Station Map, Samples, Recipe, Workflow, Devices, and Logs pages.

MOVE steps may use `AUTO` source: planning follows that Sample's current
resolved exact Slot, so later steps never predict an earlier auto-allocation.
The GUI offers Instant, 20×, 10×, 5×, and 1× playback; automated execution
defaults to Instant while visible playback remains interruptible and runs in a
worker thread.

Demo devices still report `NOT_IMPLEMENTED` and `DISCONNECTED` truthfully.
No robot, instrument, serial/TCP transport, camera, or vendor library is used.

## Setup

Windows:

```bat
setup_windows.bat
```

The script creates `.venv` and installs the project with development dependencies into that local environment. It does not install packages globally.

Equivalent manual setup:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Run

```bat
run_windows.bat
```

The launcher opens the simulation-only N-AutoLab Qt GUI. It never contacts
hardware.

To inspect the in-memory demo lab:

```powershell
.venv\Scripts\python.exe scripts\show_demo_lab_state.py
```

This diagnostic loads configuration and prints canonical state without moving
a physical or simulated sample.

## Tests

After setup:

```powershell
.venv\Scripts\python.exe -m pytest
```

## Roadmap

Phase 1A/1B/1C are complete at the repository level. The deterministic golden
path is Storage → Hot Plate → Spin Coater → Hot Plate → Storage, and multi-slot
tests prove three samples may occupy one Hot Plate concurrently. Phase 2 robot
integration has not started. Later phases add hardware one family at a time. See
[docs/ROADMAP.md](docs/ROADMAP.md) and
[docs/CAPABILITY_MATRIX.md](docs/CAPABILITY_MATRIX.md).

## Safety

Phase 1 has zero hardware access. No robot, gripper, serial port, TCP device,
vendor DLL, camera, or spectrometer is opened. Future real hardware must use
explicit backends, fail closed, expose truthful implementation and connection
states, pass preflight, and have tests plus operator-visible status.
