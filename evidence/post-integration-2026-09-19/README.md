# Post-integration investigation

The compiler, entanglement and adapter candidates were squash-merged into main.
`integration.json` records each merge commit and proves its tree matches the
previously reviewed candidate exactly. The compiler and entanglement runtime
wheels used below are the already certified artifacts: 2,330 passing tests,
11 skips, zero failures/errors. No runtime code changed in this investigation.
The expanded adapter suite separately passes 64 tests, including three new
checks of the application Hamiltonians against known initial-state energies.

## Noncanonical Cartan: the 6% regression did not reproduce

The original benchmark ran baseline and candidate in separate environments in
sequence. The follow-up binds the exact historical promotion expression and
the current method in the same process, sharing dependencies. Each fresh process
warms both paths, randomly alternates their order for 41 paired blocks of 20
calls per path, and retains every timing. Three fresh processes use seeds
1701, 1702 and 1703. Bootstrap intervals describe within-process block variation,
not uncertainty across machines.

| Case | Old/new median ratio, run 1 | Run 2 | Run 3 |
| --- | ---: | ---: | ---: |
| positive_noncanonical | 1.0110× | 0.9929× | 1.0248× |
| permuted_noncanonical | 0.9934× | 1.0011× | 1.0125× |
| outside_chamber | 1.0143× | 0.9833× | 1.0135× |
| canonical | 2.9312× | 2.8517× | 2.8824× |

The original positive-noncanonical case ranges from 0.7% slower to 2.5% faster;
a repeatable 6% regression is not supported. Its only added runtime operation
is the chamber-side scalar guard before the same materialization/KAK expression.
The other noncanonical controls are also near parity. Repeated post-GC memory
samples do not reproduce the previous retained-allocation jump. Timing/order
and allocator variation are plausible explanations, not a proven root cause.
No speculative runtime patch was applied. Canonical promotion retains a roughly
2.85–2.93× gain in this paired experiment. Raw intervals and memory samples remain
in `cartan-paired-*.json`.

## Application workloads

These are application-oriented, fixed-parameter workloads, not full optimizer
runs or claims of converged solutions. All use 6/10/14 qubits and depths 1/3:

- Weighted ring MaxCut QAOA: evaluate the full weighted cut objective.
- Heisenberg-chain quench: first-order product-formula evolution of a Neel
  state under XX + YY + 0.7 ZZ interactions and a 0.23 Z field; evaluate energy.
- Variational transverse-field Ising: a local Ry/CX ansatz evaluated against
  -sum ZZ - 0.7 sum X.

Every workload checks compiled-output state fidelity and each available query
against Qiskit Statevector. If any Hamiltonian term is unavailable, aggregate
energy is unavailable; missing terms are never silently replaced by zero.
The query uses the verified-equivalent input retained by the public planner;
it does not claim compiled-output query timing. Pauli fallback cap: 128 terms.

| Family | Frontier cap | Complete workloads / 6 | Available terms / requested |
| --- | ---: | ---: | ---: |
| qaoa_maxcut | 4 | 6/6 | 60/60 |
| qaoa_maxcut | 8 | 6/6 | 60/60 |
| heisenberg_quench | 4 | 3/6 | 114/222 |
| heisenberg_quench | 8 | 4/6 | 166/222 |
| vqe_ising | 4 | 3/6 | 66/114 |
| vqe_ising | 8 | 4/6 | 86/114 |

Across 36 budget/workload conditions, maximum available-term error is 3.56e-15;
maximum complete-energy error is 1.07e-14. Maximum compiled-output fidelity
deviation from one is 6.22e-15. Raising the frontier cap recovers some deeper
energy workloads but does not recover them all. Complete QAOA coverage uses the
planner's combined routes; it is not evidence that every QAOA frontier fits width
four. Full per-term routes, rejected widths, reuse, promotion counts, numerical
answers, batch runtime, compile runtime and traced allocations are archived.

## Wider frontier probes

Complete-pair, noncommuting interaction schedules force chronological width to
match the number of qubits. Planning and numeric caches are fresh for each timed
call. Five warmed samples are recorded; memory tracing is a separate run.

| Width | Representation | Median milliseconds | Coefficient payload bytes | Traced peak bytes |
| --- | --- | ---: | ---: | ---: |
| 4 | real | 0.435 | 2,048 | 25,240 |
| 4 | complex | 0.587 | 4,096 | 36,200 |
| 6 | real | 0.992 | 32,768 | 188,656 |
| 6 | complex | 1.643 | 65,536 | 271,048 |
| 8 | real | 3.776 | 524,288 | 2,461,040 |
| 8 | complex | 7.821 | 1,048,576 | 3,214,544 |
| 10 | real | 37.570 | 8,388,608 | 37,797,608 |

All evaluated widths agree with independent statevector expectations within
1e-15. The real path is approximately 1.35×, 1.66× and 2.07× faster than the forced
complex route at widths four, six and eight. Width ten has a real-only numeric
probe; no complex timing is inferred. Its 8 MiB coefficient tensor causes about
36 MiB traced peak allocation, confirming that tensor payload is not a process
memory budget. Tracemalloc counts are retained positive blocks, not cumulative
allocation traffic or full process RSS.

Width 12/16/24 schedules were rejected at caps 4/8/10 before numerical evaluation.
Planning took approximately 0.23/0.42/0.94 milliseconds. Those schedules would
require individual real tensors of 128 MiB, 32 GiB, and 2 PiB respectively; they
were not allocated. These widths describe this chronological schedule, not an
optimal contraction proof. Keep the public default cap at four: the results
support workload-aware opt-in, not a blanket increase.

## Reproduce

Use the previously certified wheel archive and constraints linked by
`integration.json`. With that environment's Python and
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`, run:

```
python scripts/probe_application_frontiers.py --certification PATH --mode cartan --seed 1701 --output cartan-paired-1.json
python scripts/probe_application_frontiers.py --certification PATH --mode cartan --seed 1702 --output cartan-paired-2.json
python scripts/probe_application_frontiers.py --certification PATH --mode cartan --seed 1703 --output cartan-paired-3.json
python scripts/probe_application_frontiers.py --certification PATH --mode applications --output application-workloads.json
python scripts/probe_application_frontiers.py --certification PATH --mode frontiers --output wide-frontiers.json
```

`PATH` identifies a passed certification directory containing its manifest and
installed-wheel venv. Driver SHA-256 is recorded in `integration.json`. New
application-definition tests are in `tests/test_application_workloads.py`.
The earlier 0.94× noncanonical measurement remains archived as historical data;
it has not been overwritten by these follow-up results.
