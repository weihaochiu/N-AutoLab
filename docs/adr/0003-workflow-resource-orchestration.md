# ADR 0003 — Workflow and Resource Orchestration

## Status

Accepted

## Context

Recipes must coordinate samples, stations, devices, and transport without embedding robot commands or raw coordinates.

## Decision

Separate user `Recipe` intent, atomic `Action` definitions, resolved executable `Workflow`, and `WorkflowExecutor`. Use registries, `StationMap`, `TransportGraph`, and `Transporter` roles to resolve resources. Workflows request logical operations such as `MoveSample`.

## Consequences

Validation, resolution, preflight, status, resource conflicts, and transport become explicit. The model is more structured than direct scripts but remains device- and GUI-independent.

## References

- Orca `main@9cd52e3eac0f365a4f153010dea334ea5b84340d` (architecture concepts only; AGPL source not copied)
- `ARCHITECTURE.md`
