# Experimental Pass Contract

`openqse-rqm-adapter` implements an experimental machine-readable compiler-pass contract inspired by the openQSE Compiler Working Group discussion in `openQSE-Compiler-toolpipeline.md`.

This is an RQM Technologies experiment. It is **not** an official openQSE schema, API, standard, or reference implementation.

## Boundary

The principal interoperability boundary is now OpenQASM 3:

```text
LogicalCircuit / OpenQASM3
          |
          v
rqm.quaternionic.compile
          |
          v
RQM Quaternionic IR
          |
          v
RQM compiler passes
          |
          v
LogicalCircuit / OpenQASM3
```

The internal quaternionic representation is intentionally not imposed on adjacent components.

## Contract

The current contract declares:

- pass: `rqm.quaternionic.compile`;
- version: `0.2.0`;
- input artifact: `LogicalCircuit`;
- input encoding: `OpenQASM3` version 3;
- internal IR: `RQM-Quaternionic-IR/0.1`;
- output artifact: `LogicalCircuit`;
- output encoding: `OpenQASM3` version 3;
- feature profiles: unitary gates and measurement;
- guarantee: computational semantics are preserved for the supported subset and quaternionic semantics remain encapsulated.

## Supported OpenQASM 3 subset

The dependency-free exchange implementation currently supports explicit qubit/bit declarations, `stdgates.inc`, measurement assignment, and the gates `i`, `x`, `y`, `z`, `h`, `s`, `t`, `rx`, `ry`, `rz`, `cx`, `cz`, `swap`, and `barrier`.

Numeric rotation parameters and simple expressions involving `pi` are accepted. Dynamic control, gate definitions, symbolic parameters, modifiers, timing, pulses, and arbitrary OpenQASM 3 syntax are not yet supported. Unsupported syntax fails explicitly rather than being silently discarded.

Native RQM `u1q` operations must be lowered to a portable representation before OpenQASM 3 emission.

## Legacy JSON artifact

The repository may continue to emit its RQM JSON payload for debugging, target metadata, diagnostics, and local execution. That payload is an RQM artifact; it is no longer the principal interoperability contract and is not represented as an openQSE standard.
