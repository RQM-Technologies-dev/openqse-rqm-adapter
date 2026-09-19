# Linear Algebra ↔ Quaternionic Geometry Correspondence Guide

## Purpose

This document is a translation layer between conventional quantum-mechanics / quantum-information language and the geometric representations being explored by the RQM compiler and the OpenQSE–RQM adapter.

It is intended to make the work inspectable by researchers who naturally reason in state vectors, matrices, tensor products, density operators, and circuit simulation. The goal is not to replace linear algebra by terminology. For every proposed geometric representation, the standard quantum calculation remains the reference against which exactness must be demonstrated.

A correspondence in this document can have one of three statuses:

- **Established mathematics** — a standard mathematical equivalence, such as unit quaternions and SU(2).
- **RQM representation** — an implementation-level representation intended to encode a conventional quantum object exactly over a stated domain.
- **Research target** — a proposed correspondence whose domain, proof, reconstruction map, closure properties, or computational advantage still requires characterization.

The long-term acceptance criterion is:

```
conventional object
        ↕
geometric object
        ↕
proof / reconstruction map
        ↕
numerical conformance test
```

## Correspondence map

| Conventional quantum mechanics / linear algebra | RQM / geometric representation | Meaning and validation target |
|---|---|---|
| Complex qubit vector (α, β)ᵀ | Quaternion / spinor orientation | Represent a single-qubit pure state geometrically while preserving all observable predictions. Specify the forward and inverse maps and their gauge convention. |
| Normalization |α|² + |β|² = 1 | Unit quaternion q ∈ S³ | The normalized single-qubit object is associated with a unit element of the quaternionic/spinorial geometry. **Established mathematical structure**, subject to the precise RQM state convention. |
| Global phase equivalence | Geometric / gauge equivalence | States differing only by physically irrelevant global phase must map to the same physical state, or to geometric representatives explicitly identified as gauge-equivalent. |
| SU(2) matrix | Unit-quaternion action | Single-qubit special-unitary evolution can be expressed through the standard SU(2)–unit-quaternion correspondence. **Established mathematics.** |
| Pauli X, Y, Z | Quaternionic axis rotations | Express Pauli actions as rotations/actions associated with the corresponding geometric axes and verify equality with matrix evolution under the chosen convention. |
| Bloch sphere | Projected S³/S¹ geometry | Relate the full normalized spinor/unit-quaternion description to the physical pure-state Bloch sphere after quotienting the appropriate phase freedom. |
| Single-qubit unitary | Quaternion multiplication / frame transformation | Replace repeated 2×2 complex matrix action, where applicable, with composition in the geometric representation. Composition must reconstruct the same conventional state. |
| Tensor product | Composite relational representation | RQM seeks to represent composite systems through local objects plus explicit relations where this is exact. This is **not** a claim that arbitrary tensor products disappear; the exact representable domain and reconstruction rule must be stated. |
| Bell state | Special structured relation | Bell states provide a compact, highly structured test case for relational representations. Reconstruction must recover the conventional Bell amplitudes and correlations. |
| Two-qubit entanglement | AxisHinge / richer relational object where applicable | **RQM research representation.** AxisHinge is intended to encode a structured domain of exact two-qubit relationships geometrically. Its exact closure domain must be measured rather than assumed. |
| General two-qubit unitary | Cartan-style relational representation where applicable | Use Cartan/canonical two-qubit structure to carry relationships that exceed simpler AxisHinge closure. Exact scope, parameterization, and reconstruction are conformance requirements. |
| State-vector expansion | General exact fallback representation | When a compact representation is not closed under an operation, correctness takes priority: promote to a representation capable of exact evaluation, including conventional expansion where necessary. |
| Matrix multiplication | Geometric composition | Where an exact geometric representation exists, compose the corresponding transformations directly and verify against the conventional matrix product. |
| Operator closure | Representation closure | Ask whether applying the next operation leaves the result exactly expressible in the current representation class. If yes, remain compact; if not, promote. |
| Basis change | Frame / coordinate transformation | Re-express a quantum state or operation in another basis as a corresponding change of geometric frame/coordinates, preserving physical predictions. |
| Measurement probability | Conventional Born probabilities reproduced from geometry | A geometric representation is acceptable only if measurement probabilities agree with the conventional calculation for the supported domain. |
| Partial trace / reduced state | Marginal / reduced relational construction | **Research target.** Define how local observable state is recovered from a composite geometric representation and demonstrate equality with the conventional reduced density operator. |
| Fidelity | Equivalent geometric invariant / distance calculation | Where a direct geometric expression is used, demonstrate that it returns the same fidelity as the conventional definition over its stated domain. |
| Circuit simulation | Evolution of geometric / relational objects | Instead of committing globally to one representation, evolve the cheapest exact representation available, promoting or demoting as closure changes. |

