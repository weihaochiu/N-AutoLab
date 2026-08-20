# ADR 0007 — Station Instance and Slot Resource Hierarchy

## Status

Accepted

## Context

Automation must distinguish multiple same-type station instances, multiple
sample positions per station, and one semantic robot pose per position. A flat
station occupant list cannot say which physical position holds each sample and
cannot safely support future deterministic allocation.

## Decision

Adopt `Lab → Station instance → StationSlot → Sample`. Canonical Station IDs use
`<station_type>_<instance_number>`; canonical Slot IDs use
`<station_id>.slot_<NN>`. `Sample.current_location` always references an exact
Slot. Slot state is canonical; Station occupancy/capacity are derived from child
slots through `LabState`. GUI shorthand remains display data only.

Devices remain separate: a Station may reference a primary device, and a Device
may conceptually serve multiple Stations. Phase 1A.1 adds deterministic read
queries, not resource resolution, reservations, scheduling, or execution.

## Consequences

N-AutoLab supports multiple hot plates, variable slot counts, exact semantic
poses, capacity greater than one per slot, and deterministic future allocation.
The resource model is slightly more complex, and Phase 1B must distinguish exact
Slot, exact Station/auto Slot, and Station type/auto Station+Slot intentions.

## References

- PyLabRobot resource hierarchy concept (concept only; no copied code)
- Orca SystemMap and ResourceRegistry concepts (concept only; no copied code)
- ADR 0006
- `docs/REFERENCE_ARCHITECTURE.md`
