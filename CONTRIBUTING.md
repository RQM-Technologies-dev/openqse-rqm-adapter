# Contributing to the RQM OpenQSE Adapter

RQM Technologies owns this implementation. OpenQSE is the architectural
context. Contributions should keep that boundary explicit.

## Local setup

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
python3 scripts/run_demo.py
```

## Design rules

- Keep quaternionic semantics inside the RQM frontend, IR, and passes.
- The OpenQSE-facing payload must expose standard operations, unitaries,
  target metadata, and diagnostics — not quaternion algebra.
- Do not claim official OpenQSE status, approval, or standardization.
- Prefer a small public API: `compile`, `lower`, `emit`, `validate`.
- Label experimental or incomplete behavior honestly.
- Do not add resource scheduling, runtime dispatch, or hardware control.

## Adding code

See [docs/development.md](docs/development.md) for how to add a pass, target,
backend, or adapter translation.

## Tests

New behavior needs tests that check results, not just imports. Run:

```bash
python3 -m pytest
```

## Pull requests

Describe the adapter-boundary impact: what stays RQM-specific, what is emitted
on the OpenQSE-facing side, and what remains unimplemented.
