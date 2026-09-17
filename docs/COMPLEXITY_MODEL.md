# Computational Complexity Model

## Purpose

The RQM/OpenQSE adapter is designed around a simple computational principle:

> **Use the least-general exact representation that is closed for the quantum operation being processed.**

The adapter therefore treats representation choice as part of compilation rather than assuming that every operation must immediately be expanded into a general dense matrix, fully materialized circuit object, or other maximally general form.

This document defines the complexity questions the project intends to measure. It does **not** claim that RQM provides a universal asymptotic speedup for arbitrary quantum computation.

## Representation hierarchy

The current RQM ecosystem contains increasingly general structured representations, including the conceptual hierarchy:

```text
Bell
  ⊂ AxisHinge
  ⊂ CartanRelation
  ⊂ QuaternionCartanBlock
  ⊂ U(4)
```

Not every implementation type is literally a set-theoretic subtype of the next. The hierarchy expresses increasing representational generality: a more specialized exact representation should be retained while the relevant operations remain closed within it.

The intended compilation pattern is:

```text
conventional artifact
  -> recognize structured case
  -> select least-general exact representation
  -> propagate/compose in that representation
  -> test closure
  -> promote only when closure requires it
  -> minimize/demote when an exact simpler form is recovered
  -> materialize conventional output only when required
```

## Complexity objective

The research hypothesis is that closure-driven representation selection can reduce computational work for circuit families whose operations remain within structured representations for meaningful portions of compilation.

The adapter and sibling RQM packages should therefore measure at least five distinct costs rather than collapsing them into a single performance number:

1. **Representation size** — parameters/bytes required to encode an operation or block.
2. **Arithmetic work** — scalar, complex, quaternionic, matrix, and decomposition operations required for composition and transformation.
3. **Promotion/demotion cost** — work required to move between specialized and more general exact representations.
4. **Decomposition/optimization cost** — work avoided or incurred when conventional decompositions, canonicalizations, cancellations, or synthesis procedures are needed.
5. **Materialization/backend cost** — work required to construct conventional matrices, gates, OpenQASM artifacts, or backend-facing objects when those forms are actually needed.

Wall-clock time and memory consumption should be recorded as empirical consequences of these mechanisms, not substituted for the mechanism-level measurements above.

## Per-operation accounting

For an operation `g`, let `R(g)` denote the least-general exact representation recognized by the compiler. A useful implementation-level accounting model is:

```text
C_RQM(g) = C_recognize(g)
           + C_operate(R(g))
           + C_closure(g)
           + C_transition(g)
           + C_materialize(g)
```

where transition and materialization costs are zero when they are unnecessary.

A conventional baseline should be measured independently for the same semantic operation and output requirements. The relevant question is then not whether one primitive is intrinsically cheaper in isolation, but whether the full compilation path performs less representational and arithmetic work while preserving exact semantics.

## Circuit-level accounting

For a circuit or compilation region `G = {g_1, ..., g_n}`, benchmarks should report:

- how many operations enter each representation;
- how long they remain closed there;
- the number and direction of representation transitions;
- the amount of general representation materialization avoided;
- intermediate representation size;
- arithmetic/decomposition counts where measurable;
- peak memory;
- wall-clock compilation time;
- semantic equivalence against the conventional path.

This makes it possible to distinguish a genuine representation-driven reduction from ordinary implementation effects.

## Claims discipline

The current defensible claim is architectural:

**RQM is designed to reduce representational and computational work by retaining operations in the least-general exact representation available and promoting them only when exact closure requires it.**

Stronger statements require evidence. In particular, this repository should not claim without corresponding proof or benchmark evidence that:

- every quantum operation is cheaper under RQM;
- every circuit receives an asymptotic improvement;
- universal quantum computation can be classically simulated in polynomial time;
- an observed constant-factor benchmark improvement establishes a different complexity class.

Those are separate theoretical or empirical questions.

## Benchmark program

The next useful benchmark suite should compare RQM and conventional paths over representative circuit families and record both semantic equivalence and mechanism-level cost. At minimum it should include:

- single-qubit sequences that remain in compact quaternionic form;
- Bell/AxisHinge cases that remain closed;
- cases requiring AxisHinge -> CartanRelation promotion;
- general two-qubit cases approaching the QuaternionCartan/U(4) boundary;
- mixed circuits with repeated promotion and simplification opportunities;
- adversarial cases where structured representations provide little or no advantage.

The benchmark should report where the approach wins, ties, or loses in raw measured quantities without extrapolating beyond the tested circuit family.

## Relationship to OpenQSE interoperability

This complexity strategy is internal to RQM. OpenQSE-facing artifacts do not need to understand the RQM representation hierarchy. The interoperability objective is precisely to preserve conventional exchange boundaries while allowing an independently developed compiler to perform internal work using materially different mathematical representations.

That separation lets the adapter test two questions at once:

1. Can RQM's alternative representations interoperate through stable compiler/artifact boundaries?
2. When they can, how much representational and computational work can be avoided before conventional materialization becomes necessary?
