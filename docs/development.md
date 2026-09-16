# Development

## Local setup

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
python3 scripts/run_demo.py
./scripts/verify_clean_ecosystem.sh
```

The package uses a `src/` layout. Install it before importing
`rqm_openqse_adapter`.

## Testing

```bash
python3 -m pytest
python3 -m pytest tests/test_end_to_end.py -v
```

Standalone adapter tests cover IR construction, JSON round-trip, validation
failures, pass order, target checks, adapter payload shape, and an end-to-end
Bell compilation.

Ecosystem interoperability tests require the sibling RQM packages installed
from source. Use `scripts/verify_clean_ecosystem.sh` rather than skipping or
mocking those checks.

## Adding a compiler pass

1. Create a class with `name` and `run(module, context)`.
2. Record diagnostics on `context.diagnostics` instead of raising when a
   warning is enough.
3. Insert it in a `PassManager` **after** `validate` and, if it needs
   quaternion attributes, after `canonicalize`.
4. Add a test that checks a behavioral change, not just that the class
   instantiates.

See [compiler-pipeline.md](compiler-pipeline.md).

## Adding a target

Construct a `Target`:

```python
from rqm_openqse_adapter.targets import Target

target = Target(
    name="example-qpu",
    architecture="superconducting",
    modality="physical",
    qubit_count=4,
    supported_operations=["h", "cx", "measure"],
    connectivity=[(0, 1), (1, 2), (2, 3)],
    accepted_payload_formats=["openqse-compatible-circuit/v0.1"],
)
```

Do not add a scheduler. This repository only records target constraints.

## Adding a backend

`LocalStatevectorBackend.run(payload)` is the current execution path. A new
backend should consume the **payload**, not the quaternionic IR. That keeps
quaternionic semantics inside the adapter.

## Adding an adapter translation

`openqse/adapter.py` maps lowered operations to payload instructions:

- named single-qubit gates stay named and may include a `unitary`
- `u1q` becomes `op: "unitary"` with `origin: "u1q"`
- quaternion attributes are dropped

New output formats (OpenQASM, Qiskit, MLIR) should be additional emitters
beside this JSON payload, not replacements for the RQM IR.

## Debugging

- Dump IR with `result.ir_json` or `rqm_openqse_adapter.ir.dumps(module)`
- Dump the artifact with `payload.to_json()`
- Inspect `payload.diagnostics` and `payload.provenance.pipeline`
- Compare IR `attributes.quaternion` with payload instructions to confirm the
  boundary strip
- Run `python3 examples/openqse/run.py` to print both sides of the handoff

If a construct is unsupported, fail closed with a diagnostic. Do not silently
drop operations.
