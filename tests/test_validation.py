from __future__ import annotations

import pytest

from rqm_openqse_adapter import ValidationError, local_simulator_target, validate
from rqm_openqse_adapter.frontend.quaternionic_input import QuaternionicProgram
from rqm_openqse_adapter.targets.target import Target


def test_unknown_operation_is_rejected() -> None:
    program = QuaternionicProgram(name="bad", num_qubits=1)
    program.op("not-a-gate", 0)
    diagnostics = validate(program)
    assert not diagnostics.ok()
    assert any(item.code == "unknown_operation" for item in diagnostics.errors())
    with pytest.raises(ValidationError):
        from rqm_openqse_adapter import compile

        compile(program)


def test_qubit_out_of_range() -> None:
    program = QuaternionicProgram(name="oob", num_qubits=1)
    program.h(3)
    # Builder expands qubit count; force a stale module instead.
    module = program.to_module()
    module.qubits = module.qubits[:1]
    diagnostics = validate(module)
    assert any(item.code == "qubit_out_of_range" for item in diagnostics.errors())


def test_cx_cannot_reuse_the_same_qubit() -> None:
    program = QuaternionicProgram(name="same", num_qubits=1)
    program.cx(0, 0)
    diagnostics = validate(program)
    assert any(item.code == "duplicate_operands" for item in diagnostics.errors())


def test_rx_requires_angle() -> None:
    program = QuaternionicProgram(name="rx", num_qubits=1)
    program.op("rx", 0)
    diagnostics = validate(program)
    assert any(item.code == "missing_parameters" for item in diagnostics.errors())


def test_non_unit_quaternion_is_invalid() -> None:
    program = QuaternionicProgram(name="u1q", num_qubits=1)
    program.u1q(0, 1.0, 1.0, 0.0, 0.0)
    diagnostics = validate(program)
    assert any(item.code == "non_unit_quaternion" for item in diagnostics.errors())


def test_target_rejects_insufficient_qubits() -> None:
    program = QuaternionicProgram(name="wide", num_qubits=4)
    program.h(0)
    target = local_simulator_target(qubit_count=2)
    diagnostics = validate(program, target=target)
    assert any(item.code == "target_qubit_capacity" for item in diagnostics.errors())


def test_target_rejects_unsupported_operation() -> None:
    program = QuaternionicProgram(name="swap-only-not", num_qubits=2)
    program.swap(0, 1)
    target = Target(
        name="limited",
        qubit_count=4,
        supported_operations=["h", "cx", "measure"],
    )
    diagnostics = validate(program, target=target)
    assert any(item.code == "unsupported_on_target" for item in diagnostics.errors())


def test_valid_program_passes() -> None:
    program = QuaternionicProgram(name="ok", num_qubits=1, num_clbits=1)
    program.h(0)
    program.measure(0, 0)
    diagnostics = validate(program, target=local_simulator_target())
    assert diagnostics.ok()
