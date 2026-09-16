from __future__ import annotations

from rqm_openqse_adapter.ecosystem.bridge import circuits_to_compiler, compiler_to_circuits
from rqm_openqse_adapter.ecosystem.pipeline import REQUIRED_CORE, run_clean_demonstration


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
