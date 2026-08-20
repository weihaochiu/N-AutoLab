# Capability Matrix

Status vocabulary:

- `SPECIFIED`: architecture and acceptance direction exist; implementation does not.
- `IMPLEMENTED`: the scoped software capability exists and has passing tests.
- `NOT_IMPLEMENTED`: no trustworthy implementation exists.
- `SIMULATED`: an explicit simulation exists and is labeled.
- `REAL_AVAILABLE`: a real backend exists and has passed required validation.
- `ERROR`: a configured capability is unhealthy or invalid.

`IMPLEMENTED` for a model/query does not imply resource resolution, workflow
execution, simulation, GUI availability, or real-hardware readiness.

| Capability | Architecture Defined | Simulation | Real Hardware | GUI | Tests | Status | Target Phase | Reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| General-purpose Sample model | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A | N-AutoLab |
| Station instance model | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 | PyLabRobot concept + ADR 0007 |
| StationSlot model | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 | PyLabRobot hierarchy concept + N-AutoLab |
| Multi-Station same type | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 | Orca lookup concept + N-AutoLab |
| Multi-Slot Station | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 | N-AutoLab |
| Slot-level Sample location | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 | ADRs 0006–0007 |
| Station aggregate occupancy | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 | ADR 0007 |
| Slot availability query | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 | Orca availability concept + N-AutoLab |
| Station-type query | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 | Orca registry concept + N-AutoLab |
| Device description/state model | YES | N/A | NO | NO | YES | IMPLEMENTED | 1A | PyLabRobot concept + N-AutoLab |
| Device/backend pattern | YES | NO | NO | NO | Boundary tests | SPECIFIED | 2+ | PyLabRobot |
| SampleRegistry | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A | Orca registry concept |
| StationRegistry | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A | Orca registry concept |
| StationSlotRegistry | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 | Orca registry concept + N-AutoLab |
| Resource relationship deletion guards | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 Hardening | N-AutoLab ADRs 0006–0007 |
| Strict resource enable-state validation | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 Hardening | N-AutoLab |
| Nested Slot ownership validation | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 Hardening | N-AutoLab ADR 0007 |
| Injected registry identity preservation | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 Hardening | N-AutoLab |
| DeviceRegistry | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A | Orca registry concept |
| Action declaration | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A | Orca concept + N-AutoLab |
| Destination intent declaration | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A.1 | N-AutoLab |
| Recipe / RecipeStep declaration | YES | N/A | N/A | NO | YES | IMPLEMENTED | 1A | N-AutoLab; V1 reference |
| Multi-station demo config v2 | YES | N/A | DISABLED | Console diagnostic | YES | IMPLEMENTED | 1A.1 | N-AutoLab |
| Resource Resolver | YES | NO | N/A | NO | NO | NOT_IMPLEMENTED | 1B | N-AutoLab + Orca concepts |
| StationMap | YES | NO | NO | NO | NO | SPECIFIED | 1B | PyLabRobot + Orca; V1 data reference |
| TransportGraph | YES | NO | NO | NO | NO | SPECIFIED | 1B | Orca SystemMap concept |
| Transporter pattern | YES | NO | NO | NO | NO | SPECIFIED | 1B | Orca |
| Workflow model | YES | NO | N/A | NO | NO | NOT_IMPLEMENTED | 1B | Orca concept |
| WorkflowExecutor | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 1B | Orca concept |
| Event system | YES | NO | N/A | NO | NO | NOT_IMPLEMENTED | 1B | Orca concept |
| Preflight | YES | NO | NO | NO | NO | SPECIFIED | 1B | N-AutoLab + V1 safety behavior |
| SimulationTransporter | YES | NO | N/A | NO | NO | NOT_IMPLEMENTED | 1B | Orca + N-AutoLab |
| Workflow UX | YES | NO | N/A | NO | NO | SPECIFIED | 1C | IvoryOS UX |
| Devices Page / direct control UX | YES | NO | NO | NO | NO | SPECIFIED | 1C | IvoryOS UX |
| GUI | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 1C | IvoryOS UX + N-AutoLab |
| SimulationRobotBackend | YES | NO | N/A | NO | NO | NOT_IMPLEMENTED | 2 | PyLabRobot pattern |
| RealRobotBackend | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 2 | V1 behavior reference |
| Spin coater hardware | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 4 | V1 incomplete reference |
| Hot plate hardware | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 5 | V1 behavior reference |
| Production recipe workflow | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 6 | N-AutoLab |
| D405 vision correction | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 7 | V1 behavior reference |
| OtO spectrometer | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 8 | V1 placeholder only |
| Experiment/sample provenance | YES | NO | N/A | NO | NO | NOT_IMPLEMENTED | 9 | N-AutoLab |
| Closed-loop optimization | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 10 | Future evaluation |
| Architecture dependency guards | YES | N/A | N/A | N/A | YES | IMPLEMENTED | 1A.1 | N-AutoLab |
| Windows Phase 1A.1 launcher | YES | N/A | DISABLED | Console status only | Manual check | IMPLEMENTED | 1A.1 | N-AutoLab |
