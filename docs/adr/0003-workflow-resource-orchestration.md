# ADR 0003 — Workflow and Resource Orchestration

## Status

Accepted

## Context

Recipes must coordinate samples, stations, devices, and transport without embedding robot commands or raw coordinates.

## Decision

Separate user `Recipe` intent, atomic `Action` definitions, resolved executable `Workflow`, and `WorkflowExecutor`. Use registries, `StationMap`, `TransportGraph`, and `Transporter` roles to resolve resources. Workflows request logical operations such as `MoveSample`.

## Consequences

Validation, resolution, preflight, status, resource conflicts, and transport become explicit. The model is more structured than direct scripts but remains device- and GUI-independent.

## Phase 1 Realization

Recipe intent resolves against a virtual occupancy snapshot into stable
Workflow/Step IDs. Exact Station selects lowest `slot_index`; Station type sorts
by canonical Station ID then Slot index. Preflight is side-effect-free and REAL
mode is forbidden. The executor delegates movement only to the
`SimulationTransporter`, which updates canonical state through
`LabState.relocate_sample`. Pause is honored at safe step boundaries; failures
stop future steps and remain visible. No reservation/scheduler framework or
hardware backend was introduced.

Final integration permits an omitted Recipe MOVE source. The builder maintains
one planning location per Sample and resolves every Workflow source to an exact
Slot; an explicit source remains a precondition. Preflight uses the same
sequential snapshot, ignores merely unlocated unused Samples, and still blocks
global Sample/Slot contradictions. Simulation duration is virtual for Instant
tests and optionally mapped to interruptible worker-thread playback for the Qt
operator view.

## References

- Orca `main@9cd52e3eac0f365a4f153010dea334ea5b84340d` (architecture concepts only; AGPL source not copied)
- `ARCHITECTURE.md`
