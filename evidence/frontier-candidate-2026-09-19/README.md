# Generalized transfer, frontier planning and reuse — certified candidate

**2,282 passed, 11 skipped, zero failures/errors across eight installed-wheel suites.** Compiler candidate `8050d6b8053a66019b248f63628e4d9fed60a5f6`; adapter runtime/test candidate `d32daaa9dceb097975b7562a057540764cfa6410`. Evidence-only additions after these revisions do not redefine the tested wheels. No version bump, release tag, deployment or hardware run.

## Implemented

- Fixed the arbitrary-hub star remapping defect: pair coordinates follow hub/leaf identity. Independent tests cover all three hub positions and every three-qubit Pauli product after local measurement rotations.
- Generalized star transfer from global-Z to arbitrary I/X/Y/Z products, with automatic hub discovery and final local frame rotation.
- Added a query-support causal cone and bounded chronological frontier evaluator. Default width cap is four; rejection occurs before numeric frontier allocation. Interleaved stars, limited revisits and general chain products can use this route.
- Added `evaluate_observables` with batch-local reuse of at most 16 frontier plans and their small local matrices. Circuit digest, observable support and budget determine reuse. Values are not cached; mutation invalidates reuse. Specialized star/chain/topology plans are not cached by this API.
- Results and reports distinguish frontier width, rejection, reuse, work units and intermediate units.

## Measured coverage and performance

Both boundary runs use the same 96 conditions: eight families, 4/8/12 qubits, global-Z/local-X, and Pauli budgets 64/4096. The new run also enables the distinct four-active-qubit frontier budget; this is not a claim of identical RAM budgets across representations. Five warmed timing samples per condition, single-thread settings, separate memory sampling, and an Aer native-expectation baseline are retained.

Coverage improved from **74/96 to 80/96**. Six previously unavailable conditions were recovered, none were lost, and every available answer passed the 1e-9 gate. Maximum boundary error: 2.78e-15. Sixteen conditions remain unavailable under these route budgets.

| Family | Previous available | New available | New median reference/RQM end-to-end ratio |
| --- | ---: | ---: | ---: |
| star | 12/12 | 12/12 | 2.114× |
| chain | 12/12 | 12/12 | 1.968× |
| hardware_2 | 12/12 | 12/12 | 1.192× |
| hardware_4 | 9/12 | 10/12 | 0.305× |
| hardware_5 | 4/12 | 6/12 | 0.937× |
| interleaved_star | 11/12 | 12/12 | 2.010× |
| revisited_star | 12/12 | 12/12 | 2.168× |
| random_noncommuting | 2/12 | 4/12 | 0.565× |

Ratios above one favor RQM. Ratios exclude unavailable rows and must be read with coverage. These are local measurements, not confidence intervals or a universal speed claim. Interleaved and revisited stars now select bounded transfer; global star/chain fast paths remain supported.

## Adaptive policies: real tradeoffs

All 18 policy conditions (4/8/12 qubits, disjoint/overlapping pair windows, safe/balanced/aggressive) agreed with independent statevector queries, including queries on the actual compiled output. Maximum error was 4.16e-15. Selective policies committed promotions and reduced IR size, while increasing compilation time.

Below are the 12-qubit overlapping-pair results. The source has 276 IR operations. Native CX counts come from a separate reproducible Qiskit synthesis probe in the `[rz,sx,x,cx]` basis, with seed 17.

| Policy | Compile median ms | Compiled IR operations | Committed promotions | CX after Qiskit level 0 | CX after Qiskit level 3 |
| --- | ---: | ---: | ---: | ---: | ---: |
| safe | 40.13 | 276 | 0 | 198 | 33 |
| balanced | 84.89 | 161 | 5 | 123 | 33 |
| aggressive | 125.99 | 23 | 11 | 33 | 33 |

**Aggressive promotion helped minimally optimized downstream synthesis, but did not improve final CX count over Qiskit level 3 on these fixtures.** All policies reached the same level-3 native counts. The Braket-profile lowering still contains `su4q` blocks, so counting one such descriptor as one hardware gate would be misleading. Earlier policy raw fields named `lowered_two_qubit_operations` count descriptors, not native gates or device duration.

The recorded policy batch-query timings use the public planner, which can retain the verified-equivalent input. Actual compiled-output queries were checked for correctness but not separately timed. Native synthesis counts are a separate measurement.

This supports keeping the safe default. Selective promotion is useful when a downstream consumer benefits from compact blocks or performs less synthesis; the experiment does not establish a universal downstream or total-latency advantage.

## Query reuse

Interleaved-star workloads were evaluated independently and in batches; both paths return newly computed values. No cross-call cache is retained.

| Qubits | Queries | Uncached/batched median ratio | Reused plans | Independent oracle |
| --- | ---: | ---: | ---: | --- |
| 8 | 1 | 1.057× | 0 | Qiskit Statevector |
| 8 | 10 | 1.222× | 9 | Qiskit Statevector |
| 8 | 100 | 1.250× | 99 | Qiskit Statevector |
| 12 | 1 | 0.964× | 0 | Qiskit Statevector |
| 12 | 10 | 1.274× | 9 | Qiskit Statevector |
| 12 | 100 | 1.216× | 99 | Qiskit Statevector |
| 32 | 1 | 1.074× | 0 | uncached route agreement only |
| 32 | 10 | 1.162× | 9 | uncached route agreement only |
| 32 | 100 | 1.129× | 99 | uncached route agreement only |

Batches of 10–100 queries improved measured throughput by 1.13–1.27×. Single-query ratios fluctuate around parity. Independently checked 8/12-qubit batch answers had maximum error 6.66e-15. The 32-qubit workload checks cached/uncached agreement only; it is a scalability measurement, not independent correctness evidence. Cache benefits depend on repeated query support; changing support may require a different plan.

## Resource and correctness limits

A frontier width w bounds an individual frontier tensor by 4**w complex entries. Total working storage includes circuit lists, local matrices, states and temporary arrays; this is not a whole-process cap. Preflight rejects the selected chronological schedule, not all possible contraction orders. Specialized routes have their own resource behavior, and the Pauli fallback retains its separate post-expansion term limit.

Tests cover arbitrary hubs, mixed Pauli axes, randomized gates/wires/angles, near-cancellation, disconnected query support, invalid budgets, pre-allocation rejection, cache invalidation and actual selectively compiled SU(4) output. Numerical oracle checks support these tested families, not arbitrary polynomial-time simulation.

## Original release benchmark

The original 21-condition taxonomy was rerun with five repetitions on the same compiler wheel: 21/21 valid, maximum error 2.11e-15. Its historical hardware-gate field does not govern software scientific acceptance.

## Reproduce and inspect

`candidate-artifacts.zip` contains all eight exact wheels, the manifest, revision list and dependency constraints. `manifest.json` records wheel hashes, source trees, import locations and test counts. Build with `scripts/certify_candidate.py --sources <siblings> --output <fresh-directory> --revisions candidate-revisions.json --constraints constraints.txt` after checking out the recorded commits.

Using that certification venv and `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`, run `scripts/scientific_boundary_benchmark.py` and `scripts/probe_frontier_policies.py` with `--certification <directory> --output <new-directory>`. The supplemental `scripts/probe_native_lowering.py --output <file.json>` uses the same venv and adds no runtime package changes. All scripts and raw data are published with this evidence. The prior baseline is in `../scientific-candidate-2026-09-19/`.

Compilation and query timings are separate; all measured values include floating-point error. The compiler remains backend-neutral, the API orchestrates, and Qiskit/Braket provide execution routes.
