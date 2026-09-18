"""Fail-closed OpenQASM 3 ↔ RQM ecosystem demonstration."""

from __future__ import annotations

import json
import math
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..diagnostics import AdapterError
from .bridge import circuits_to_compiler, compiler_to_circuits
from .evidence import EvidenceLedger
from .probe import installed_probes

REQUIRED_CORE = [
    "rqm-circuits",
    "rqm-core",
    "rqm-compiler",
    "compile_representation_aware",
    "plan_and_evaluate",
    "rqm-entanglement",
    "rqm-qiskit",
    "to_u1q",
    "merge_u1q",
    "sign_canon",
    "cancel_2q",
    "AxisHinge",
    "AxisHinge.promote",
    "verify_equivalence",
    "openqasm3_import",
    "openqasm3_export",
]

CONFORMANCE_OPENQASM = """OPENQASM 3.0;
include "stdgates.inc";
gate rxx(p0) _gate_q_0, _gate_q_1 {
  h _gate_q_0;
  h _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  h _gate_q_1;
  h _gate_q_0;
}
gate sxdg _gate_q_0 {
  s _gate_q_0;
  h _gate_q_0;
  s _gate_q_0;
}
gate ryy(p0) _gate_q_0, _gate_q_1 {
  sxdg _gate_q_0;
  sxdg _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  sx _gate_q_0;
  sx _gate_q_1;
}
qubit[2] q;
h q[0];
rx(0.4) q[0];
rxx(0.5) q[0], q[1];
ryy(0.7) q[0], q[1];
"""

BELL_OPENQASM = """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
h q[0];
cx q[0], q[1];
"""

_PACKAGE_SURFACES = {
    "to_u1q": ("rqm-compiler", "rqm_compiler.passes.to_u1q"),
    "merge_u1q": ("rqm-compiler", "rqm_compiler.passes.merge_u1q"),
    "sign_canon": ("rqm-compiler", "rqm_compiler.passes.sign_canon"),
    "cancel_2q": ("rqm-compiler", "rqm_compiler.passes.cancel_2q"),
    "verify_equivalence": ("rqm-compiler", "rqm_compiler.verification"),
    "compile_representation_aware": ("rqm-compiler", "rqm_compiler.planner"),
    "plan_and_evaluate": ("rqm-compiler", "rqm_compiler.planner"),
    "AxisHinge": ("rqm-entanglement", "rqm_entanglement.relational"),
    "AxisHinge.promote": ("rqm-entanglement", "rqm_entanglement.relational"),
    "openqasm3_import": ("rqm-qiskit", "rqm_qiskit.assurance"),
    "openqasm3_export": ("rqm-qiskit", "rqm_qiskit.assurance"),
}


@dataclass
class CleanDemonstrationReport:
    python_version: str
    repository_shas: dict[str, str]
    installed_versions: dict[str, str | None]
    capabilities: dict[str, Any]
    compiler_passes_executed: list[str]
    relational_representations: list[str]
    openqasm_input: str
    openqasm_output: str | None
    semantic_verification: dict[str, Any]
    test_counts: dict[str, Any] = field(default_factory=dict)
    optional_not_exercised: list[dict[str, str]] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "python_version": self.python_version,
            "repository_shas": dict(self.repository_shas),
            "installed_versions": dict(self.installed_versions),
            "capabilities": self.capabilities,
            "compiler_passes_executed": list(self.compiler_passes_executed),
            "relational_representations": list(self.relational_representations),
            "openqasm_input": self.openqasm_input,
            "openqasm_output": self.openqasm_output,
            "semantic_verification": dict(self.semantic_verification),
            "test_counts": dict(self.test_counts),
            "optional_not_exercised": list(self.optional_not_exercised),
            "details": dict(self.details),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, default=str)


