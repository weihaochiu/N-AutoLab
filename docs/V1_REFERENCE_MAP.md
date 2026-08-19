# N-AutoProv V1 Reference Map

Inspection date: 2026-08-20 (Asia/Taipei)

## Reference Identity

| Field | Value |
| --- | --- |
| Local reference | `D:\Github\N-AutoProv` |
| GitHub reference | <https://github.com/weihaochiu/N-AutoProv> |
| Branch inspected | `chore/backup-and-baseline-review` |
| Commit inspected | `0f1d14eecbbd264d5dd1bf9e2fee367d723a4030` |
| Role | Hardware Behavior Reference / Migration Reference |
| Explicit non-role | Architecture template |

The V1 repository was inspected read-only and was not modified. “Validated behavior” below means behavior supported by the inspected source, configuration examples, ADRs, or baseline review. Nothing was revalidated on real hardware during Phase 0.

Allowed migration methods:

- `STUDY`: extract requirements and safety behavior before designing new code.
- `PORT`: move a small, sufficiently isolated behavior after review and tests.
- `MIGRATE_DATA`: transform user-owned configuration, recipes, calibration, or history into a new schema.
- `REWRITE`: implement the capability against N-AutoLab abstractions without carrying V1 structure forward.
- `REFERENCE_ONLY`: consult for UX, terminology, or operational context; do not migrate code/data by default.
- `DROP`: intentionally omit obsolete or unsafe behavior.

## Mapping

