from __future__ import annotations

from pathlib import Path

from rqm_openqse_adapter.ecosystem.bridge import circuits_to_compiler, compiler_to_circuits
from rqm_openqse_adapter.ecosystem.pipeline import CONFORMANCE_OPENQASM, REQUIRED_CORE, run_clean_demonstration


def test_ecosystem_packages_import() -> None:
    import rqm_circuits
    import rqm_compiler
    import rqm_core
    import rqm_entanglement
    import rqm_qiskit

    assert rqm_core.Quaternion is not None
    assert rqm_circuits.Circuit is not None
    assert rqm_compiler.optimize_circuit is not None
    assert rqm_entanglement.AxisHinge is not None
    assert rqm_qiskit.import_openqasm3 is not None


def test_circuits_compiler_roundtrip_is_verified() -> None:
    from rqm_compiler import Circuit, verify_equivalence

    source = Circuit(2)
    source.h(0)
    source.cx(0, 1)
    restored = circuits_to_compiler(compiler_to_circuits(source))
    report = verify_equivalence(source, restored)
    assert report.verified is True


def test_conformance_openqasm_matches_checked_in_source() -> None:
    source = Path(__file__).resolve().parents[1] / "examples/conformance/input.qasm"
    assert source.read_text(encoding="utf-8") == CONFORMANCE_OPENQASM


def test_clean_demonstration_executes_required_capabilities() -> None:
    report = run_clean_demonstration()
    for name in REQUIRED_CORE:
        capability = report.capabilities[name]
        assert capability["installed"] is True, name
        assert capability["imported"] is True, name
        assert capability["executed"] is True, name
        assert capability["verified"] is True, name
    assert "to_u1q" in report.compiler_passes_executed
    assert "merge_u1q" in report.compiler_passes_executed
    assert "sign_canon" in report.compiler_passes_executed
    assert "cancel_2q" in report.compiler_passes_executed
    assert "AxisHinge" in report.relational_representations
    assert "CartanRelation" in report.relational_representations
    assert report.openqasm_output
    assert "OPENQASM 3" in report.openqasm_output
    assert report.semantic_verification["compiler_verified"] is True
    assert report.semantic_verification["export_reimport_verified"] is True
    assert report.capabilities["rqm-optimize"]["executed"] is True
    assert report.capabilities["rqm-optimize"]["details"]["role"] == "backend-adjacent-qiskit-compression"


import pytest
from types import SimpleNamespace
from rqm_openqse_adapter.diagnostics import AdapterError
from rqm_openqse_adapter.ecosystem.pipeline import _verify_query, _verify_qiskit_operators


@pytest.mark.parametrize("value,available,exact", [
    (0.0, False, True), (0.0, True, False), (float("nan"), True, True),
    (float("inf"), True, True), (0.5, True, True), (0.1j, True, True),
])
def test_query_verification_rejects_invalid_evidence(value, available, exact):
    with pytest.raises(AdapterError):
        _verify_query(SimpleNamespace(value=value, available=available, exact=exact), 0.0)


def test_query_verification_uses_complex_error():
    assert _verify_query(SimpleNamespace(value=0.2+1e-12j, available=True, exact=True), 0.2) < 1e-9


def test_operator_oracle_detects_changed_semantics():
    from qiskit import QuantumCircuit
    a = QuantumCircuit(2)
    b = a.copy()
    b.x(1)
    with pytest.raises(AdapterError, match="operator mismatch"):
        _verify_qiskit_operators(a, b, boundary="injected corruption")


def test_demo_rejects_corrupt_public_query(monkeypatch):
    import rqm_compiler
    monkeypatch.setattr(rqm_compiler, "plan_and_evaluate", lambda *a, **k:
                        SimpleNamespace(value=float("nan"), available=True, exact=True,
                                        method="injected", work_units=0))
    with pytest.raises(AdapterError, match="non-finite"):
        run_clean_demonstration()