## The central compiler idea: representation closure

For a representation class R and operation G, the key question is whether

```
G(R) ∈ R.
```

If the answer is yes, the representation is closed under that operation and the compiler can update the geometric object without expanding into a more general representation.

If the answer is no, exactness requires promotion:

```
compact representation
        ↓
operation
        ↓
closure failure
        ↓
richer exact representation
```

If later structure permits an exact return to a simpler representation, the compiler may demote again.

This makes representation choice part of computation rather than a one-time front-end decision.

## AxisHinge as an OpenQSE-facing example

AxisHinge should be understood as a proposed exact relational representation over a defined subset of two-qubit states and transformations—not as a synonym for all entanglement.

The conformance path should be explicit:

```
conventional |ψ_AB⟩
      ↓ encode
AxisHinge H_AB
      ↓ apply supported operation G
AxisHinge H'_AB
      ↓ reconstruct
conventional |ψ'_AB⟩
```

The reconstructed result must agree with

```
|ψ'_AB⟩ = G |ψ_AB⟩
```

to the specified numerical tolerance.

A second test must deliberately cross the AxisHinge boundary:

```
H_AB → operation outside AxisHinge closure
     → detected closure failure
     → promotion to CartanRelation or another exact route
     → reconstruction
     → conventional-reference comparison
```

The interesting scientific measurement is therefore not merely whether AxisHinge can encode a Bell state. It is the size and structure of its **exact closure domain**.

## What OpenQSE should be able to test

For each RQM representation exposed through the adapter, an external test should ultimately be able to ask:

1. **Encode:** Can a conventional state/operator be mapped into the representation?
2. **Reconstruct:** Can the conventional object be recovered without loss over the stated domain?
3. **Evolve:** Does RQM evolution match conventional reference evolution?
4. **Measure:** Do observable probabilities agree?
5. **Detect closure:** Does the implementation correctly identify when the current representation is insufficient?
6. **Promote:** Does it move to a richer exact route before information is lost?
7. **Demote:** Can it recognize when a simpler exact representation becomes available again?
8. **Account:** What resources were actually consumed by the representation and its closure maintenance?

That final item matters because compact notation by itself is not computational compression. Any claimed efficiency must include the resources required to maintain, transform, promote, reconstruct, and measure the representation.

## Suggested conformance pattern

Every correspondence above should mature toward a common test record:

```
CONVENTIONAL INPUT
    ↓
RQM ENCODE
    ↓
RQM OPERATION(S)
    ↓
RQM RECONSTRUCTION
    ↓
REFERENCE LINEAR-ALGEBRA CALCULATION
    ↓
COMPARE
    ├── state / density operator
    ├── measurement probabilities
    ├── invariants
    ├── numerical error
    ├── representation transitions
    └── resource accounting
```

This creates a shared language between conventional quantum-software researchers and the RQM implementation.

## Scientific posture

The adapter should make a strong distinction between three questions:

**Equivalence:** Does the RQM representation reproduce conventional quantum mechanics exactly over its declared domain?

**Closure:** How long and under which operations can that exact representation be maintained without promotion?

**Complexity:** Does maintaining that representation actually require fewer computational resources than the conventional exact route?

Those are separate claims and should be tested separately.

The purpose of this guide is therefore not to ask OpenQSE users to accept a different mathematical language. It is to make the translation sufficiently explicit that they can independently test whether the geometric language carries the same quantum information—and then measure whether it provides a useful computational representation.

---

### Working principle

> **No geometric shortcut earns computational significance merely because it is compact to write. It earns significance when it is exact, remains closed across useful computations, and its total measured resource cost is lower than the corresponding general exact route.**

This document is expected to evolve alongside the RQM compiler, its representation hierarchy, and OpenQSE conformance experiments.
