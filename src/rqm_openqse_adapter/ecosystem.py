"""Bridge the OpenQSE-facing adapter to installed RQM ecosystem packages.

The external exchange remains OpenQASM 3. Internally this bridge delegates to
rqm-compiler and, through that package, rqm-core/rqm-entanglement. Optional
Qiskit assurance/export and rqm-optimize stages are reported when installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .diagnostics import UnsupportedConstructError
from .openqasm3 import loads_openqasm3


@dataclass
class EcosystemResult:
    output_openqasm3: str
    repositories_used: list[str]
    evidence: dict[str, Any] = field(default_factory=dict)


def _to_compiler_circuit(source: str):
    from rqm_compiler import Circuit

    module = loads_openqasm3(source, name="openqse-rqm-exchange").to_module()
    circuit = Circuit(module.num_qubits)
    for op in module.operations:
        name = op.name
        params = {p.name: p.value for p in op.parameters}
        targets = op.target_indices()
        controls = op.control_indices()
        if name == "measure":
            for q in targets or op.qubit_indices():
                circuit.measure(q)
        elif name in {"cx", "cz"}:
            getattr(circuit, name)(controls[0], targets[0])
        elif name == "swap":
            qs = op.qubit_indices()
            circuit.swap(qs[0], qs[1])
        elif name == "barrier":
            # Compiler IR has no semantic need for barriers in this experiment.
            continue
        elif name in {"rx", "ry", "rz"}:
            getattr(circuit, name)(targets[0], params.get("angle"))
        elif hasattr(circuit, name):
            getattr(circuit, name)(targets[0])
        else:
            raise UnsupportedConstructError(f"No rqm-compiler bridge for {name!r}")
    return circuit


def _compiler_to_openqasm3(circuit) -> str:
    """Lower compiler u1q form to named 1q gates, then emit OpenQASM 3."""
    from rqm_compiler import lower_circuit_for_backend

    lowered = lower_circuit_for_backend(circuit, backend_family="braket_gate_model")
    lines = ["OPENQASM 3;", 'include "stdgates.inc";', f"qubit[{lowered.num_qubits}] q;", f"bit[{lowered.num_qubits}] c;"]
    for op in lowered.operations:
        gate = op.gate
        if gate == "measure":
            for q in op.targets:
                lines.append(f"c[{q}] = measure q[{q}];")
            continue
        qubits = list(op.controls) + list(op.targets)
        args = ", ".join(f"q[{q}]" for q in qubits)
        if op.params:
            if "angle" in op.params:
                lines.append(f"{gate}({float(op.params['angle']):.17g}) {args};")
            else:
                raise UnsupportedConstructError(f"Cannot export compiler parameters for {gate!r}")
        else:
            lines.append(f"{gate} {args};")
    return "\n".join(lines) + "\n"


def run_rqm_ecosystem(source: str) -> EcosystemResult:
    """Run OpenQASM through the real RQM compiler and relational stack."""
    from rqm_compiler import AdaptiveCartanPolicy, optimize_circuit
    from rqm_entanglement import AxisHinge, BellHinge, CartanRelation, compose_relations

    compiler_input = _to_compiler_circuit(source)
    optimized, report = optimize_circuit(compiler_input, adaptive_policy=AdaptiveCartanPolicy.safe())

    # Exercise the public adaptive-relational API as interoperability evidence.
    hinge_x = AxisHinge("xx", 0.125)
    hinge_z = AxisHinge("zz", 0.25)
    promoted = compose_relations(hinge_x, hinge_z)
    bell = BellHinge(1, 1)

    repositories = ["rqm-core", "rqm-circuits", "rqm-compiler", "rqm-entanglement"]
    evidence: dict[str, Any] = {
        "compiler": {
            "input_operations": len(compiler_input.operations),
            "output_operations": len(optimized.operations),
            "u1q_count": sum(op.gate == "u1q" for op in optimized.operations),
            "pipeline": ["normalize", "canonicalize", "flatten", "to_u1q", "merge_u1q", "sign_canon", "cancel_2q"],
            "report": getattr(report, "to_dict", lambda: {"repr": repr(report)})(),
        },
        "relational": {
            "bell": bell.name,
            "axis_hinge": {"axis": hinge_x.axis, "theta": hinge_x.theta},
            "promotion_result": type(promoted).__name__,
            "cartan_relation_observed": isinstance(promoted, CartanRelation),
        },
    }

    # rqm-qiskit is optional because it brings the Qiskit dependency surface.
    try:
        from rqm_qiskit import assure_openqasm3
        assurance = assure_openqasm3(source)
        repositories.append("rqm-qiskit")
        evidence["qiskit_assurance"] = {"available": True, "result": repr(assurance)}
    except (ImportError, ModuleNotFoundError) as exc:
        evidence["qiskit_assurance"] = {"available": False, "reason": str(exc)}

    # rqm-optimize is deliberately backend-adjacent and Qiskit-circuit based;
    # record availability rather than forcing it into the backend-neutral path.
    try:
        import rqm_optimize  # noqa: F401
        repositories.append("rqm-optimize")
        evidence["rqm_optimize"] = {"available": True, "stage": "backend-adjacent"}
    except (ImportError, ModuleNotFoundError) as exc:
        evidence["rqm_optimize"] = {"available": False, "reason": str(exc)}

    return EcosystemResult(
        output_openqasm3=_compiler_to_openqasm3(optimized),
        repositories_used=repositories,
        evidence=evidence,
    )