| V2 Component | V1 Reference Path | V1 Purpose | Validated Behavior | Future Migration Method | Priority | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Robot connection | `drivers/arm_driver.py`; `infrastructure/robot_startup_safety.py`; `docs/adr/ADR-013-Robot-Startup-Preflight-And-C22-Recovery.md` | Connect xArm Lite6 and read controller status | Connection is non-moving; controller errors are exposed; motion remains disabled until explicit operator action | STUDY | High | Preserve fail-closed behavior through a future `RealRobotBackend`; do not preserve V1 composition. |
| Robot motion | `drivers/arm_driver.py`; `infrastructure/robot_safe_motion.py`; ADRs 015, 018–021, 025 | Cartesian/joint commands, Safe-Z paths, initial return, command serialization | SDK calls are locked; controller/operator gates protect axis motion; high-level saved-point moves use lift/transit/descend | STUDY | High | Re-express as transporter/backend capabilities; workflows must not call these primitives. |
| Gripper | `drivers/arm_driver.py`; `arm_subpanels/tab_gripper.py`; `docs/adr/ADR-026-Lite6-Vacuum-Gripper-SDK-Control.md` | Mechanical end-effector operation through xArm API | Documented mapping uses `set_vacuum_gripper(True/False)` for close/open and blocks on controller faults | STUDY | High | Hardware-specific naming and semantics require field revalidation before a real backend. |
| Teach points | `drivers/arm_driver.py`; `arm_subpanels/tab_cartesian.py`; `config/examples/arm_config.example.json` | Save TCP poses, Safe-Z, and initial position | Named saved points are resolved separately from high-level routes; Safe-Z is a plane, not a saved XYZ point | MIGRATE_DATA | High | Build an explicit, versioned migration into `pose_reference` data; never copy machine-local paths. |
| Station positions | `logic/station_map.py`; `config/examples/station_map.example.json`; `ui_components/station_map_panel.py`; ADRs 023–024 | Map logical station ids to saved-point names | Station map references saved points rather than duplicating coordinates; missing mappings fail preflight | MIGRATE_DATA | High | Data concept is useful; N-AutoLab station/resource model is a rewrite. |
| Safety shutdown | `infrastructure/safe_shutdown_manager.py`; `app.py`; `docs/adr/ADR-022-Safe-Shutdown-Manager.md` | Ordered stop, hot-plate standby, optional guarded robot return, disconnect | Shutdown can block exit when motion is busy or hot-plate standby fails; raw UI close is routed through manager | STUDY | High | Translate requirements per capability; do not assume every N-AutoLab system has robot/hot plate. |
| Emergency handling | `infrastructure/robot_startup_safety.py`; `infrastructure/xarm_error_codes.py`; `drivers/arm_driver.py` | C22/controller-error detection and recovery guidance | C22 blocks motion and requires external/manual recovery; V1 avoids clear-and-continue | STUDY | High | An all-device emergency model is `NOT_IMPLEMENTED_IN_V1`; only robot-specific lessons exist. |
| Recipe | `logic/recipe_factory.py`; `logic/recipe_migration.py`; `logic/recipe_utils.py`; `logic/steps/`; `ui_components/matrix_panel.py`; ADR 029 | Build and normalize spin/anneal/transfer recipe steps | Schema v2 adds explicit station metadata and dry-run migration/validation | MIGRATE_DATA | High | Preserve user recipe meaning through versioned import; rewrite models as general `Action`/`Recipe`/`Workflow`. |
| Station Map | `logic/station_map.py`; `infrastructure/station_preflight.py`; `ui_components/station_map_panel.py`; `config/examples/station_map.example.json` | Resolve logical stations and loading slots for scheduler movement | Required/enabled station checks and saved-point resolution exist; optical station is disabled placeholder | MIGRATE_DATA | High | Do not adopt fixed V1 station ids as core types. |
| GUI | `app.py`; `ui_*.py`; `arm_subpanels/`; `hotplate_subpanels/`; `tabs/`; `ui_components/`; `ui_monitor/` | Tkinter operator application and equipment panels | Direct control, logs, map, recipe matrix, status, and guarded actions provide operational UX evidence | REFERENCE_ONLY | Medium | N-AutoLab plans desktop Qt and a separated application boundary; no Tkinter migration by default. |
| Camera | `tabs/tab_vision.py`; `infrastructure/camera_mock.py` | Vision window, color/depth display, controls, arm-point save | UI displays real or explicit mock frames and exposes exposure/gain/filter controls | REFERENCE_ONLY | Medium | General camera capability and GUI contract must be rewritten; import-time fallback behavior must not hide runtime failure. |
| D405 | `drivers/d405_driver.py`; `tabs/tab_vision.py`; ADRs 009–010 | RealSense D405 connection, frames, depth, filtering | Source configures RealSense streams and exposes frame/distance access | STUDY | Medium | Real device behavior was not exercised in Phase 0; use a future `CameraDevice` backend. |
| Hot Plate | `drivers/hotplate_driver.py`; `hotplate_subpanels/`; `logic/steps/anneal_step.py`; ADR 011 | Modbus RTU temperature read/write and anneal behavior | No automatic simulation fallback; disconnected/simulated production anneal fails closed | STUDY | High | Register map and real behavior require hardware verification before `RealHotPlateBackend`. |
| Spin Coater | `drivers/spin_driver.py`; `ui_spin_panel.py`; `logic/steps/spin_step.py`; ADR 024 | Serial connection shell and planned recipe run contract | `run_program` validates inputs/readiness, but vendor command and stop protocols raise `NotImplementedError` | REWRITE | High | **NOT_IMPLEMENTED_IN_V1** for real vendor execution. Do not treat opening a serial port as hardware readiness. |
| Spectrometer / OtO | `third_party/oto_photonics/README.md`; `docs/OPEN_ITEMS_20260520_OtO_Optical_QC.md`; ADR 029 | SDK placement rules and future optical-QC plan | Optical station is disabled and `hardware_ready=false`; proprietary SDK is not distributed | REWRITE | Medium | **NOT_IMPLEMENTED_IN_V1**. No driver or validated acquisition behavior exists. |
| Configuration | `config.py`; `config/README.md`; `config/examples/*.example.json` | System/device/station settings and local overrides | Machine-local configuration is separated from tracked examples; station map stores references | MIGRATE_DATA | High | Define new schemas and explicit migration; never commit credentials, IPs, ports, or local calibration. |
| Logging | `infrastructure/logging_config.py`; `ui_components/log_window.py`; `logic/pick_stability_test.py` | GUI log events, file logging, and operator test records | UTF-8 file logging and GUI visibility exist; pick tests write structured run outputs | STUDY | Medium | Define event/provenance schemas before porting any log format. |
| Error handling | `infrastructure/robot_startup_safety.py`; `infrastructure/xarm_error_codes.py`; drivers and view models; `docs/reviews/BASELINE_CODE_REVIEW_20260819.md` | Fail-closed driver messages and operator guidance | Robot/hot-plate/spin paths include explicit failures and preflight blockers | STUDY | High | Error taxonomy is device-specific and incomplete; create general typed outcomes in later phases. |
| Event system | `infrastructure/event_bus.py`; `infrastructure/logging_config.py` | Queue UI/log notifications | A small publish/subscribe queue decouples some log presentation | REFERENCE_ONLY | Low | N-AutoLab event contracts are new work; V1 bus is not an architecture template. |
| Scheduling/resource locks | `logic/scheduler.py`; `logic/resource_manager.py`; `logic/sample_task.py` | Run sample tasks and coordinate shared V1 devices | Robot/hot-plate preflight and resource locks exist around a fixed V1 process model | STUDY | Medium | Rewrite against general resources, actions, and transport; no Phase 0 executor implementation. |

## Migration Guardrails

1. Inspect and test behavior before moving any V1 logic.
2. Put vendor calls behind N-AutoLab backend abstractions.
3. Transform data through explicit, versioned import tools; do not load V1 files as native V2 state.
4. Generalize behavior without importing V1's material/process assumptions.
5. Treat every `NOT_IMPLEMENTED_IN_V1` item as new design and validation work.
6. Revalidate safety-critical behavior with simulation and approved hardware plans before real operation.
