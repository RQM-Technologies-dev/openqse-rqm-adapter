"""Run the OpenQASM3 -> RQM IR -> passes -> OpenQASM3 conformance demo."""

from __future__ import annotations

import json
from pathlib import Path

from rqm_openqse_adapter.openqasm3 import dumps_openqasm3, loads_openqasm3
from rqm_openqse_adapter.openqse.contract import rqm_quaternionic_compiler_contract
from rqm_openqse_adapter.passes.pipeline import PassContext, PassManager
from rqm_openqse_adapter.targets.target import local_simulator_target
from rqm_openqse_adapter.config import AdapterConfig

HERE = Path(__file__).resolve().parent
ARTIFACTS = HERE / "artifacts"


def main() -> None:
    source = (HERE / "bell.qasm").read_text()
    contract = rqm_quaternionic_compiler_contract()

    program = loads_openqasm3(source, name="openqse-rqm-bell-conformance")
    input_module = program.to_module()

    context = PassContext(target=local_simulator_target(), config=AdapterConfig())
    output_module = PassManager().run(input_module, context)
    output_qasm = dumps_openqasm3(output_module)

    # Reparse the emitted exchange artifact: the demo is not successful if the
    # adapter cannot consume what it produced.
    reparsed = loads_openqasm3(output_qasm, name="roundtrip-check").to_module()

    report = {
        "status": "pass",
        "experiment": "OpenQASM3 -> RQM Quaternionic IR -> RQM passes -> OpenQASM3",
        "contract": contract.to_dict(),
        "input": {
            "artifact_type": "LogicalCircuit",
            "encoding": "OpenQASM3",
            "operations": len(input_module.operations),
        },
        "internal": {
            "ir": "RQM-Quaternionic-IR/0.1",
            "passes_applied": list(context.applied),
            "quaternionic_semantics_exposed_downstream": False,
        },
        "output": {
            "artifact_type": "LogicalCircuit",
            "encoding": "OpenQASM3",
            "operations_after_reparse": len(reparsed.operations),
        },
        "checks": {
            "output_reparses": True,
            "operation_count_preserved": len(input_module.operations) == len(reparsed.operations),
            "qubit_count_preserved": input_module.num_qubits == reparsed.num_qubits,
            "clbit_count_preserved": input_module.num_clbits == reparsed.num_clbits,
        },
        "disclaimer": "Experimental RQM interoperability demonstration; not an official openQSE conformance test.",
    }
    if not all(report["checks"].values()):
        report["status"] = "fail"

    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "input.qasm").write_text(source)
    (ARTIFACTS / "output.qasm").write_text(output_qasm)
    (ARTIFACTS / "contract.json").write_text(json.dumps(contract.to_dict(), indent=2, sort_keys=True) + "\n")
    (ARTIFACTS / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
