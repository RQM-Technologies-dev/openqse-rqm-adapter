# OpenQSE integration

This document describes the experimental integration contract implemented by
the RQM OpenQSE Adapter.

**Assumption vs implementation:** OpenQSE does not currently define a frozen
payload schema in this repository. The artifact format below is an RQM
prototype shaped for an OpenQSE-style compiler/tool pipeline. It is
OpenQSE-compatible in intent, not an official OpenQSE standard.

```
Input
  |
  v
RQM Quaternionic IR
  |
  v
Adapter
  |
  +--> artifact
  +--> target metadata
  +--> diagnostics
  |
  v
downstream compiler/backend
```

## Input

Implemented:

- `QuaternionicProgram` builder
- dict/JSON ingest of a small operation list
- conversion to `Module` IR

Assumed / not implemented:

- `rqm-circuits` wire-format import
- OpenQASM 3 ingest
- hybrid host-language embeddings

## RQM quaternionic IR

Implemented: modules, qubits, clbits, operations, operands, parameters,
attributes, source metadata, target requirements. JSON serialization is for
debugging.

See [quaternionic-ir.md](quaternionic-ir.md).

## Adapter

Implemented public API:

```python
compile(program, target, execute=False)
lower(program_or_ir, target)
emit(program_or_ir, target)
validate(program_or_ir, target)
```

`OpenQSEAdapter` exposes the same methods as an object.

The adapter:

- accepts RQM IR
- validates target assumptions
- runs required lowering
- produces a backend-facing payload
- produces metadata / resource estimates
- reports unsupported constructs as diagnostics or `UnsupportedConstructError`

It does not call an OpenQSE service. There is no network protocol here.

## Artifact

Implemented JSON object with:

| Field | Purpose |
| --- | --- |
| `schema` | `rqm-openqse-payload/v0.1` |
| `format` | `openqse-compatible-circuit/v0.1` |
| `status` | `experimental` |
| `disclaimer` | states this is not an official OpenQSE artifact |
| `circuit` | named instructions; `u1q` becomes `op: unitary` |
| `target` | copy of the `Target` model |
| `resources` | qubit/clbit counts, depth estimate, required ops |
| `diagnostics` | errors/warnings/info from the pipeline |
| `provenance` | RQM adapter name, version, owner, pass list |

Quaternion attributes are stripped at this boundary.

## Target metadata

Implemented fields: name, architecture, modality, qubit count, supported
operations, connectivity (`all-to-all` or undirected edges), accepted payload
formats, constraints, metadata, version.

Not implemented: live resource queries, calibration ingestion, QRI transport.

## Diagnostics

Implemented codes include unknown operations, out-of-range qubits, missing
parameters, non-unit quaternions, target capacity, unsupported-on-target, and
connectivity failures.

## Downstream compiler/backend

Implemented: `LocalStatevectorBackend`, an ideal RQM-owned simulator.

Not implemented: vendor compiler submission, QPU execution, OpenQSE runtime
handoff.

## Honesty constraints

- Two-qubit gates are ordinary named gates. This prototype does not invent a
  quaternionic two-qubit algebra.
- The Bell example is `H` then `CX`. The simulator result matches that
  conventional sequence.
- Passes are real but not sophisticated optimizations.
