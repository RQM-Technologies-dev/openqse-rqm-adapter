# Experimental Pass Contract

`openqse-rqm-adapter` implements an experimental machine-readable compiler-pass contract inspired by the openQSE Compiler Working Group discussion in `openQSE-Compiler-toolpipeline.md`.

This is an RQM Technologies experiment. It is **not** an official openQSE schema, API, standard, or reference implementation.

## Why this exists

The working-group material separates two concerns:

1. pass-management infrastructure: discovery, composition, validation, execution, and provenance; and
2. IR/artifact contracts: what a pass consumes and produces.

RQM uses a quaternionic IR internally. The interoperability experiment is therefore useful precisely because downstream components should not need to adopt that internal representation.

## Contract fields

The prototype contract declares:

- stable pass identifier and version;
- implementation identity;
- input and output artifact categories;
- encoding identity and version;
- optional IR identity and version;
- feature profiles;
- semantic guarantees;
- capabilities; and
- provenance.

The implementation lives in `src/rqm_openqse_adapter/openqse/contract.py`.

## Current baseline

The initial contract declares:

- pass: `rqm.quaternionic.compile`;
- input artifact: `LogicalCircuit`;
- input encoding: `RQMQuaternionicProgram`;
- internal IR: `RQM-Quaternionic-IR`;
- output artifact: `LogicalCircuit`;
- output encoding: `RQMPortableCircuitJSON`;
- features: unitary gates, measurement, and target metadata;
- guarantees: quaternionic semantics are encapsulated at the adapter boundary and computational semantics are preserved by supported transformations.

The RQM-specific encodings are deliberately named as RQM experimental encodings. The repository does not claim that its existing JSON payload is an openQSE standard.

## Planned exchange boundary

The next interoperability step is an OpenQASM 3 exchange path:

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

That path will allow the working group to evaluate the contract and alternative-IR experiment without adopting an RQM serialization format.
