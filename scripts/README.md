# Scripts

`show_demo_lab_state.py` loads and prints the Phase 1 station/slot hierarchy. It
does not connect to hardware, move samples, or execute a workflow.

`backup_commit.py` creates and verifies the exact-commit archive required by the
tracked pre-push hook. `install_git_hooks.py` activates `.githooks` for this
repository.
