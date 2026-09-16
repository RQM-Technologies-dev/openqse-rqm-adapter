# ORNL QSC + openQSE ecosystem context

## Source and status

This note records architectural context presented on an Oak Ridge National Laboratory slide titled **“QSC + openQSE”**, photographed during a presentation on 2026-09-16.

This is a transcription and interpretation of presentation material, not an official openQSE specification. Where this note draws an implication for `openqse-rqm-adapter`, it is explicitly an RQM Technologies interpretation.

## Architecture shown

The slide places the following organizations/projects in one ecosystem:

```text
                         QSC
                          |
        +-----------------+------------------+
        |                 |                  |
 Hybrid Algorithms  Scientific Apps      Validation
                                            |
                                      Software Thrust
                                            |
                                    QHPC Architectures
                                            |
                           +----------------+----------------+
                           |                |                |
                        Systems         Controls       Orchestration

OLCF -----------------> IQM Testbed
  |                        |
  +--------------------> openQSE Community
                           |
                    +------+------+
                    |             |
             Produces a       Produces a
              Reference       Specification
            Implementation
```

The slide also shows QSC using OLCF resources and identifies the IQM Testbed and openQSE Community as part of the surrounding QSC/OLCF activity.

## Statements captured from the slide

The presentation states that:

- hybrid algorithms and scientific applications feed requirements into both the **Software thrust** and **QHPC Architectures thrust**;
- the **Software thrust produces tools**;
- **HPC Orchestration creates the backbone by which these tools co-exist in a single ecosystem**;
- the openQSE Community produces both a **reference implementation** and a **specification**;
- under an **open-source development model**, software artifacts created as part of the Orchestration project are used for the openQSE community reference implementation; and
- the reference implementation provided by the openQSE community can in turn be used by the Orchestration project.

## Implications for this adapter

The important interoperability target is therefore larger than a compiler file format.

`openqse-rqm-adapter` should be designed as an independently implemented tool that can participate behind stable openQSE contracts while remaining compatible with a broader QHPC/orchestration ecosystem.

For RQM, the intended boundary is:

```text
openQSE / QHPC orchestration-facing contract
                  |
                  v
          OpenQASM 3 artifact
                  |
                  v
         openqse-rqm-adapter
                  |
                  v
      independent RQM ecosystem

      rqm-core
          |
      rqm-circuits
          |
      rqm-compiler <----> rqm-entanglement
          |
      rqm-qiskit / backend bridges
          |
      optional backend-adjacent rqm-optimize

                  |
                  v
          OpenQASM 3 artifact
                  |
                  v
openQSE / QHPC orchestration-facing contract
```

The adapter should therefore demonstrate four properties:

1. **Contract interoperability** — RQM can consume and return recognizable artifacts without requiring adjacent tools to understand RQM-native mathematics.
2. **Independent internal representation** — `u1q`, quaternion/SU(2) operations, `AxisHinge`, `CartanRelation`, and other RQM representations remain internal compiler choices.
3. **Composable tooling** — RQM behaves as one tool/pass implementation that could co-exist with other software-thrust tools under an orchestration layer rather than requiring RQM to own the whole software stack.
4. **Verifiable boundaries** — promotion, optimization, lowering, and export must preserve declared semantics and produce evidence suitable for a reference-implementation/conformance workflow.

## Relationship to the Compiler Working Group experiment

This context strengthens the reason for the repository's current pass/artifact-contract experiment.

The useful demonstration is not “openQSE should standardize RQM IR.” It is:

> A compiler with an independent mathematical representation can participate in a common software and orchestration ecosystem through stable artifact/pass contracts, while its internal representation remains implementation-specific.

That hypothesis should be tested with real RQM packages rather than a local toy implementation. The clean integration gate therefore remains a prerequisite before presenting this work to the openQSE Compiler Working Group.

## QSC-facing design questions to preserve

As the prototype develops, keep these questions visible:

- Which compiler/pass metadata must an orchestration layer discover before invoking an RQM transformation?
- Which artifact categories and feature profiles should be standardized by openQSE rather than by individual implementations?
- How should semantic verification/provenance travel with an artifact between independently developed tools?
- How should a tool advertise that it temporarily promotes a conventional circuit into richer internal representations such as `u1q`, `AxisHinge`, or `CartanRelation` while returning a conventional exchange artifact?
- Where should target/backend constraints enter: pass contract, QHPC orchestration, runtime adapter, or a combination?
- Can the RQM adapter serve as a concrete stress test for openQSE's reference implementation by exercising an IR family materially different from conventional gate-list IRs?

These are working questions, not claims about finalized openQSE interfaces.
