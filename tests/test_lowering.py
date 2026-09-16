from __future__ import annotations

import math

from rqm_openqse_adapter import AdapterConfig, lower
from rqm_openqse_adapter.frontend.quaternionic_input import QuaternionicProgram
from rqm_openqse_adapter.ir.operations import SQRT2_INV
from rqm_openqse_adapter.passes import CanonicalizePass, LowerPass, PassContext, PassManager, ValidatePass
from rqm_openqse_adapter.targets.target import local_simulator_target


def test_pass_order_is_validate_canonicalize_lower() -> None:
    manager = PassManager()
    assert [p.name for p in manager.passes] == ["validate", "canonicalize", "lower"]


def test_canonicalization_drops_identity_and_adds_quaternion() -> None:
    program = QuaternionicProgram(name="canon", num_qubits=1)
    program.i(0)
    program.h(0)
    module = PassManager([CanonicalizePass()]).run(program.to_module(), PassContext(target=None))
    names = [op.name for op in module.operations]
    assert names == ["h"]
    quat = module.operations[0].attributes.get("quaternion")
    assert quat is not None
    assert math.isclose(quat["x"], SQRT2_INV, rel_tol=1e-12)


def test_identity_can_be_retained() -> None:
    program = QuaternionicProgram(name="keep-i", num_qubits=1)
    program.i(0)
    config = AdapterConfig(drop_identity=False)
    module = PassManager([CanonicalizePass()]).run(
        program.to_module(), PassContext(target=None, config=config)
    )
    assert [op.name for op in module.operations] == ["i"]


def test_lowering_attaches_su2_and_marks_payload_ready() -> None:
    program = QuaternionicProgram(name="lower", num_qubits=2)
    program.h(0)
    program.cx(0, 1)
    module = lower(program, target=local_simulator_target())
    hadamard = module.operations[0]
    assert hadamard.attributes.get("su2") is not None
    assert hadamard.attributes.get("lowered") is True
    assert module.metadata["payload_ready"] is True
    assert module.operations[1].name == "cx"


def test_parameter_alias_theta_becomes_angle() -> None:
    program = QuaternionicProgram(name="alias", num_qubits=1)
    program.op("rx", 0, params={"theta": 0.25})
    module = PassManager([ValidatePass(), CanonicalizePass()]).run(
        program.to_module(), PassContext(target=local_simulator_target())
    )
    assert module.operations[0].parameters[0].name == "angle"


def test_custom_pass_can_be_inserted() -> None:
    class MarkPass:
        name = "mark"

        def run(self, module, context):
            module.metadata["custom"] = True
            return module

    program = QuaternionicProgram(name="ext", num_qubits=1)
    program.h(0)
    manager = PassManager([ValidatePass(), CanonicalizePass(), MarkPass(), LowerPass()])
    module = manager.run(program.to_module(), PassContext(target=local_simulator_target()))
    assert module.metadata["custom"] is True
    assert module.metadata["lowered"] is True
