# OpenQSE Adapter Ecosystem Recertification — 2026-09-18

Purpose: recertify the OpenQSE/RQM interoperability path against the current
`main` branches of the RQM sibling repositories after the RQM Compiler 0.4
and RQM Studio architecture changes.

This recertification is intentionally software-only. The mandatory conformance
gate MUST NOT require provider credentials, paid execution, remote simulators,
or QPU access.

The required path remains:

```text
OpenQASM 3
 -> rqm-qiskit import
 -> rqm-circuits
 -> rqm-compiler <-> rqm-entanglement
 -> rqm-core mathematics
 -> semantic verification
 -> conventional lowering
 -> OpenQASM 3 export/re-import verification
```

The new RQM Studio hardware path is downstream and optional:

```text
OpenQSE artifact
 -> openQSE-rqm-adapter
 -> RQM compiler pipeline
 -> conventional target artifact
 ---------------- optional execution boundary ----------------
 -> RQM Studio / rqm-api
 -> provider adapter
 -> simulator or QPU
```

A successful recertification should update `docs/CONFORMANCE_EVIDENCE.md`
and the README with the observed sibling SHAs, test totals, workflow/run
identity, and conformance result. A failure should preserve the failing
evidence and identify the first interoperability boundary that no longer
conforms.
