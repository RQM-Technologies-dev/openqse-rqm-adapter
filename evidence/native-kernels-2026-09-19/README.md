# Native observable kernels — certified measurements

Compiler `280519b136afe17227204e23bbfeee2246e63277`, entanglement
`7c57d0672ef5caa7236d9703e2fd3096fb346ab2`, adapter driver/test candidate
`4f20c3a72e17c7a645a29ef91b1c5ddb429b0247`.

**2,330 passed, 11 skipped, zero failures/errors across eight installed-wheel suites.**
All measurements below use those installed wheels, not editable sources.
Evidence-only commits after these revisions do not redefine the tested candidate.
No release tag or merge is implied. Exact commit and wheel hashes are authoritative;
existing package version labels are unchanged and are not sufficient identifiers.

## Changes and staged measurements

- Local U†PU updates use rqm-core quaternion rotations rather than gate matrices.
- Fresh-leaf star and validated chain queries use analytic real Pauli transfers
  for rxx/ryy/rzz and CX, including reversed control direction.
- Cartan promotion bypasses reconstruction and KAK only for coordinates already
  exactly in the canonical Weyl chamber. Local quaternion frames and global
  phase are preserved. Noncanonical coordinates retain decomposition.
- Local/hinge/CX frontier plans use real coefficient tensors. Other pair gates
  retain the complex density route. Query-support pruning and admission limits
  are unchanged.

The frozen baseline is compiler `8050d6b8053a66019b248f63628e4d9fed60a5f6`
and entanglement `34cb69e37eac021bef68a488a89a2cbe7f5f95c8` from
[the preceding candidate](../frontier-candidate-2026-09-19/README.md).
The identical driver ran in both installed-wheel environments. Each condition
uses one warmup and 21 timing samples, with OPENBLAS_NUM_THREADS=1 and
OMP_NUM_THREADS=1. Instrumentation and memory sampling are separate runs.
These are local median ratios, not confidence intervals or universal speedups.

| Probe | Tested sizes | Baseline/candidate runtime ratio |
| --- | --- | ---: |
| local_observable | 4, 12, 32 qubits | 1.73–1.82× |
| hinge_star | 4, 12, 32 qubits | 1.34–1.52× |
| hinge_chain | 4, 12, 32 qubits | 6.26–6.68× |
| frontier | 4, 12, 32 qubits | 1.76–1.96× |
| wide_frontier | 3, 4, 6 qubits | 1.54–1.61× |
| generic_frontier | 3, 4, 6 qubits | 0.98–1.00× |
| canonical_cartan | 2 qubits | 3.14× |
| noncanonical_cartan | 2 qubits | 0.94× |

The noncanonical Cartan control measured about 6.7% slower; generic frontiers
measured within about 2% of baseline. These results are retained, not omitted.
The canonical Cartan result is a promotion microbenchmark, not a claim that
whole-circuit compilation is 3.14× faster.

## Materializations and allocations

For the 12-qubit probes, named gate-matrix helper calls fell from 36 (local),
45 (star), 34 (chain), and 34 (frontier) to zero. The canonical Cartan probe
fell from one relation materialization plus one KAK call to zero of each;
noncanonical Cartan retained both. Raw counters are in both kernel JSON files.
These count calls to named helpers, not every internal NumPy allocation.

| Probe (12 qubits unless Cartan) | Traced peak bytes, baseline → candidate | Retained positive blocks, baseline → candidate |
| --- | ---: | ---: |
| local_observable | 3,535 → 3,280 | 10 → 11 |
| hinge_star | 26,072 → 22,632 | 75 → 60 |
| hinge_chain | 10,416 → 10,632 | 39 → 28 |
| frontier | 29,254 → 17,600 | 54 → 46 |
| canonical_cartan | 9,461 → 4,835 | 77 → 52 |
| noncanonical_cartan | 8,086 → 9,097 | 29 → 57 |

Tracemalloc snapshot counts are **retained positive allocation differences**,
not cumulative allocation traffic. They include Python bookkeeping and may
vary with allocator reuse. Named NumPy constructor calls are also retained in
the raw evidence; nested calls can overlap. Neither is presented as a complete
allocator event count. Chain peak memory is essentially flat at 12/32 qubits;
the largest gain here is runtime, not a claim that every memory metric improves.

## Frontier closure and its boundary

The real tensor has 4**width entries, each 8 bytes instead of 16. At width six,
its coefficient payload falls from 65,536 to 32,768 bytes; measured traced peak
falls from 248,488 to 175,288 bytes. Plan caches and temporary arrays explain
why total memory does not simply halve.

This is exact coefficient closure, not a new low-rank factorization: exponential
width remains. Chronological complete-pair schedules at 4/8/12 qubits require
widths 4/8/12. Caps 2/4/8 reject every schedule wider than the cap before numeric
frontier evaluation. Planning took about 15–16, 63–66, and 147–150 microseconds
respectively on this run. Rejected plans called no instrumented numeric matrix
or allocation helpers. This is a bound for this schedule, not a proof that no
better contraction ordering exists.

## Accuracy and release regression checks

- Staged probes: 20 conditions, maximum independent-oracle error 8.33e-15.
  Query oracles use Qiskit Statevector through 12 qubits; Cartan probes compare
  reconstructed operators. The 32-qubit rows are timing/allocation probes with
  baseline agreement only, not independent full-state certification.
- Boundary benchmark: 80/96 available and within tolerance, unchanged coverage,
  no lost cases, maximum error 2.66e-15. Sixteen conditions remain unavailable
  under the configured budgets. All 96 report zero query promotions; compiler
  promotions, route choices, fallback and rejection details are recorded per row.
- Original release taxonomy: 21/21 valid, maximum error 2.11e-15, five repetitions.
- Adaptive policies: all 18 conditions valid, maximum error 3.03e-15, including
  queries of actual compiled output. Nine reuse probes reran; the 8/12-qubit
  independent-oracle maximum error is 8.22e-15. Reuse is not uniformly faster
  (the 12-qubit, ten-query row measured 0.81×); raw timing samples are preserved.
- Native synthesis counts reran on these same wheels. This is downstream
  basis synthesis, not a hardware execution measurement.

The 48 new tests cover signed Pauli basis actions, non-adjacent/reversed axes,
zero/tiny/negative/π angles, canonical chamber boundaries, local frame signs,
global phase, fallback, random revisited frontiers versus the dense evaluator,
and guards against gate-matrix materialization.

## Reproduce

Use `candidate-revisions.json` with `scripts/certify_candidate.py`, supplying
`--sources`, a fresh `--output`, `--revisions`, and `--constraints constraints.txt`.
Use the resulting environment's Python for every benchmark. Run the identical
`scripts/probe_native_kernels.py --label candidate --output candidate-kernels.json`
in both the previous and new certified wheel environments; set
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` for each command.

Run `scripts/scientific_boundary_benchmark.py` and
`scripts/probe_frontier_policies.py` with `--certification` and a fresh `--output`.
Run `scripts/probe_native_lowering.py --output native-lowering.json` in that
same environment. For the original taxonomy, load `benchmarks/job_taxonomy.py`,
set `REPEATS=5`, set `RQM_CANDIDATE_WHEEL` and `RQM_CANDIDATE_COMMIT`, and call
`main()` from an empty output directory.

`candidate-artifacts.zip` contains all eight exact tested wheels plus the manifest
and dependency constraints. SHA-256:
`0403b123da661199aba1e7f28b80e64860535e1f9e446a4b15fcf20eebb2c067`.
Individual wheel hashes, all suite XML, conformance output, full certification
log, raw timing samples, call counters, and memory readings are included here.
