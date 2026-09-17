# RQM Compiler Benchmark Summary

> **Status:** experimental, reproducible benchmark evidence from `rqm-compiler`. These results characterize specific circuit families and exact-observable workloads; they are not a claim that RQM efficiently simulates arbitrary quantum circuits.

## Why these benchmarks exist

The RQM compiler explores a representation strategy that differs from immediately materializing a general state vector or dense operator. Its working rule is:

> **Use the least-general exact representation available, preserve closure while possible, and promote only when a more general representation is required.**

For the OpenQSE interoperability experiment, the interesting question is not whether OpenQSE adopts RQM's mathematics. It is whether an alternative compiler can keep its own internal representation hierarchy behind conventional exchange boundaries and whether that hierarchy has measurable computational consequences.

The benchmark program therefore progressed through three questions:

1. Does the compiler-owned closed representation grow exponentially as qubit count, depth, non-Clifford density, and entanglement connectivity increase?
2. Does overlapping/global entanglement force the compact representation to blow up or lose correctness?
3. When RQM and a conventional simulator compute the **same exact quantum observable**, can the compact path produce a real end-to-end simulation speedup?

The third question is the important one. Compact IR alone is not a simulation speedup.

---

## 1. Closed-representation scaling

The primary compiler metric is

\[
C_R = \text{minimum closed RQM representation size},
\]

measured from representation-owned closure accounting rather than an external IR-size proxy.

Adversarial/random circuit families progressively increased entanglement connectivity, non-Clifford density, and circuit depth. The test set included random Clifford+T structure, SU(4)-stress circuits, all-to-all/random two-qubit interactions, and hardware-efficient/random patterns.

Through the tested range, including **32 qubits at depth 32**, structured families did not exhibit the state-vector-like exponential transition in compiler working representation. Representative hardest-point measurements included:

| Family | n=8 | n=16 | n=32 |
|---|---:|---:|---:|
| Clifford+T | 3,840 | 7,680 | 15,360 |
| SU(4)-stress | 7,168 | 14,336 | 28,672 |
| All-to-all | 5,075 | 14,742 | 47,989 |

The first two families approximately doubled when qubit count doubled. Dense connectivity grew faster, but still did not show a state-vector-like `2^n` representation curve over the tested range.

### Important instrumentation correction

Early adaptive runs reported many failed promotion attempts. A forensic classifier separated decomposition failures, numerical-tolerance failures, equivalence-proof failures, unsupported structures, and implementation defects. The reproduced failures were traced to a missing optional Qiskit/SU(4) decomposition dependency in CI—not a mathematical closure result.

After enabling the dependency, the proof-gated promotion path operated successfully. Subsequent benchmark interpretation therefore uses the corrected environment.

---

## 2. Overlapping-entanglement experiment

A second experiment held the local two-qubit interaction budget approximately constant while changing the interaction graph:

```text
disjoint -> chain -> star -> random -> dense
```

The grid covered:

```text
n       = 4, 8, 16, 32
rounds  = 1, 2, 4, 8, 16
seeds   = 3
topology families = 5
```

for **300 conditions**.

At the hardest tested point, `n=32`, `rounds=16`, every topology had the same median measured closed-representation size:

| Topology | Median C_R |
|---|---:|
| Disjoint | 4,528 |
| Chain | 4,528 |
| Star | 4,528 |
| Random | 4,528 |
| Dense | 4,528 |

Across rounds at `n=32`, the sequence was approximately:

```text
288, 568, 1,136, 2,264, 4,528
```

for `1, 2, 4, 8, 16` rounds respectively.

This is empirical evidence that, for these workloads, overlap topology did not by itself force the compiler working representation toward a dense global-state representation.

The adaptive machinery was active: **8 successful promotions** occurred, with no decomposition/tolerance/implementation failures in this corrected run.

For tractable small systems, exact dense-reference checks of global parity and the `|0...0>` probability matched the optimized result within the benchmark's numerical tolerance.

### What this does not prove

`C_R` is not the dimension of the quantum state. A compact circuit/relational representation can remain small while extraction of arbitrary global state information is still exponentially difficult. This experiment therefore establishes compact representation behavior, not universal efficient simulation.

---

## 3. Global-information extraction frontier

The next experiment explicitly attacked the point where conventional exact simulation normally pays the exponential bill. It considered:

- selected amplitudes;
- small marginals;
- distant two-point correlations;
- global Pauli parity;
- full measurement distributions.

Three globally entangling circuit families were compiled through **64 qubits**. At `n=64`, `rounds=16`, representative median closed-representation sizes were:

| Family | Median C_R | Median compile time | Peak memory |
|---|---:|---:|---:|
| GHZ/chain | 12,524 | ~1.73 s | ~8.0 MB |
| Star | 12,524 | ~1.71 s | ~8.0 MB |
| Random overlap | 9,052 | ~1.34 s | ~4.8 MB |

For comparison only, an explicitly materialized 64-qubit complex128 state vector would contain `2^64` amplitudes and require roughly **256 EiB**. These are different computational objects, so this comparison illustrates why extraction must be tested separately; it is not itself a speedup claim.

The experiment showed that compact compilation continued to 64 qubits, while the then-current implementation did **not** yet provide a direct compact extractor for arbitrary requested global state information. That result identified the next engineering target rather than treating compact compilation as simulation.

---

## 4. End-to-end exact-observable simulation benchmark

