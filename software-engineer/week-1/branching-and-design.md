# Workflow and design notes

## Branch strategy
- `main`: reviewed, releasable state.
- `feature/<short-task>`: one scoped change.
- `fix/<short-bug>`: one defect correction.
- Open a pull request, describe behavior and evidence, review the diff, then merge. Keep branches short-lived and avoid committing secrets or generated data.

## Calculator and SOLID
Keep parsing, arithmetic operations, and presentation separate. `Calculator` can receive an operation registry, making new operations extendable without editing a long conditional. Validate divide-by-zero at the boundary and keep functions single-purpose.

## Task manager design
`task_manager.py` separates persistence (`load`/`save`) from command parsing and task operations at a small scale. A larger version should use repository and service classes, atomic writes, schema versioning, and unit tests. Current JSON file is local and not safe for simultaneous writers.
