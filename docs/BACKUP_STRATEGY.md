# Repository Backup Strategy

## Purpose

N-AutoLab uses a small, auditable backup approach during early development. Git history and a second local copy protect source and documentation; runtime artifacts are handled separately.

## Source Control

- GitHub repository `weihaochiu/N-AutoLab` is the remote source-control location.
- `main` must contain reviewed, tested commits and must never be force-pushed during normal work.
- After a push, compare the local commit SHA with `origin/main`.
- Tags or releases may later mark hardware-validated milestones.

GitHub is remote source control, not the only backup of machine-local calibration or experimental data.

## Recommended Local Backup

Maintain a periodic mirror or copy on a different physical disk or managed backup location, for example a user-selected directory outside the working repository. The exact destination is machine policy and must not be hard-coded into the project.

A source backup should be based on a known commit or Git bundle/mirror, not a ZIP of an arbitrary dirty working tree. Never include credentials, machine-local device settings, licensed vendor SDK files, or ignored runtime data by accident.

## What Is Not Committed

The following stay out of source control:

- `.venv/`, caches, build output, and package metadata;
- `logs/` and `output/`;
- `backup/` and `BACKUP/`;
- machine-local addresses, ports, secrets, calibration, teach points, and runtime state;
- vendor DLLs, SDK archives, installers, manuals, or binaries without redistribution approval;
- experimental raw data unless a future provenance/storage policy explicitly says otherwise.

These categories need their own laboratory data and machine-configuration backup policy before real operation.

## Push Safety

Before every push:

1. inspect status and the complete staged diff;
2. run hardware-safe tests and documentation/structure checks;
3. confirm no local configuration, secrets, logs, outputs, backups, SDKs, or temporary clones are staged;
4. commit intentionally;
5. push without force;
6. fetch or query the remote and verify its SHA.

## Future Automation

A pre-push safety gate and exact-commit backup automation are tracked in `NAL-INFRA-001`. Phase 0 specifies the behavior but intentionally does not add a complex backup framework. Future automation must be recoverable, testable, exclude local/secret/vendor artifacts, and never bypass normal Git review.
