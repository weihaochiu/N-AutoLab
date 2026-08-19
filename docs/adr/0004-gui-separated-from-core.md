# ADR 0004 — GUI Separated from Core

## Status

Accepted

## Context

Operators need direct control, workflow monitoring, logs, results, and errors, but presentation code must not become the hardware or workflow engine.

## Decision

Use a desktop Qt GUI over application use cases and read models. Widgets display state, collect commands, and present outcomes. Major backend capabilities receive minimal GUI-visible status while all business and hardware logic remains outside the GUI.

## Consequences

GUI and backend work can be tested separately. More explicit application boundaries are required. Table and future flow recipe editors share one recipe engine.

## References

- IvoryOS `main@ba3e5940d1aea7faf0b42c8ad8003e4c45b40b7c` (UX reference only)
- `ARCHITECTURE.md`
