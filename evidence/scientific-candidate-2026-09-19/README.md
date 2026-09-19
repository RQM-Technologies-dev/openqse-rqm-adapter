# Scientific candidate evidence — 2026-09-19

**Software certification passed: 2,255 passed, 11 skipped, zero failures/errors across eight suites.** This certifies the recorded candidate artifacts, not a published 0.4.0 package release or hardware performance. Package metadata remains compiler 0.3.0 and adapter 0.1.1; identify these candidates by commit and wheel hash.

The compiler computes; the API orchestrates; Qiskit and Braket bridges supply simulator and hardware routes. These results require neither provider credentials nor paid execution.

## Fixed candidates

| Repository | Commit |
| --- | --- |
| rqm-core | `4c89792a5f44339f6b0c68871f991d726328491c` |
| rqm-circuits | `c8f970f222a10cc95a044947c522ec574bae9dab` |
| rqm-entanglement | `34cb69e37eac021bef68a488a89a2cbe7f5f95c8` |
| rqm-compiler | `a018f673a8ce2edca44da5c9b4c8a2cc4b6b9b26` |
| rqm-qiskit | `bfd53bec96ea04e8e9d84158014f6ce7217a6099` |
| rqm-optimize | `be12b2c9e16477a81f9af0a549189aa61299e7d3` |
| rqm-braket | `c9fc7eef0eee7ba4f49e9105d304e37a7c32bf2f` |
| openqse-rqm-adapter | `fabb0fa3716e6dd73c90552dd89a8fd0e85f4649` |

The exact eight tested wheels are preserved in `candidate-artifacts.zip`. `manifest.json` contains their SHA-256 hashes, source trees, installed module locations, and test counts. Evidence-only commits after these revisions do not redefine the tested candidate.

## Correctness guards and integration

- Queries must be available, algebraically exact, finite, and within absolute complex error 1e-9 of an independent oracle. All 16 two-qubit Pauli observables are compared against Qiskit Statevector built by independently parsing the original QASM; maximum error 9.99e-16.
- Full operators independently check original QASM to lowering/export and the optional optimizer, up to one global phase. Tests inject wrong, unavailable, non-exact and non-finite answers to verify rejection.
- An asymmetric three-qubit fixture checks both Qiskit and Braket operator conventions and Braket local-simulator probabilities. No cloud jobs were submitted.
- Suites run against installed wheels in a fresh venv, with source-path injection disabled. Dependency checks and import-location assertions passed.

| Suite | Passed | Skipped |
| --- | ---: | ---: |
| rqm-core | 451 | 0 |
| rqm-circuits | 252 | 10 |
| rqm-entanglement | 131 | 1 |
| rqm-compiler | 410 | 0 |
| rqm-qiskit | 560 | 0 |
| rqm-optimize | 101 | 0 |
| rqm-braket | 310 | 0 |
| openqse-rqm-adapter | 40 | 0 |

## Boundary experiment

96 conditions: eight families × 4/8/12 qubits × global-Z/local-X queries × 64/4096 Pauli-term budgets. Each timing has five recorded repetitions after warmup; memory is sampled separately. Circuit seed is 7300+n. Aer evaluates the observable directly without exporting a full statevector.

**74/96 available, all numerically valid; 22/96 unavailable under the selected budgets. Maximum available-answer error: 2.78e-15.** Unavailable results remain in coverage and carry no speedup.

| Family | Available / conditions | Median reference/RQM end-to-end ratio, available only |
| --- | ---: | ---: |
| star | 12/12 | 1.701× |
| chain | 12/12 | 1.329× |
| hardware_2 | 12/12 | 0.636× |
| hardware_4 | 9/12 | 0.310× |
| hardware_5 | 4/12 | 0.160× |
| interleaved_star | 11/12 | 0.695× |
| revisited_star | 12/12 | 0.809× |
| random_noncommuting | 2/12 | 0.107× |

Ratios above 1 favor RQM. These are local five-repeat measurements, not population estimates or a universal speed claim. The denominators include compilation plus query; component samples are preserved. Available-only speed ratios must be read alongside coverage.

### What remains small

Validated one-pass star/global-Z and strict chain/global-Z routes use at most 16 entries in an individual complex array (256 payload bytes). At 4→8→12 qubits that bound stayed fixed. Traced total query allocation peaks still grew: star 10,408→14,368→18,472 bytes, chain 10,661→12,662→17,320 bytes. Circuit descriptions and block lists are not constant-space.

For global-Z at budget 4096, measured end-to-end ratios were 2.17–2.55× for stars and 1.51–1.76× for chains. A local-X request uses another route; a compact circuit alone does not certify compact evaluation of every query.

