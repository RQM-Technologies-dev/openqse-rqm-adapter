# Architecture

## Why this adapter exists

RQM Technologies compiles quaternionic representations of ordinary single-qubit
`SU(2)` operations. OpenQSE, as discussed by the compiler working group, is a
middleware compilation layer between SDKs and QPU-facing systems.

Those two concerns should meet at a **compiler/tool-pipeline boundary**, not
inside the OpenQSE runtime. This repository is RQM's experimental adapter at
that boundary.

RQM owns the implementation. OpenQSE is the interoperability context. Nothing
here is an official OpenQSE compiler or standard.

## Where it sits

```
Application / RQM Quaternionic Program
                |
                v
      Quaternionic Frontend     # RQM-specific input
                |
                v
        Quaternionic IR         # RQM-specific IR
                |
                v
      RQM Compiler Passes       # RQM-specific transformations
                |
                v
      RQM OpenQSE Adapter       # this package
                |
                v
   OpenQSE-compatible payload   # standard ops, unitaries, metadata
                |
                v
   Existing compiler/backend
                |
                v
             QPU or simulator
```

The adapter is not a scheduler, runtime, or control-electronics stack.

## What remains RQM-specific

- Quaternionic program construction (`u1q`, documented named-gate quaternion forms)
- The quaternionic IR, including `quaternion` attributes
- Canonicalization that attaches those forms
- Lowering that converts unit quaternions to SU(2) matrices using the RQM convention
- Provenance that identifies RQM Technologies as the owner

## What is exposed to the OpenQSE side

The emitted artifact contains:

- a circuit of **named standard operations** (`h`, `cx`, `measure`, …)
- explicit **2×2 unitaries** for native `u1q` operations
- optional unitaries on named single-qubit gates for verification
- target metadata
- compiler-estimated resource requirements
- diagnostics
- provenance and an experimental disclaimer

It does **not** contain quaternion components. Downstream tools are not asked
to implement quaternion algebra.

## Why the OpenQSE runtime should not need quaternionic semantics

A unit quaternion and an `SU(2)` matrix carry the same single-qubit rotation
information. Once the adapter has lowered that information to named gates or
explicit matrices, a runtime or vendor compiler can consume ordinary quantum
circuit artifacts.

Keeping quaternionic coordinates inside RQM avoids forcing every OpenQSE
component to learn an RQM-specific math convention.

## How target requirements flow

1. The IR records `TargetRequirements` (qubit count, required operations).
2. A `Target` object describes a backend: name, architecture/modality, qubit
   capacity, supported operations, connectivity, accepted payload formats.
3. Validation checks the module against the target.
4. The emitted payload copies the target description and resource estimates.

The adapter does not allocate, reserve, or schedule resources.

## How backend-facing artifacts are produced

```
compile(program, target)
  -> frontend to IR
  -> validate
  -> canonicalize
  -> lower
  -> OpenQSEAdapter.emit
  -> optional LocalStatevectorBackend.run
```

`emit` is the OpenQSE-facing handoff. `execute=True` is a local demonstration
path only.

## Prototype limits

This is a first baseline. It does not yet lower to OpenQASM, Qiskit, MLIR, or
a provider IR. Those are roadmap items, not present capabilities.
