from __future__ import annotations

from rqm_openqse_adapter import OpenQSEAdapter, emit, local_simulator_target
from rqm_openqse_adapter.frontend.quaternionic_input import QuaternionicProgram
from rqm_openqse_adapter.ir.operations import SQRT2_INV


def _has_quaternion_field(value) -> bool:
    if isinstance(value, dict):
        if "quaternion" in value:
            return True
        return any(_has_quaternion_field(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_quaternion_field(item) for item in value)
    return False


def test_adapter_emit_has_expected_artifact_structure() -> None:
    program = QuaternionicProgram(name="artifact", num_qubits=1, num_clbits=1)
    program.u1q(0, 0.0, SQRT2_INV, 0.0, SQRT2_INV)
    program.measure(0, 0)
    payload = emit(program, target=local_simulator_target())
    data = payload.to_dict()
    assert data["schema"] == "rqm-openqse-payload/v0.1"
    assert data["status"] == "experimental"
    assert "not an official OpenQSE" in data["disclaimer"].lower() or "Not an official OpenQSE" in data["disclaimer"]
    assert data["circuit"]["num_qubits"] == 1
    first = data["circuit"]["instructions"][0]
    assert first["op"] == "unitary"
    assert first["origin"] == "u1q"
    assert "unitary" in first
    assert "params" not in first
    assert "quaternion" not in first
    assert data["resources"]["qubit_count"] == 1
    assert "unitary" in data["resources"]["required_operations"]
    assert data["target"]["name"] == "rqm-local-statevector"
    assert data["provenance"]["owner"] == "RQM Technologies"
    assert data["provenance"]["pipeline"] == ["validate", "canonicalize", "lower"]
    assert not _has_quaternion_field(data["circuit"])


def test_named_gates_remain_named_on_the_openqse_side() -> None:
    program = QuaternionicProgram(name="named", num_qubits=2, num_clbits=2)
    program.h(0)
    program.cx(0, 1)
    payload = emit(program)
    ops = [inst["op"] for inst in payload.circuit["instructions"]]
    assert ops == ["h", "cx"]
    assert "quaternion" not in payload.circuit["instructions"][0]


def test_adapter_class_matches_functional_api() -> None:
    program = QuaternionicProgram(name="api", num_qubits=1)
    program.x(0)
    adapter = OpenQSEAdapter(target=local_simulator_target())
    payload = adapter.emit(program)
    assert payload.circuit["instructions"][0]["op"] == "x"
    diagnostics = adapter.validate(program)
    assert diagnostics.ok()
