# RQM Compiler 0.4 in the OpenQSE Adapter

The adapter consumes `rqm-compiler 0.4` as a **representation-aware,
query-aware optimization component** behind conventional interoperability
artifacts.

The public compiler path is:

```text
OpenQASM / rqm-circuits
        |
        v
compile_representation_aware
        |
        +-- quaternion/local representation
        +-- relational AxisHinge / Cartan structure
        +-- strict topology recognition
        +-- representation closure accounting (C_R)
        +-- conservative promotion/fallback
        |
        v
plan_and_evaluate(query) when an exact observable is requested
        |
        +-- direct star relational readout
        +-- chain boundary transfer
        +-- validated fixed-depth 1D topology contraction
        +-- general exact fallback
        |
        v
standard-compatible materialization / backend lowering
```

## Interoperability principle

OpenQSE-facing artifacts do not need to encode RQM's internal quaternion,
AxisHinge, Cartan, boundary-transfer, or contraction objects. The adapter
exchanges conventional circuit artifacts while `CompilerReport` can expose
why RQM selected a particular internal route.

Relevant report fields include:

- `representation_complexity` (C_R);
- `query_complexity` (C_Q/work units);
- maximum representation level and representation histogram;
- recognized topology;
- selected query route;
- contraction width and largest intermediate;
- promotion count;
- fallback status and reason.

This makes the alternative internal representation observable to tooling
without making it an OpenQSE wire-format requirement.

## Scope

The specialized readout routes are exact only inside their strict recognizer
envelopes and are guarded by a 1e-9 reference gate in the compiler's release
benchmarks. Unsupported structures fall back rather than being relabeled as a
validated compact representation.

The current 0.4 frozen taxonomy contains 21/21 exact-valid conditions across
seven tested workload families. Timing results are workload- and
environment-specific and do not establish efficient arbitrary-circuit
simulation.
