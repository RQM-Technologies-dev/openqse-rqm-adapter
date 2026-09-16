# Clean ecosystem conformance

This example is the fail-closed OpenQASM 3 interoperability demonstration:

```
OpenQASM 3
  → rqm-qiskit import
  → rqm-circuits
  → rqm-compiler (to_u1q, merge_u1q, sign_canon, cancel_2q)
  → rqm-core quaternion mathematics
  → rqm-entanglement AxisHinge / CartanRelation
  → semantic verification
  → named-gate lowering
  → OpenQASM 3
```

It records each capability as installed, imported, executed, and verified.
Required capabilities that were only imported, not executed, fail the run.

```bash
python3 examples/conformance/run.py
```

Use `scripts/verify_clean_ecosystem.sh` for a completely fresh environment.
That is the same procedure as `.github/workflows/clean-ecosystem-integration.yml`.
The workflow checks siblings out first and then runs the script with
`SKIP_CLONE=1`; locally the script clones or updates them itself. The venv,
install order, tests, and demonstration are identical.
