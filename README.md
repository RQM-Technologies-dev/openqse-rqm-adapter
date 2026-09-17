# RQM OpenQSE Adapter

**Experimental alternative-IR interoperability test for the openQSE compiler/tool-pipeline architecture.**

```text
OpenQASM 3
    -> openQSE-facing pass/artifact boundary
    -> openqse-rqm-adapter
    -> real RQM compiler ecosystem
       rqm-circuits -> rqm-compiler <-> rqm-entanglement
              |             |               |
           rqm-core        u1q       AxisHinge / CartanRelation
              |                             |
              +---- verified lowering ------+
    -> OpenQASM 3
```

The question this repository tests is deliberately narrow: **can an independently developed compiler use materially different internal mathematical representations while interoperating through recognizable exchange artifacts and stable compiler boundaries?**

RQM owns this implementation. OpenQSE is the architectural/interoperability context. This repository does **not** propose RQM's quaternionic IR, `u1q`, `AxisHinge`, `CartanRelation`, or QuaternionCartan as openQSE standards, and it is not an official OpenQSE compiler or endorsed reference implementation.

## Computational complexity objective

The computational motivation for RQM's representation hierarchy is straightforward:

> **Use the least-general exact representation for every quantum operation, and promote to a more general representation only when exact closure requires it.**

Instead of immediately expanding every operation into a general dense matrix or fully materialized circuit representation, the RQM path attempts to recognize structured cases, preserve and compose them in compact exact representations, test closure, and materialize a more general form only when necessary.

Conceptually, the increasingly general representation path includes:

```text
Bell
  ⊂ AxisHinge
  ⊂ CartanRelation
  ⊂ QuaternionCartanBlock
  ⊂ U(4)
```

and the intended compilation strategy is:

```text
conventional artifact
  -> recognize structured case
  -> least-general exact RQM representation
  -> operate / propagate there
  -> closure test
  -> promote only when required
  -> minimize / demote when possible
  -> conventional materialization only when required
```

For circuit families that remain closed within structured representations, this approach is intended to reduce intermediate representation size, arithmetic work, decomposition work, and backend-materialization cost. The magnitude and asymptotic character of any reduction must be established by proof and/or benchmark evidence; this repository does **not** assume universal computational-complexity superiority.

See [`docs/COMPLEXITY_MODEL.md`](docs/COMPLEXITY_MODEL.md) for the measurement model, claims discipline, and proposed benchmark program.

## Reproduce the clean ecosystem demonstration

```bash
./scripts/verify_clean_ecosystem.sh
```

The gate creates a fresh virtual environment, installs the real sibling RQM packages from source, executes the OpenQASM 3 round trip, records installed/imported/executed/verified capability evidence, and runs the required adapter and sibling test suites. It fails closed when a required capability is not actually exercised or verified.

**Recorded clean result:** 1,874 passed, 11 skipped, 0 failed across 1,885 collected tests. GitHub Actions independently reproduced the merged integration successfully on `main` (`Clean ecosystem integration`, run `35153527075`). See [`docs/CONFORMANCE_EVIDENCE.md`](docs/CONFORMANCE_EVIDENCE.md).

## Real ecosystem path

The fail-closed demonstration executes:

```text
OpenQASM 3
  -> rqm-qiskit import
  -> rqm-circuits
  -> rqm-compiler
       normalize
       canonicalize
       flatten
       to_u1q
       merge_u1q
       sign_canon
       cancel_2q
  -> rqm-core quaternion mathematics
  <-> rqm-entanglement
       BellHinge
       AxisHinge
       AxisHinge -> CartanRelation promotion
       CartanRelation compose/minimize
       QuaternionCartan reconstruction
  -> semantic verification
  -> conventional named-gate lowering
  -> OpenQASM 3 export/re-import verification
```

`rqm-optimize` is exercised separately after Qiskit lowering, in its intended backend-adjacent role rather than being injected into the backend-neutral compiler path.

The clean demonstration records compiler equivalence as **VERIFIED** and export/re-import equivalence as **VERIFIED**. It demonstrates real representation promotion/lowering without requiring the external exchange boundary to understand those internal representations.

## Experimental pass/artifact contract

The repository also implements a machine-readable experimental pass contract inspired by the openQSE Compiler Working Group's pass/artifact-contract discussion. The principal exchange encoding is OpenQASM 3; RQM-native representations remain implementation details.

See:

- [`docs/pass-contract.md`](docs/pass-contract.md)
- [`docs/CONFORMANCE_EVIDENCE.md`](docs/CONFORMANCE_EVIDENCE.md)
- [`docs/ORNL_QSC_OPENQSE_CONTEXT.md`](docs/ORNL_QSC_OPENQSE_CONTEXT.md)
- [`docs/openqse-integration.md`](docs/openqse-integration.md)
- [`docs/COMPLEXITY_MODEL.md`](docs/COMPLEXITY_MODEL.md)
- [`examples/conformance/`](examples/conformance/)

## Standalone prototype

The repository retains a small standalone adapter prototype for inspection and development. It contains a local quaternionic frontend/IR, validation/canonicalization/lowering passes, target model, JSON payload, and ideal local simulator. That standalone path is **not** the evidence used for the cross-repository interoperability claim; the clean ecosystem demonstration above uses the real sibling RQM packages.

The standalone prototype does not implement the OpenQSE runtime, resource scheduling, hardware control, QEC/FTQC compilation, or a complete quaternionic programming language.

## Quick start for standalone development

Python 3.10+ is required for the standalone adapter. The clean ecosystem demonstration requires Python 3.11+ because the sibling RQM packages do.

```bash
git clone https://github.com/RQM-Technologies-dev/openqse-rqm-adapter.git
cd openqse-rqm-adapter
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

Bundled standalone examples:

```bash
python3 examples/basic_quaternionic/run.py
python3 examples/bell/run.py
python3 examples/openqse/run.py
```

## Current status

This is an **experimental prototype intended for interoperability discussion and reproducible testing**, not production hardware submission.

The previous OpenQSE Compiler Working Group notes are preserved under [`legacy/openqse-working-group/`](legacy/openqse-working-group/).

## Roadmap

- benchmark representation size and per-operation computational work against conventional paths;
- measure closure duration, promotion/demotion frequency, and avoided materialization across representative circuit families;
- continue aligning the experimental pass/artifact contract with Compiler Working Group decisions;
- broaden OpenQASM 3 coverage without weakening fail-closed semantics;
- test richer target/backend capability contracts;
- evaluate QIR/MLIR boundaries where they answer a working-group interoperability question;
- extend hybrid, QEC, and FTQC experiments when corresponding contracts are defined;
- test compatibility with QHPC/orchestration and reference-implementation interfaces as those interfaces become concrete.

Production mathematics and backend bridges belong to the sibling packages: `rqm-core`, `rqm-circuits`, `rqm-compiler`, `rqm-entanglement`, `rqm-qiskit`, and `rqm-optimize`.

## License

Apache License 2.0. See [LICENSE](LICENSE).
