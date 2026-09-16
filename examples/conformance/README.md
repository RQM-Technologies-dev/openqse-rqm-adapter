# openQSE/RQM interoperability experiment

This directory contains a small, reproducible experiment for the pass/artifact-contract concepts being discussed by the openQSE Compiler Working Group.

It is **not an official openQSE conformance suite**. It is an RQM Technologies implementation experiment intended to provide concrete input to the working-group discussion.

## Demonstrated seam

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
validate -> canonicalize -> lower
          |
          v
LogicalCircuit / OpenQASM3
```

The experiment demonstrates that the RQM implementation can use a distinct internal mathematical representation without requiring the adjacent tool-pipeline component to consume that representation.

## Run

From the repository root:

```bash
python3 -m pip install -e ".[dev]"
python3 examples/conformance/run.py
```

The harness writes four reviewable artifacts under `examples/conformance/artifacts/`:

- `input.qasm` — neutral input exchange artifact;
- `output.qasm` — neutral output exchange artifact;
- `contract.json` — machine-readable declaration of the experimental pass contract;
- `report.json` — checks and provenance for the run.

The output OpenQASM is reparsed by the adapter. The run fails if the emitted artifact cannot be consumed or if basic structural invariants are lost.

## What this proves — and what it does not

The demo checks a narrow interoperability property: a supported OpenQASM 3 logical circuit can cross into the RQM implementation, be represented and processed internally, and cross back out through the same recognizable exchange representation.

It does not establish full OpenQASM 3 compliance, equivalence for arbitrary quantum programs, production readiness, hardware compatibility, or official openQSE conformance.
