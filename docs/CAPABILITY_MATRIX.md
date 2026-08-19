# Capability Matrix

Status vocabulary:

- `SPECIFIED`: architecture and acceptance direction exist; implementation does not.
- `NOT_IMPLEMENTED`: no trustworthy implementation exists.
- `SIMULATED`: an explicit simulation exists and is labeled.
- `REAL_AVAILABLE`: a real backend exists and has passed the required validation.
- `ERROR`: a configured capability is unhealthy or invalid.

Phase 0 uses `YES`/`NO` only to report evidence, not readiness.

| Capability | Architecture Defined | Simulation | Real Hardware | GUI | Tests | Status | Target Phase | Reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| General-purpose Sample model | YES | NO | N/A | NO | NO | SPECIFIED | 1 | N-AutoLab |
| Station model | YES | NO | N/A | NO | NO | SPECIFIED | 1 | PyLabRobot resource concepts + N-AutoLab |
| Resource relationships | YES | NO | N/A | NO | NO | SPECIFIED | 1 | PyLabRobot |
| Device abstraction | YES | NO | NO | NO | NO | SPECIFIED | 1 | PyLabRobot |
| Device/backend pattern | YES | NO | NO | NO | NO | SPECIFIED | 1 | PyLabRobot |
| Device implementation state | YES | NO | NO | NO | NO | SPECIFIED | 1 | N-AutoLab |
| SampleRegistry | YES | NO | N/A | NO | NO | NOT_IMPLEMENTED | 1 | Orca registry concept |
| StationRegistry | YES | NO | N/A | NO | NO | NOT_IMPLEMENTED | 1 | Orca registry concept |
| DeviceRegistry | YES | NO | N/A | NO | NO | NOT_IMPLEMENTED | 1 | Orca registry concept |
| StationMap | YES | NO | NO | NO | NO | SPECIFIED | 1 | PyLabRobot + Orca; V1 data reference |
| TransportGraph | YES | NO | NO | NO | NO | SPECIFIED | 1 | Orca SystemMap concept |
| Transporter pattern | YES | NO | NO | NO | NO | SPECIFIED | 1 | Orca |
| Action model | YES | NO | N/A | NO | NO | SPECIFIED | 1 | Orca + N-AutoLab |
| Recipe model | YES | NO | N/A | NO | NO | SPECIFIED | 1 | N-AutoLab; V1 migration reference |
| Workflow model | YES | NO | N/A | NO | NO | SPECIFIED | 1 | Orca |
| WorkflowExecutor | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 1 | Orca concept |
| Event system | YES | NO | N/A | NO | NO | NOT_IMPLEMENTED | 1 | Orca concept |
| Preflight | YES | NO | NO | NO | NO | SPECIFIED | 1 | N-AutoLab + V1 safety behavior |
| Workflow UX | YES | NO | N/A | NO | NO | SPECIFIED | 1 | IvoryOS UX |
| Devices Page / direct control UX | YES | NO | NO | NO | NO | SPECIFIED | 1+ | IvoryOS UX |
| Logs / result visibility | YES | NO | NO | NO | NO | SPECIFIED | 1+ | IvoryOS UX |
| SimulationTransporter | YES | NO | N/A | NO | NO | NOT_IMPLEMENTED | 1 | Orca + N-AutoLab |
| SimulationRobotBackend | YES | NO | N/A | NO | NO | NOT_IMPLEMENTED | 2 | PyLabRobot pattern |
| RealRobotBackend | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 2 | V1 behavior reference |
| Spin coater | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 4 | V1 incomplete reference |
| Hot plate | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 5 | V1 behavior reference |
| Production recipe workflow | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 6 | N-AutoLab |
| D405 vision correction | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 7 | V1 behavior reference |
| OtO spectrometer | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 8 | V1 placeholder only |
| Experiment/sample provenance | YES | NO | N/A | NO | NO | NOT_IMPLEMENTED | 9 | N-AutoLab |
| Closed-loop optimization | YES | NO | NO | NO | NO | NOT_IMPLEMENTED | 10 | Future evaluation |
| Project structure/import | YES | N/A | N/A | N/A | YES | SPECIFIED | 0 | N-AutoLab |
| Windows Phase 0 launcher | YES | N/A | DISABLED | Console status only | Manual check | SPECIFIED | 0 | N-AutoLab |
