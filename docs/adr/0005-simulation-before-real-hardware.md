# ADR 0005 — Simulation Before Real Hardware

## Status

Accepted

## Context

Workflow, resource, and GUI behavior must be testable without laboratory hardware, and hardware integration must not be the first validation environment.

## Decision

Whenever practical, implement a truthful simulation backend before the corresponding real backend. Simulation uses the same abstraction, reports `SIMULATED`, supports fault injection, and never activates automatically after real connection failure.

## Consequences

Most behavior can be developed safely and deterministically. Simulation fidelity must be specified, and real hardware still requires separate staged validation.

## References

- PyLabRobot device-free development and visualizer concepts
- `docs/ROADMAP.md`