The validated two-layer 1D global-Z route used at most 32 tensor entries here. Four-layer instances reached 1,024 entries at 12 qubits and were slower than the Aer baseline. Small intermediate objects do not guarantee a runtime advantage.

### Where the current approach stops helping

Revisiting a star leaf or interleaving a noncommuting local rotation correctly rejects the specialized envelope. At 12 qubits and budget 4096 their global-Z fallbacks retained 64 and 80 Pauli terms and achieved only 0.392× and 0.376× reference/RQM ratios.

Five-layer circuits are outside the current 2–4-layer recognizer. Their 8- and 12-qubit global-Z queries exhausted the 4096-term budget. Random noncommuting 8- and 12-qubit queries also exhausted it. The measured maximum overshoot was 6,144 terms: the current cap is checked after a gate expansion, not a hard allocation ceiling.

### How efficiently RQM detects the boundary

The strict star/chain/hardware recognizers reject structural mismatches before falling back. On 12-qubit global-Z cases, the sum of separately measured rejected-recognizer medians was about 14 µs for an interleaved star, 26 µs for a revisited star, 39 µs for a five-layer circuit, and 17 µs for the random family. These are isolated rejection timings, not whole-planner latencies.

Actual global-Z query/failure latencies on those same cases were approximately 19.5, 19.6, 30.1 and 14.5 ms respectively. RQM identifies the unsupported specialized envelope cheaply; it discovers Pauli-budget failure during expansion. It does not yet predict that failure without doing expansion, nor certify a global complexity boundary for arbitrary circuits.

### Promotions and units

Raw rows distinguish compiler `promotion_count` from query promotion. The current compiler counter counts committed adaptive SU(4) replacement events; it was zero for these benchmark inputs and is not a count of all AxisHinge-to-Cartan calls. The independent conformance probes observed five AxisHinge.promote calls and one CartanRelation.promote call across the complete demonstration, including its direct checks. Query promotion was zero for specialized routes or one for delegation to the general Pauli evaluator, including failed queries.

Intermediate units are complex array entries, tensor entries, or retained Pauli terms. C_R is a representation-size metric, not bytes. Tracemalloc captures traced query allocations, not process RSS. Recognizer rejection does not prove that no better exact method exists.

## Original release benchmark rerun

The unchanged 21-condition taxonomy ran with five repetitions against the same installed compiler wheel: 21/21 available and valid, maximum error 2.11e-15; all 21 committed verified regional optimizations. Its historical `hardware_gate` field records pending provider execution and is not the scientific release gate.

| Family | Valid | Median reference/RQM ratio |
| --- | ---: | ---: |
| local | 3/3 | 1.915× |
| clifford | 3/3 | 1.250× |
| star | 3/3 | 1.591× |
| chain | 3/3 | 1.657× |
| clifford_t | 3/3 | 1.275× |
| hardware_efficient | 3/3 | 0.550× |
| random_sparse | 3/3 | 0.366× |

This legacy taxonomy exports a statevector to compute parity; its ratios are not directly comparable to the new native-expectation benchmark. Both baselines and versions are recorded.

## Reproduce

Check out `candidate-revisions.json`, run `scripts/certify_candidate.py` with `--revisions` and `--constraints constraints.txt`, then invoke `scripts/scientific_boundary_benchmark.py` with the new certification venv. Set `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`. For the old taxonomy set `RQM_CANDIDATE_WHEEL` and `RQM_CANDIDATE_COMMIT`, load `benchmarks/job_taxonomy.py`, set `REPEATS=5`, and call `main()` from an empty output directory.

To rerun the exact binaries, install the archived wheels with the recorded dependency constraints into a fresh venv. Wheel SHA-256 checks identify the tested artifacts; newly built wheel ZIP timestamps may differ. Raw timing arrays, query errors, budgets, failure reasons, representation metrics, test XML and conformance evidence are included.

## Limits and earlier failed attempts

The guards and numerical checks support these fixtures, not arbitrary-circuit exact simulation or universal polynomial complexity. Algebraic exact routes still use floating-point arithmetic and prune coefficients below 1e-13. The measured acceptance threshold is 1e-9.

Preliminary attempts encountered missing build backends, a native llvmlite 0.49.0 import crash in this environment, and five core tests requiring Git-history fixtures. The final runner uses declared isolated build backends, preserves exact checkout history, and pins numba 0.63.1 / llvmlite 0.46.0 / numpy 2.3.5. The final fresh run passed all mandatory checks. No hardware, commercial deployment, package-version bump, or release tag was performed.
