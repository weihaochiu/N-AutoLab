# ADR 0006 — Canonical Location and Occupancy State

## Status

Accepted

## Context

A sample location and a station's occupants describe the same relationship.
Allowing callers to mutate either field independently would create silent state
divergence and unreliable capacity checks.

## Decision

Expose `Sample.current_location` and `Station.occupant_ids` as read-only public
views. `LabState.place_sample`, `remove_sample`, and `relocate_sample` are the
canonical mutation API. They validate every expected failure before changing
state, then update both views and sample history together.

## Consequences

Resource transitions are deterministic and testable without hardware. Domain
objects retain small private mutation hooks for `LabState`; application,
workflow, GUI, and configuration code must use the canonical API. Process-level
concurrency and persistence transactions remain future decisions.

## References

- `ARCHITECTURE.md` §6
- Orca registry/resource-orchestration concept (concept only; no copied code)
- `docs/REFERENCE_ARCHITECTURE.md`
