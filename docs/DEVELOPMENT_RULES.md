# Development Rules

These rules are mandatory unless superseded by an accepted ADR that updates the architecture contract.

## Rule 1 — No business logic in GUI

GUI code displays state, collects input, invokes application use cases, and presents results/errors. It does not own hardware, workflow, sample, station, or safety rules.

## Rule 2 — No hardware SDK in Core

Core and resource packages must not import vendor SDKs, serial libraries, device DLLs, Qt, or concrete backends.

## Rule 3 — Recipe must not directly control hardware

A recipe describes experimental intent. Validation and resolution produce actions/workflows, which delegate capabilities through device/transporter abstractions.

## Rule 4 — All real hardware must use Backend abstraction

Vendor SDK, serial, TCP, DLL, and protocol calls exist only in explicit real backends. No direct calls from GUI, application, workflow, recipe, or core code.

## Rule 5 — Simulation before RealBackend whenever practical

Define and test the capability contract with an explicit simulation before hardware integration. Record justified exceptions in an ADR.

## Rule 6 — No fake READY state

Use truthful implementation states:

```text
NOT_IMPLEMENTED
SIMULATED
REAL_AVAILABLE
ERROR
```

Connection state is separate. Failure to connect a real device must never silently select simulation or report success.

## Rule 7 — Every major capability requires tests

Tests cover domain rules, state transitions, validation, failures, and dependency boundaries. Hardware tests are separate, opt-in, and require explicit authorization.

## Rule 8 — Keep capability and backlog records current

Every major capability change updates:

```text
docs/CAPABILITY_MATRIX.md
OPEN_ITEMS.md
```

## Rule 9 — Keep architecture records current

Major architecture changes update:

```text
ARCHITECTURE.md
docs/REFERENCE_ARCHITECTURE.md
docs/adr/
```

## Rule 10 — Review third-party licenses before reuse

Do not copy third-party implementation without license review. Architecture concepts may be studied and attributed. Dependencies or copied/adapted source require an explicit decision, compatibility review, attribution, and distribution plan. Orca source is AGPL-3.0-only and is not copied.

## Rule 11 — Preserve canonical resource state

Application, workflow, configuration, simulation, and future GUI code must use
`LabState` placement/removal/relocation operations. They must not mutate sample
location or station occupants independently. A rejected transition must not
partially mutate state.

## Rule 12 — Use explicit sample-holding slots

Every Station that can hold a Sample exposes one or more explicit
`StationSlot` resources, including single-position equipment.

## Rule 13 — Sample location is always an exact Slot

`Sample.current_location` stores a canonical Slot ID, never a parent Station ID
or GUI shorthand. Parent Station identity is resolved through the Slot registry.

## Rule 14 — Derive parent Station occupancy

Parent Station capacity, occupancy, availability, and occupants are calculated
from child Slot state. Station must not maintain a second mutable canonical
occupancy list.

## Python and Project Style

- Python 3.11 or newer.
- UTF-8 text.
- Type hints for public interfaces and nontrivial internal code.
- `pathlib` for new filesystem logic.
- `src` package layout with package name `nautolab`.
- `pytest` for tests.
- Focused modules and explicit dependencies.
- No hard-coded local paths such as `D:\...` in runtime code.
- No global mutable runtime state without an accepted, testable design.
- No giant utility module or god object.
- No material-, recipe-, station-, or vendor-specific name in general-purpose Core.

## Safety and Execution Rules

- Ordinary development and tests must perform zero real hardware access.
- Real hardware execution requires explicit configuration, backend selection, connection checks, preflight, operator-visible state, and an approved test/run plan.
- No automatic simulation fallback.
- No success event before the required operation completes successfully.
- Abort, reset, and shutdown semantics must be specified and tested per capability.
- Robot coordinates and other calibration data are referenced, not scattered through workflow code.

## Git and Change Rules

- Inspect `git status` and diff before staging.
- Stage only intentional files; do not include local configuration, credentials, logs, outputs, backups, vendor SDKs, or temporary reference clones.
- Do not use force push for normal development.
- Run relevant hardware-safe checks before every push.
- Verify the remote branch SHA after push.
- Use logical commits; avoid both monolithic unrelated commits and meaningless micro-commits.
