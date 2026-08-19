# ADR 0001 — General-Purpose Laboratory Platform

## Status

Accepted

## Context

N-AutoLab must support many current and unknown materials, samples, processes, devices, and layouts. N-AutoProv V1 is too process- and hardware-specific to serve as the new architecture.

## Decision

Use general domain concepts: `Sample`, `Station`, `Device`, `Resource`, `Transporter`, `Action`, `Recipe`, and `Workflow`. Material- and process-specific details belong in metadata, configuration, recipe content, or later extensions—not Core types.

## Consequences

The core cannot assume glass, perovskite, a robot, a hot plate, or a spin coater. Some use cases require configuration or extension models instead of specialized core classes.

## References

- `ARCHITECTURE.md`
- `docs/V1_REFERENCE_MAP.md`
