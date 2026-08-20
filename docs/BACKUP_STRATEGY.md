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

## Automated Pre-Push Gate

`NAL-INFRA-001` is implemented by tracked `.githooks/pre-push`,
`scripts/backup_commit.py`, and `scripts/install_git_hooks.py`. Installation sets
`core.hooksPath=.githooks`. Every normal push first archives `HEAD` with
`git archive`, so dirty or ignored working-tree data cannot enter the ZIP.

The hook reads Git's `<local ref> <local sha> <remote ref> <remote sha>` stdin
records and archives every unique non-deletion local SHA. This covers non-HEAD
branches, tags, and multi-ref pushes; deletion records require no source
archive. HEAD is available only to the explicit manual command path and is
never a pre-push fallback.

The script verifies ZIP CRC and the complete tracked-file list before publishing
the archive, then retains the newest ten `BACKUP/N-AutoLab_*.zip` files. Cleanup
only begins after the new archive passes verification. Archive, verification,
or retention failure exits nonzero and blocks the push. Tests also extract a
backup to prove that its committed files are restorable.
