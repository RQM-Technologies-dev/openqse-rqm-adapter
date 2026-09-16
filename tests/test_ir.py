from __future__ import annotations

import json
import math

from rqm_openqse_adapter.frontend.quaternionic_input import QuaternionicProgram
from rqm_openqse_adapter.ir.operations import SQRT2_INV, named_quaternion, quaternion_to_su2
from rqm_openqse_adapter.ir.serialization import dumps, loads


def test_module_construction_and_qubit_metadata() -> None:
    program = QuaternionicProgram(name="demo", num_qubits=2)
    program.h(0)
    program.cx(0, 1)
    module = program.to_module()
    assert module.name == "demo"
    assert module.num_qubits == 2
    assert [op.name for op in module.operations] == ["h", "cx"]
    assert module.operations[1].control_indices() == [0]
    assert module.operations[1].target_indices() == [1]
    assert module.target_requirements.min_qubits == 2
    assert "h" in module.required_operations()
    assert "cx" in module.required_operations()


def test_json_round_trip_preserves_operations() -> None:
    program = QuaternionicProgram(name="roundtrip", num_qubits=1, num_clbits=1)
    program.rx(0, 0.5)
    program.measure(0, 0)
    original = program.to_module()
    restored = loads(dumps(original))
    assert restored.name == original.name
    assert restored.num_qubits == 1
    assert restored.operations[0].name == "rx"
    assert restored.operations[0].parameter_map()["angle"] == 0.5
    assert restored.operations[1].name == "measure"
    parsed = json.loads(dumps(original))
    assert parsed["schema"] == "rqm-quaternionic-ir/v0.1"
    assert parsed["status"] == "experimental"


def test_named_quaternion_hadamard_matches_documented_form() -> None:
    w, x, y, z = named_quaternion("h")
    assert math.isclose(w, 0.0, abs_tol=1e-12)
    assert math.isclose(x, SQRT2_INV, rel_tol=1e-12)
    assert math.isclose(y, 0.0, abs_tol=1e-12)
    assert math.isclose(z, SQRT2_INV, rel_tol=1e-12)
    matrix = quaternion_to_su2(w, x, y, z)
    # First column is U|0>. Global phase may differ from textbook H.
    amp0, amp1 = matrix[0][0], matrix[1][0]
    assert math.isclose(abs(amp0), SQRT2_INV, rel_tol=1e-12)
    assert math.isclose(abs(amp1), SQRT2_INV, rel_tol=1e-12)
