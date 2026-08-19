# ADR 0002 — Device / Backend Separation

## Status

Accepted

## Context

Laboratory capabilities must work with simulations and multiple vendors without exposing SDKs to Core, Workflow, or GUI code.

## Decision

Represent a capability with a hardware-independent `Device` and delegate behavior to an explicit simulation or real `Backend`. Real backends alone may import vendor SDKs, serial/TCP libraries, or DLL boundaries.

## Consequences

Backends require contract tests and truthful implementation/connection states. Failed real hardware never silently falls back to simulation. More adapters are required, but higher layers remain portable.

## References

- PyLabRobot `main@158a0a9001edcfd200edbb6818233b2d6f945f39`
- `docs/REFERENCE_ARCHITECTURE.md`
