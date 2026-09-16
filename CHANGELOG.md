# Changelog

## 0.1.1 — 2026-09-16

- Add a fail-closed OpenQASM 3 ↔ RQM ecosystem interoperability layer that
  converts through the real sibling packages instead of reimplementing them.
- Record each capability as installed, imported, executed, and verified.
- Add `examples/conformance/run.py`, `scripts/verify_clean_ecosystem.sh`, and
  a matching GitHub Actions workflow.

## 0.1.0 — 2026-09-16

- Convert this repository from OpenQSE working-group notes into the
  **RQM OpenQSE Adapter** implementation prototype.
- Add a quaternionic frontend, IR, validation/canonicalization/lowering
  pipeline, OpenQSE-compatible payload emitter, target metadata, and a local
  statevector backend.
- Preserve the former compiler working-group charter under
  `legacy/openqse-working-group/` as historical material.
- This release is experimental. It is not production-ready and is not an
  official OpenQSE implementation.
