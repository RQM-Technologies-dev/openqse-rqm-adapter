from pathlib import Path

from rqm_openqse_adapter.openqasm3 import dumps_openqasm3, loads_openqasm3
from rqm_openqse_adapter.openqse.contract import rqm_quaternionic_compiler_contract
from rqm_openqse_adapter.passes.pipeline import PassContext, PassManager
from rqm_openqse_adapter.targets.target import local_simulator_target
from rqm_openqse_adapter.config import AdapterConfig


FIXTURE = Path(__file__).parents[1] / "examples" / "conformance" / "bell.qasm"


def test_conformance_seam_round_trips_through_rqm_passes():
    source = FIXTURE.read_text()
    before = loads_openqasm3(source, name="conformance").to_module()
    context = PassContext(target=local_simulator_target(), config=AdapterConfig())
    after = PassManager().run(before, context)
    exchanged = dumps_openqasm3(after)
    reparsed = loads_openqasm3(exchanged).to_module()

    assert context.applied
    assert reparsed.num_qubits == before.num_qubits
    assert reparsed.num_clbits == before.num_clbits
    assert len(reparsed.operations) == len(before.operations)


def test_conformance_contract_is_openqasm_on_both_sides():
    contract = rqm_quaternionic_compiler_contract()
    assert contract.input.artifact_type == "LogicalCircuit"
    assert contract.output.artifact_type == "LogicalCircuit"
    assert contract.input.encoding == "OpenQASM3"
    assert contract.output.encoding == "OpenQASM3"
    assert contract.provenance["internal_ir"] == "RQM-Quaternionic-IR/0.1"
