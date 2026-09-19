# Scientific candidate certification

The compiler computes; the API connects. `rqm-compiler` owns backend-neutral
compilation, query planning, correctness guards, regional verification, and
representation/query telemetry. `rqm-api` orchestrates execution and jobs.
`rqm-qiskit` and `rqm-braket` translate compiler output and provide simulator and
hardware routes through their SDKs. The OpenQSE adapter certifies scientific
interoperability across these boundaries.

The 0.4.0 scientific gate is software-only. Two real hardware demonstrations
remain API/bridge integration deliverables, not prerequisites for publishing
compiler conformance and bounded research results. Billing, public admission,
and commercial deployment are separate concerns. Passing this gate does not
establish hardware performance or official OpenQSE endorsement.

## Candidate gate

1. Commit all sources and record their exact revisions. Use the candidate
   compiler branch, not an assumed package version: its current package metadata
   remains 0.3.0. Release numbering is a separate deliberate step.
2. Run `scripts/certify_candidate.py --sources /path/to/sibling-repositories
   --output /new/output --revisions candidate-revisions.json`. The sources folder
   contains all seven RQM repositories and `openqse-rqm-adapter`.
3. The script rejects tracked modifications and revision mismatches, archives
   committed sources, builds wheels, installs them into a fresh environment,
   confirms installed module locations, runs dependency checks and eight suites,
   and checks the full QASM round trip. No editable installations are permitted.
4. Reproduction uses the recorded revisions and `--constraints` pointing at the
   first run's `constraints.txt`. Retain the exact wheels and their SHA-256 hashes
   when reproducing artifact execution; rebuilding can change ZIP timestamps.
5. Run the benchmark with that output's `venv/bin/python`, with
   `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`, passing `--certification /output`
   and `--output /new/benchmark-output`. Keep raw timing samples, all failures,
   query budgets, errors, units, and the benchmark source hash.

The mandatory query fixture compares every two-qubit Pauli observable with
Qiskit's statevector built from independently parsed original OpenQASM. Missing,
non-exact, non-finite, or numerically incorrect answers fail. Complete operators
verify original-input to lowering/export and optional optimizer output, up to
one global phase. Tests deliberately inject corruption to check these guards.

## Measurement interpretation

`C_R` is the existing closed-representation size metric, not measured bytes.
Compiler promotion counts refer to committed compiler transformations; query
promotion counts refer to delegation from structured Pauli propagation to the
general evaluator. They are different events.

Star/chain intermediate bounds count the largest individual complex array (16
entries), not total storage. Circuit/block lists grow with circuit size. Tensor
routes report contraction-plan intermediate entries. Pauli routes report peak
retained terms, including expansion overshoot when the cap is exceeded. Separate
tracemalloc samples measure traced query allocations, not whole-process RSS.

A route's `exact` flag describes its algebraic method. Floating-point arithmetic
and a 1e-13 coefficient cutoff still require independent numerical verification;
reported benchmark acceptance is absolute complex error at most 1e-9.

A rejected specialized recognizer is not proof that no efficient representation
exists. Report its rejection time separately from fallback evaluation time.
Unavailable results are retained in coverage denominators and have no speedup.
The benchmark compares against Aer native expectation evaluation without full
statevector export, and reports compilation and query timing separately.
