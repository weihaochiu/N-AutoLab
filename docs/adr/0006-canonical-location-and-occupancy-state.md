# ADR 0006 — Canonical Location and Occupancy State

## Status

Accepted; refined by ADR 0007

## Context

A sample location and a station's occupants describe the same relationship.
Allowing callers to mutate either field independently would create silent state
divergence and unreliable capacity checks.

## Decision

The atomic mutation principle remains authoritative. ADR 0007 refines the
location target from parent Station to exact `StationSlot`: public views are
`Sample.current_location` and `StationSlot.occupant_ids`; parent Station
occupancy is derived.

## Consequences

Resource transitions are deterministic and testable without hardware. Domain
objects retain small private mutation hooks for `LabState`; application,
workflow, GUI, and configuration code must use the canonical API. Process-level
concurrency and persistence transactions remain future decisions.

## References

- `ARCHITECTURE.md` §6
- Orca registry/resource-orchestration concept (concept only; no copied code)
- `docs/REFERENCE_ARCHITECTURE.md`
- ADR 0007
