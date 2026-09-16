from __future__ import annotations

import math

from rqm_openqse_adapter import compile, local_simulator_target
from rqm_openqse_adapter.frontend.quaternionic_input import QuaternionicProgram
from rqm_openqse_adapter.ir.operations import SQRT2_INV


def test_end_to_end_bell_probabilities() -> None:
    program = QuaternionicProgram(name="bell", num_qubits=2, num_clbits=2)
    program.h(0)
    program.cx(0, 1)
    program.measure_all()
    result = compile(program, local_simulator_target(qubit_count=4), execute=True)
    assert result.execution is not None
    probs = result.execution.probabilities
    assert math.isclose(probs.get("00", 0.0), 0.5, abs_tol=1e-9)
    assert math.isclose(probs.get("11", 0.0), 0.5, abs_tol=1e-9)
    assert math.isclose(probs.get("01", 0.0), 0.0, abs_tol=1e-9)
    assert math.isclose(probs.get("10", 0.0), 0.0, abs_tol=1e-9)
    assert result.payload.provenance["adapter"] == "rqm-openqse-adapter"
    assert [inst["op"] for inst in result.payload.circuit["instructions"][:2]] == ["h", "cx"]


def test_end_to_end_u1q_hadamard_probabilities() -> None:
    program = QuaternionicProgram(name="u1q-h", num_qubits=1, num_clbits=1)
    program.u1q(0, 0.0, SQRT2_INV, 0.0, SQRT2_INV)
    program.measure(0, 0)
    result = compile(program, execute=True)
    assert result.execution is not None
    probs = result.execution.probabilities
    assert math.isclose(probs.get("0", 0.0), 0.5, abs_tol=1e-9)
    assert math.isclose(probs.get("1", 0.0), 0.5, abs_tol=1e-9)
    assert result.execution.kind == "ideal-statevector-probabilities"
