# Scripts

`show_demo_lab_state.py` loads and prints the Phase 1 station/slot hierarchy. It
does not connect to hardware, move samples, or execute a workflow.

`backup_commit.py` creates and verifies exact-commit archives. In pre-push mode
it reads Git ref updates from stdin and backs up each unique non-deletion local
SHA rather than assuming HEAD. `install_git_hooks.py` activates `.githooks` for
this repository.
