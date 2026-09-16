# RQM OpenQSE Adapter

Experimental RQM implementation demonstrating integration of quaternionic compilation with the OpenQSE compiler/tool-pipeline architecture.

RQM owns this implementation. OpenQSE is the architectural and interoperability context. This repository is an experimental integration point that compiler researchers can clone, run, inspect, and discuss. It is **not** an official OpenQSE compiler, standard, or endorsed reference implementation.

## What it does

This package is a compiler/tool-pipeline adapter:

- **Quaternionic frontend** accepts a small explicit RQM program (named gates, native `u1q` unit-quaternion operations, measurement, metadata).
- **Quaternionic IR** stores modules, qubits, operations, operands, parameters, attributes, and target requirements.
- **Compiler passes** run a real but intentionally simple pipeline: validate → canonicalize → lower.
- **Target model** records architecture, qubit capacity, supported operations, connectivity, and accepted payload formats. It does not schedule resources.
- **OpenQSE adapter** emits an OpenQSE-compatible JSON artifact: standard named operations or explicit unitaries, resource metadata, diagnostics, and provenance.
- **Local simulator backend** executes the emitted payload with an ideal statevector so the pipeline produces observable computational-basis probabilities.

Quaternionic mathematics stay inside the adapter. The OpenQSE-facing artifact does not require a downstream runtime to understand quaternions.

## What it does not do

- Implement the OpenQSE runtime
- Replace vendor compilers
- Implement resource scheduling or allocation
- Implement hardware control electronics
- Define the OpenQSE architecture
- Claim official OpenQSE status, approval, or standardization
- Provide a complete quaternionic programming language
- Implement mid-circuit feed-forward, QEC, or FTQC compilation

## Architecture

```
Application / RQM Quaternionic Program
                |
                v
      Quaternionic Frontend
                |
                v
        Quaternionic IR
                |
                v
      RQM Compiler Passes
         validate
         canonicalize
         lower
                |
                v
      RQM OpenQSE Adapter
                |
                v
   OpenQSE-compatible payload
     (named ops, unitaries,
      target metadata, diagnostics)
                |
                v
   Existing compiler/backend
     (local statevector in this repo)
                |
                v
             QPU
         or simulator
```

See [docs/architecture.md](docs/architecture.md) and [docs/openqse-integration.md](docs/openqse-integration.md).

## Clean ecosystem demonstration

The interoperability demonstration is a separate, fail-closed path:

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

It does not reimplement sibling mathematics. A capability is recorded only when
it is installed, imported, executed, and verified. Required capabilities that
were only imported fail the run.

From a completely fresh environment:

```bash
./scripts/verify_clean_ecosystem.sh
```

That script clones the sibling RQM repositories, creates a clean virtualenv,
installs them from source in dependency order, runs import checks, the adapter
test suite, `examples/conformance/run.py`, and the sibling package tests.

`rqm-optimize` is exercised only after Qiskit lowering, as backend-adjacent
compression. It is not injected into the backend-neutral compiler path.

## Quick start

Python 3.10+ is required for the standalone adapter. The ecosystem demonstration
requires Python 3.11+ because the sibling RQM packages do. Numpy is the only
runtime dependency of the adapter itself.

```bash
git clone https://github.com/RQM-Technologies-dev/openqse-rqm-adapter.git
cd openqse-rqm-adapter
python3 -m pip install -e ".[dev]"
```

Run the tests:

```bash
python3 -m pytest
```

Run a bundled example:

```bash
python3 examples/basic_quaternionic/run.py
python3 examples/bell/run.py
python3 examples/openqse/run.py
```

Generate and inspect an OpenQSE-compatible adapter artifact:

```bash
python3 scripts/run_demo.py openqse --save /tmp/rqm-openqse-artifacts
python3 -m json.tool /tmp/rqm-openqse-artifacts/openqse-payload.json
```

Minimal Python usage:

```python
from rqm_openqse_adapter import compile, local_simulator_target
from rqm_openqse_adapter.frontend import QuaternionicProgram

program = QuaternionicProgram(name="bell", num_qubits=2, num_clbits=2)
program.h(0)
program.cx(0, 1)
program.measure_all()

result = compile(program, local_simulator_target(), execute=True)
print(result.payload.to_json())
print(result.execution.probabilities)
```

## Current status

This repository is an **experimental prototype**.

The baseline is intentionally small: a documented quaternionic IR, three compiler passes, an OpenQSE-compatible JSON payload, and a local simulator. It is suitable for inspection and interoperability discussion, not production compilation or hardware submission.

The previous contents of this repository were OpenQSE Compiler Working Group notes. Those notes are preserved under [`legacy/openqse-working-group/`](legacy/openqse-working-group/) and are not part of the adapter implementation.

## Roadmap

- Richer quaternionic IR (control flow, mid-circuit measurement, extra native ops)
- Additional RQM compiler passes (fusion, commutation, mapping)
- Qiskit integration
- OpenQASM integration where technically appropriate
- MLIR integration
- Richer target capability handling
- Additional simulator and backend support
- QPU integration
- Hybrid classical/quantum support
- Error correction / FTQC-aware compilation
- OpenQSE interoperability experiments with ORNL, HPE, and other compiler groups

The standalone adapter still compiles a small quaternionic IR for OpenQSE-compatible payloads. Production math and backend bridges belong to the sibling packages (`rqm-core`, `rqm-circuits`, `rqm-compiler`, `rqm-entanglement`, `rqm-qiskit`, `rqm-optimize`). The clean-ecosystem demonstration uses those packages as the real compilation path.

## License

Apache License 2.0. See [LICENSE](LICENSE).
