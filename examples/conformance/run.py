"""Run OpenQASM3 through the real cross-repository RQM ecosystem."""

from __future__ import annotations

import json
from pathlib import Path

from rqm_openqse_adapter.ecosystem import run_rqm_ecosystem
from rqm_openqse_adapter.openqasm3 import loads_openqasm3
from rqm_openqse_adapter.openqse.contract import rqm_quaternionic_compiler_contract

HERE = Path(__file__).resolve().parent
ARTIFACTS = HERE / "artifacts"


def main() -> None:
    source = (HERE / "bell.qasm").read_text()
    contract = rqm_quaternionic_compiler_contract()
    before = loads_openqasm3(source).to_module()

    result = run_rqm_ecosystem(source)
    after = loads_openqasm3(result.output_openqasm3).to_module()

    report = {
        "status": "pass",
        "experiment": "OpenQASM3 -> openqse-rqm-adapter -> real RQM ecosystem -> OpenQASM3",
        "contract": contract.to_dict(),
        "repositories_used": result.repositories_used,
        "ecosystem_evidence": result.evidence,
        "checks": {
            "output_reparses": True,
            "qubit_count_preserved": before.num_qubits == after.num_qubits,
            "clbit_count_preserved": before.num_clbits == after.num_clbits,
            "real_rqm_compiler_used": "rqm-compiler" in result.repositories_used,
            "real_rqm_entanglement_used": "rqm-entanglement" in result.repositories_used,
            "u1q_pipeline_exercised": result.evidence["compiler"]["u1q_count"] >= 1,
            "axis_hinge_to_cartan_promotion_exercised": result.evidence["relational"]["cartan_relation_observed"],
        },
        "disclaimer": "Experimental RQM interoperability demonstration; not an official openQSE conformance test.",
    }
    if not all(report["checks"].values()):
        report["status"] = "fail"

    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "input.qasm").write_text(source)
    (ARTIFACTS / "output.qasm").write_text(result.output_openqasm3)
    (ARTIFACTS / "contract.json").write_text(json.dumps(contract.to_dict(), indent=2, sort_keys=True) + "\n")
    (ARTIFACTS / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
