# Clean ecosystem interoperability evidence

This document records the reproducible evidence for the RQM/openQSE interoperability experiment as of 2026-09-16. It is evidence for this repository's experimental integration path, **not** an official openQSE conformance certification.

## Result

Two clean-environment executions succeeded:

- Cursor clean virtual environment: **1,874 passed, 11 skipped, 0 failed** across 1,885 collected tests.
- GitHub Actions `Clean ecosystem integration`, run `35153527075`, on merged `main`: **success**.

Merged adapter commit: `0132973d39d2785aef5eb431858090dbc480b43e`.

## Tested repository revisions

The clean local execution used current `main` revisions at the time of the run:

| Repository | Commit |
| --- | --- |
| `openqse-rqm-adapter` clean-run branch | `e9830ac66872f192f31b1614ee4c50a4238b232e` |
| `rqm-core` | `e31eeae94d4cd3f7a88eb3d0622ba6cd191e0e62` |
| `rqm-circuits` | `b681ada3c71ea8179c7cde682dc9dd469a326b5b` |
| `rqm-compiler` | `d27958b9fc9dc6b395b507d29fd1bb6bbe2e58f8` |
| `rqm-entanglement` | `401b5f44180ddb1a0232c4d247097236c7315da3` |
| `rqm-qiskit` | `70347019eb6889f0dbd07e685d3f200643a84a27` |
| `rqm-optimize` | `09a17b5c045e6a368d74a0a3af17165e48e66a0b` |

The merged `main` commit combines that clean-run implementation with the ORNL/QSC context documentation. The GitHub Actions run checked the sibling repositories out from their `main` branches and ran the same clean verification script.

## Environment

Clean local execution:

- Python 3.12.3
- GCC 13.3.0
- `rqm-core` 0.2.2
- `rqm-circuits` 0.2.1
- `rqm-compiler` 0.3.0
- `rqm-entanglement` 0.2.1
- `rqm-qiskit` 0.4.0
- `rqm-optimize` 0.1.3
- `rqm-openqse-adapter` 0.1.1

The clean script pins Qiskit 2.5.1 because the current `rqm-qiskit` test suite asserts that exact version even though its declared dependency range admits later 2.5.x releases. No tests are skipped or weakened to hide that constraint.

## Path actually executed

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
  <-> rqm-entanglement relational representations
       BellHinge
       AxisHinge
       AxisHinge -> CartanRelation promotion
       CartanRelation compose/minimize
       QuaternionCartan reconstruction
  -> compiler semantic verification
  -> conventional named-gate lowering
  -> OpenQASM 3 export/re-import verification

separate backend-adjacent check:
  -> rqm-optimize geodesic optimization after Qiskit lowering
```

A package is not counted as exercised merely because it imports. The evidence model distinguishes installed, imported, executed, and verified states and fails closed when a required capability does not reach the required state.

## Demonstrated relational behavior

The clean run exercised:

- `u1q` canonical single-qubit representation and fusion path;
- `AxisHinge`;
- `AxisHinge -> CartanRelation` promotion during the two-qubit optimization path;
- `CartanRelation` composition and minimization;
- `QuaternionCartan`, with reported reconstruction error approximately `6.66e-16`;
- `BellHinge`, with measured concurrence `1.0`.

These observations establish that the interoperability demonstration crosses real RQM representation boundaries. They do not establish general performance or complexity advantages for those representations.

## Exchange artifact

The input circuit contains `h`, `rx(0.4)`, `rxx(0.5)`, and `ryy(0.7)` on two qubits. Because `stdgates.inc` does not define `rxx` or `ryy`, the fixture carries Qiskit-compatible gate definitions. Import preserves pair-rotation operations for the relational compiler path.

The reported conventional output contains:

```text
rz(-2.741592653589793) q[0];
ry(pi/2) q[0];
rxx(0.5) q[0], q[1];
ryy(0.7) q[0], q[1];
```

Compiler equivalence status: **VERIFIED**.

Export/re-import equivalence status: **VERIFIED**.

## Test distribution

| Suite | Passed | Skipped |
| --- | ---: | ---: |
| adapter | 29 | 0 |
| rqm-core | 448 | 0 |
| rqm-circuits | 252 | 10 |
| rqm-compiler | 358 | 0 |
| rqm-entanglement | 127 | 1 |
| rqm-optimize | 101 | 0 |
| rqm-qiskit | 559 | 0 |
| **Total** | **1,874** | **11** |

## Reproduce

From the repository root:

```bash
./scripts/verify_clean_ecosystem.sh
```

A successful run must complete the clean environment setup, install the real sibling packages, execute the conformance demonstration, and complete the required adapter and sibling test suites without a failure. Required capability evidence must reach its declared executed/verified state.

GitHub CI runs the same procedure after checking out the sibling repositories, using `SKIP_CLONE=1` only to avoid fetching them twice.

## Interpretation for openQSE

The experiment tests a narrow architectural hypothesis: a compiler ecosystem may use implementation-specific mathematical representations internally while interoperating with adjacent tools through recognizable artifacts and declared pass/artifact boundaries.

It does **not** propose `u1q`, `AxisHinge`, `CartanRelation`, QuaternionCartan, or any RQM-native representation as an openQSE standard.