RQM then added an exact observable evaluator that propagates Pauli observables through the compiled representation without allocating a `2^n` state vector. The benchmark compared that path against an ordinary exact state-vector evolution on the **same GitHub Actions CPU**, using the same circuit and the same requested observable.

The tested exact observables were:

\[
\langle Z^{\otimes n}\rangle
\qquad\text{and}\qquad
\langle Z_0 Z_{n-1}\rangle.
\]

Circuit families were chain, star, and scrambled entangling circuits over:

```text
n     = 4, 6, 8, 10, 12, 14, 16
depth = 1, 4, 8
queries per circuit = 2
```

The speedup metric included RQM compilation and query execution:

\[
S(n,Q)=\frac{T_{\mathrm{statevector}}(n,Q)}
{T_{\mathrm{RQM\ compile}}(n)+T_{\mathrm{RQM\ query}}(n,Q)}.
\]

A speedup was considered valid only when the RQM observable matched the state-vector result to **absolute error <= 1e-9**. If RQM's exact Pauli expansion exceeded its configured **250,000-term cap**, the condition was marked unavailable rather than approximated or silently redirected to a state vector.

### Results

The workflow completed successfully with:

| Metric | Result |
|---|---:|
| Total benchmark conditions | 126 |
| Valid equal-output conditions | 79 |
| RQM-unavailable conditions | 47 |
| Valid conditions with speedup > 1x | 22 |
| Largest n with a valid comparison | 16 |
| Maximum measured speedup | **293.12x** |
| Median speedup over all valid conditions | 0.158x |

The qubit-count slices reported by the benchmark were:

| Qubits | Median speedup among valid conditions | Maximum speedup |
|---:|---:|---:|
| 4 | 0.010x | 0.724x |
| 8 | 0.007x | 0.943x |
| 12 | **9.67x** | **16.27x** |
| 16 | **174.25x** | **293.12x** |

The analysis gate found **no available RQM query with error greater than `1e-9`**.

This is the strongest result in the current benchmark set: for a subset of exact-observable workloads that remain within the RQM evaluator's closure/resource budget, the benchmark observed a substantial end-to-end classical simulation advantage over the reference state-vector implementation.

It also exposes the boundary clearly: **47 of 126 conditions were unavailable** because the exact compact observable representation exceeded its configured term budget. The current evidence therefore supports a tractable workload region, not an arbitrary-circuit or universal-simulation claim.

---

## Interpretation

The combined experiments currently support the following narrower picture:

```text
compact compiler representation
        |
        +-- remains compact across tested structured/adversarial families
        |   through 64-qubit compilation experiments
        |
        +-- overlapping entanglement does not automatically force
        |   dense state materialization in the tested representation
        |
        +-- exact observable propagation sometimes remains compact
        |       |
        |       +-- when it does: large measured statevector-vs-RQM wins
        |       |
        |       +-- when it does not: Pauli-term expansion reaches the cap
        |
        +-- arbitrary amplitudes/full distributions are not yet covered
            by an equivalent compact native extraction result
```

One useful research hypothesis is that some quantum computations admit a compact intrinsic relational/transformation description even when their conventional ambient state-vector representation is exponentially large. The benchmark evidence is consistent with that hypothesis for specific circuit/query families, but does not establish it universally.

In particular, these results **do not demonstrate** that RQM can efficiently recover an arbitrary amplitude, arbitrary marginal, or full output distribution for an arbitrary universal quantum circuit.

---

## Why this matters for the OpenQSE adapter

The OpenQSE-facing lesson is architectural as much as numerical.

The exchange boundary does not need to standardize RQM's internal quaternionic representations for an independently developed compiler to experiment with them. OpenQASM 3 and recognizable compiler/pass artifacts can remain the interoperability boundary while RQM internally uses `u1q`, `AxisHinge`, `CartanRelation`, QuaternionCartan/SU(4), adaptive closure accounting, and representation promotion.

That makes `openqse-rqm-adapter` a concrete experiment in **alternative mathematical IR interoperability**: conventional artifacts at the boundary, independently owned mathematics inside, and measurable behavior that can be benchmarked without requiring the surrounding ecosystem to adopt the internal representation.

---

## Reproducibility and claims discipline

The source benchmark harnesses live in the sibling [`rqm-compiler`](https://github.com/RQM-Technologies-dev/rqm-compiler) repository. Relevant benchmark programs include:

```text
benchmarks/adaptive_representation.py
benchmarks/adaptive_failure_diagnostic.py
benchmarks/overlap_closure.py
benchmarks/global_extraction.py
benchmarks/simulation_speedup_gate.py
```

The end-to-end speedup result above was produced by GitHub Actions run `35266495072` from `rqm-compiler` commit `7d1feefc942470f6a92a42f7d56650b6087a7d63`. Its artifact is named `simulation-speedup-35266495072`.

Before using these results as a broader performance claim, the next validation stage should include multiple timing repeats, warm/cold-run separation, larger feasible qubit counts, per-family/per-query characterization of successful and unavailable cases, and comparison with optimized production simulators such as Qiskit Aer rather than only the current reference state-vector implementation.

Accordingly, the appropriate current claim is:

> **RQM's experiments show compact compiler-representation scaling across the tested circuit families and substantial exact end-to-end observable-simulation speedups for a bounded subset of workloads, with an explicit resource boundary where the compact observable representation becomes too large.**

That is intentionally narrower than claiming a general classical replacement for quantum computation.