def _git_sha(path: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _discover_shas(ecosystem_root: Path | None) -> dict[str, str]:
    shas = {"openqse-rqm-adapter": _git_sha(Path(__file__).resolve().parents[3])}
    names = {
        "rqm-core": "rqm-core",
        "rqm-circuits": "rqm-circuits",
        "rqm-compiler": "rqm-compiler",
        "rqm-entanglement": "rqm-entanglement",
        "rqm-qiskit": "rqm-qiskit",
        "rqm-optimize": "rqm-optimize",
    }
    root = ecosystem_root
    if root is None:
        env = Path(__file__).resolve().parents[3] / ".ecosystem"
        tmp = Path("/tmp/rqm-ecosystem")
        root = env if env.exists() else tmp
    for name, dirname in names.items():
        repo = root / dirname
        if repo.exists():
            shas[name] = _git_sha(repo)
    return shas


def _mark_package(ledger: EvidenceLedger, dist: str, module_name: str) -> Any:
    ledger.mark_installed(dist, distribution=dist)
    module = __import__(module_name)
    ledger.mark_imported(dist, module=module_name, file=getattr(module, "__file__", None))
    return module


def _bind_surfaces(ledger: EvidenceLedger) -> None:
    for name, (package, module) in _PACKAGE_SURFACES.items():
        ledger.inherit_from_package(name, package, module=module)


def run_clean_demonstration(
    *,
    ecosystem_root: Path | None = None,
    include_optimize: bool = True,
) -> CleanDemonstrationReport:
    ledger = EvidenceLedger()
    relational: list[str] = []

    rqm_core = _mark_package(ledger, "rqm-core", "rqm_core")
    rqm_circuits = _mark_package(ledger, "rqm-circuits", "rqm_circuits")
    rqm_entanglement = _mark_package(ledger, "rqm-entanglement", "rqm_entanglement")
    rqm_compiler = _mark_package(ledger, "rqm-compiler", "rqm_compiler")
    rqm_qiskit = _mark_package(ledger, "rqm-qiskit", "rqm_qiskit")
    try:
        rqm_optimize = _mark_package(ledger, "rqm-optimize", "rqm_optimize")
    except Exception as exc:  # pragma: no cover - optional sibling
        rqm_optimize = None
        ledger.ensure("rqm-optimize").details["import_error"] = str(exc)

    _bind_surfaces(ledger)

    from rqm_compiler import compile_representation_aware, plan_and_evaluate, verify_equivalence
    from rqm_compiler.compile import lower_circuit_for_backend
    from rqm_core import Quaternion
    from rqm_entanglement import (
        AxisHinge,
        BellHinge,
        CartanRelation,
        analyze_circuit_coupling,
        compose_relations,
    )
    import rqm_compiler.passes.lower_u1q_named_1q as lower_u1q_module
    import rqm_entanglement.relational as relational_module
    from rqm_qiskit import export_openqasm3, import_openqasm3
    from rqm_qiskit.convert import compiled_circuit_to_qiskit

    del rqm_core, rqm_circuits, rqm_compiler, rqm_qiskit

    with installed_probes() as probe:
        probe.wrap_function(rqm_entanglement, "compose_relations", "compose_relations")
        probe.wrap_function(relational_module, "compose_relations", "compose_relations.module")
        probe.wrap_method(AxisHinge, "promote", "AxisHinge.promote")
        probe.wrap_method(CartanRelation, "promote", "CartanRelation.promote")
        probe.wrap_method(CartanRelation, "compose", "CartanRelation.compose")
        probe.wrap_method(CartanRelation, "minimize", "CartanRelation.minimize")
        probe.wrap_function(lower_u1q_module, "quaternion_to_zyz", "rqm_core.quaternion_to_zyz")
        probe.wrap_method(Quaternion, "to_su2_matrix", "Quaternion.to_su2_matrix")

        imported = import_openqasm3(CONFORMANCE_OPENQASM)
        if imported.circuit is None or getattr(imported.report, "status", None) != "SUPPORTED":
            raise AdapterError(
                "OpenQASM 3 import failed closed: "
                f"{getattr(imported.report, 'status', None)} "
                f"{getattr(imported.report, 'error', None)} "
                f"{getattr(imported.report, 'unsupported_reasons', None)}"
            )
        ledger.mark_executed("openqasm3_import", status=imported.report.status)
        ledger.mark_executed("rqm-qiskit", path="import_openqasm3")

        compiler_in = imported.circuit
        circuits_ir = compiler_to_circuits(compiler_in)
        ledger.mark_executed("rqm-circuits", instructions=len(circuits_ir.instructions))
        compiler_roundtrip = circuits_to_compiler(circuits_ir)
        roundtrip_report = verify_equivalence(compiler_in, compiler_roundtrip)
        if not roundtrip_report.verified:
            raise AdapterError(
                "rqm-circuits ↔ rqm-compiler roundtrip failed semantic verification: "
                f"{roundtrip_report.to_dict() if hasattr(roundtrip_report, 'to_dict') else roundtrip_report}"
            )
        ledger.mark_verified("rqm-circuits", roundtrip_verified=True)

        planned = compile_representation_aware(compiler_roundtrip)
        optimized, compiler_report = planned.circuit, planned.report
        ledger.mark_executed("compile_representation_aware", representation_complexity=compiler_report.representation_complexity)
        ledger.mark_verified("compile_representation_aware", public_api=True)
        passes = list(compiler_report.passes_applied)
        if not compiler_report.optimization_applied:
            raise AdapterError(
                "rqm-compiler withheld optimization; demonstration fails closed. "
                f"fallback={compiler_report.fallback_reason} passes={passes}"
            )
        for required_pass in ("to_u1q", "merge_u1q", "sign_canon", "cancel_2q"):
            if required_pass not in passes:
                raise AdapterError(f"Required compiler pass {required_pass!r} was not applied.")
            ledger.mark_executed(required_pass, source="compile_representation_aware.report.passes_applied")
            ledger.mark_verified(required_pass, recorded_by_compiler=True)

        ledger.mark_executed("rqm-compiler", passes=passes, optimization_applied=True)
        ledger.mark_executed("verify_equivalence", status=compiler_report.equivalence_status)
        if compiler_report.equivalence_status != "VERIFIED" or not compiler_report.equivalence_verified:
            raise AdapterError("Compiler semantic verification did not return VERIFIED.")
        ledger.mark_verified("verify_equivalence", status=compiler_report.equivalence_status)
        ledger.mark_verified("rqm-compiler", equivalence_status=compiler_report.equivalence_status)

        u1q_ops = [op for op in optimized.operations if op.gate == "u1q"]
        if not u1q_ops:
            raise AdapterError("Optimized circuit contains no u1q operations.")
        for op in u1q_ops:
            quat = Quaternion(op.params["w"], op.params["x"], op.params["y"], op.params["z"])
            matrix = quat.to_su2_matrix()
            if op.params["w"] < -1e-12:
                raise AdapterError("sign_canon failed: u1q scalar component is negative.")
            if abs(sum(v * v for v in (op.params["w"], op.params["x"], op.params["y"], op.params["z"])) - 1.0) > 1e-8:
                raise AdapterError("u1q quaternion is not unit.")
            if matrix.shape != (2, 2):
                raise AdapterError("rqm-core SU(2) matrix has unexpected shape.")
        ledger.mark_executed("rqm-core", u1q_count=len(u1q_ops))

        if probe.count("compose_relations") < 1 and probe.count("compose_relations.module") < 1:
            raise AdapterError("rqm-entanglement.compose_relations was never called during compilation.")
        if probe.count("AxisHinge.promote") < 1:
            raise AdapterError("AxisHinge → CartanRelation promotion was never executed.")
        ledger.mark_executed(
            "rqm-entanglement",
            compose_relations=probe.count("compose_relations") + probe.count("compose_relations.module"),
        )
        ledger.mark_executed("AxisHinge", promotions=probe.count("AxisHinge.promote"))
        ledger.mark_executed("AxisHinge.promote", calls=probe.count("AxisHinge.promote"))
        relational.extend(["AxisHinge", "CartanRelation"])

        expected = compose_relations(AxisHinge("xx", 0.5), AxisHinge("yy", 0.7))
        if not isinstance(expected, CartanRelation):
            expected = expected.promote() if hasattr(expected, "promote") and not hasattr(expected, "c1") else expected
        pair_ops = [op for op in optimized.operations if op.gate in {"rxx", "ryy", "rzz"}]
        got = [0.0, 0.0, 0.0]
        index = {"rxx": 0, "ryy": 1, "rzz": 2}
        for op in pair_ops:
            got[index[op.gate]] += float(op.params["angle"])
        if isinstance(expected, CartanRelation):
            if any(abs(got[i] - value) > 1e-9 for i, value in enumerate((expected.c1, expected.c2, expected.c3))):
                raise AdapterError(
                    "Compiler pair-rotation compression does not match rqm-entanglement composition: "
                    f"{got} vs {(expected.c1, expected.c2, expected.c3)}"
                )
            ledger.mark_verified("AxisHinge", compiler_matches_compose=True)
            ledger.mark_verified("AxisHinge.promote", compiler_matches_compose=True)
            cartan = expected
        else:
            raise AdapterError(f"Expected CartanRelation from xx+yy composition, got {type(expected)!r}")

        minimized = cartan.minimize()
        block = cartan.promote()
        reconstructed = block.to_unitary()
        direct = cartan.to_unitary()
        import numpy as np

        err = float(np.max(np.abs(reconstructed - direct)))
        if err > 1e-8:
            raise AdapterError(f"QuaternionCartan reconstruction error {err} exceeds tolerance.")
        ledger.mark_executed("QuaternionCartan", reconstruction_error=err)
        ledger.inherit_from_package("QuaternionCartan", "rqm-entanglement", module="rqm_entanglement.su4")
        ledger.mark_verified("QuaternionCartan", reconstruction_error=err)
        relational.append("QuaternionCartan")
        ledger.mark_verified("rqm-entanglement", cartan_verified=True, reconstruction_error=err)

        hinge = BellHinge(1, 1)
        bell_state = hinge.to_state()
        if abs(abs(bell_state[0]) - 1 / math.sqrt(2)) > 1e-9 or abs(abs(bell_state[3]) - 1 / math.sqrt(2)) > 1e-9:
            raise AdapterError("BellHinge.to_state() did not produce Φ+ amplitudes.")
        bell_import = import_openqasm3(BELL_OPENQASM)
        if bell_import.circuit is None:
            raise AdapterError("Bell OpenQASM import failed.")
        bell_circuits = compiler_to_circuits(bell_import.circuit)
        coupling = analyze_circuit_coupling(bell_circuits.to_dict())
        if coupling.get("is_entangled") is not True:
            raise AdapterError(f"rqm-entanglement did not measure Bell entanglement: {coupling}")
        ledger.inherit_from_package("BellHinge", "rqm-entanglement", module="rqm_entanglement.relational")
        ledger.mark_executed("BellHinge", hinge_name=hinge.name)
        ledger.mark_verified("BellHinge", concurrence=coupling.get("pair_metrics"))
        relational.append("BellHinge")

        lowered = lower_circuit_for_backend(optimized, backend_family="braket_gate_model")
        if any(op.gate == "u1q" for op in lowered.operations):
            raise AdapterError("Backend lowering left u1q operations in the export IR.")
        if probe.count("rqm_core.quaternion_to_zyz") < 1:
            raise AdapterError("u1q lowering did not call rqm-core quaternion_to_zyz.")
        ledger.mark_executed(
            "rqm-core",
            u1q_count=len(u1q_ops),
            zyz_calls=probe.count("rqm_core.quaternion_to_zyz"),
        )
        ledger.mark_verified(
            "rqm-core",
            unit_quaternion=True,
            su2_matrices=probe.count("Quaternion.to_su2_matrix"),
            zyz_calls=probe.count("rqm_core.quaternion_to_zyz"),
        )
        export = export_openqasm3(lowered)
        if export.status != "EXPORTED" or not export.source:
            raise AdapterError(f"OpenQASM 3 export failed: {export.status} {export.error}")
        reimported = import_openqasm3(export.source)
        if reimported.circuit is None:
            raise AdapterError(f"Exported OpenQASM 3 could not be re-imported: {reimported.report}")
        export_equiv = verify_equivalence(lowered, reimported.circuit)
        if not export_equiv.verified:
            raise AdapterError(
                "Lowered circuit and re-imported OpenQASM 3 are not semantically equivalent: "
                f"{export_equiv.status} {export_equiv.max_abs_err} {export_equiv.notes}"
            )
        ledger.mark_executed("openqasm3_export", status=export.status, sha256=export.source_sha256)
        ledger.mark_verified("openqasm3_export", reimport_verified=True)
        ledger.mark_verified("openqasm3_import", reimport_verified=True)
        ledger.mark_verified("rqm-qiskit", export_status=export.status)

        qiskit_circuit = compiled_circuit_to_qiskit(lowered)
        ledger.mark_executed("rqm-qiskit", qiskit_instructions=len(qiskit_circuit.data))
        ledger.mark_verified("rqm-qiskit", qiskit_num_qubits=qiskit_circuit.num_qubits)

        optional_not: list[dict[str, str]] = []
        optimize_meta: dict[str, Any] | None = None
        if include_optimize and rqm_optimize is not None:
            from qiskit import QuantumCircuit

            if not isinstance(qiskit_circuit, QuantumCircuit):
                raise AdapterError("compiled_circuit_to_qiskit did not return a Qiskit circuit.")
            result = rqm_optimize.optimize(qiskit_circuit, return_metadata=True)
            ledger.mark_executed(
                "rqm-optimize",
                strategy=result.strategy,
                original_gate_count=result.original_gate_count,
                optimized_gate_count=result.optimized_gate_count,
                role="backend-adjacent-qiskit-compression",
            )
            ledger.mark_verified(
                "rqm-optimize",
                fused_runs=result.fused_runs,
                role="backend-adjacent-qiskit-compression",
            )
            optimize_meta = {
                "strategy": result.strategy,
                "fused_runs": result.fused_runs,
                "original_gate_count": result.original_gate_count,
                "optimized_gate_count": result.optimized_gate_count,
                "role": "backend-adjacent-qiskit-compression",
            }
        else:
            optional_not.append(
                {
                    "capability": "rqm-optimize",
                    "why": "Optional backend-adjacent compressor was not imported or was disabled. "
                    "It is not part of the backend-neutral compiler path.",
                }
            )

        ledger.require_executed_and_verified(REQUIRED_CORE)

    installed_versions = {
        name: (ledger.capabilities[name].details.get("version") if name in ledger.capabilities else None)
        for name in (
            "rqm-core",
            "rqm-circuits",
            "rqm-compiler",
            "rqm-entanglement",
            "rqm-qiskit",
            "rqm-optimize",
            "rqm-openqse-adapter",
        )
    }
    try:
        from importlib.metadata import version as dist_version

        installed_versions["rqm-openqse-adapter"] = dist_version("rqm-openqse-adapter")
        ledger.mark_installed("rqm-openqse-adapter", distribution="rqm-openqse-adapter")
        ledger.mark_imported("rqm-openqse-adapter", module="rqm_openqse_adapter")
        ledger.mark_executed("rqm-openqse-adapter", path="run_clean_demonstration")
        ledger.mark_verified("rqm-openqse-adapter", fail_closed=True)
    except Exception:
        pass

    return CleanDemonstrationReport(
        python_version=sys.version.replace("\n", " "),
        repository_shas=_discover_shas(ecosystem_root),
        installed_versions=installed_versions,
        capabilities=ledger.to_dict(),
        compiler_passes_executed=passes,
        relational_representations=sorted(set(relational)),
        openqasm_input=CONFORMANCE_OPENQASM,
        openqasm_output=export.source,
        semantic_verification={
            "compiler_status": compiler_report.equivalence_status,
            "compiler_verified": compiler_report.equivalence_verified,
            "export_reimport_status": export_equiv.status.value if hasattr(export_equiv.status, "value") else str(export_equiv.status),
            "export_reimport_verified": bool(export_equiv.verified),
            "export_max_abs_err": export_equiv.max_abs_err,
            "platform": platform.platform(),
        },
        optional_not_exercised=optional_not,
        details={
            "compiler_report": {
                "original_gate_count": compiler_report.original_gate_count,
                "optimized_gate_count": compiler_report.optimized_gate_count,
                "passes_applied": passes,
                "optimization_applied": compiler_report.optimization_applied,
                "fallback_reason": compiler_report.fallback_reason,
            },
            "probe_counts": {key: len(values) for key, values in probe.calls.items()},
            "optimized_operations": [op.to_descriptor() for op in optimized.operations],
            "lowered_operations": [op.to_descriptor() for op in lowered.operations],
            "rqm_optimize": optimize_meta,
            "bell_coupling_mode": coupling.get("mode"),
            "quaternion_cartan_error": err,
            "minimized_relation": type(minimized).__name__,
        },
    )
