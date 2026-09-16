from __future__ import annotations

import json
from pathlib import Path

from rqm_openqse_adapter import OpenQSEAdapter, local_simulator_target
from rqm_openqse_adapter.frontend.quaternionic_input import QuaternionicProgram


def build_program() -> QuaternionicProgram:
    program = QuaternionicProgram(name="openqse_boundary", num_qubits=2, num_clbits=2)
    program.h(0)
    program.cx(0, 1)
    program.measure_all()
    program.metadata["boundary"] = "RQM quaternionic IR -> adapter -> OpenQSE-compatible artifact"
    return program


def main() -> None:
    adapter = OpenQSEAdapter(target=local_simulator_target(qubit_count=4))
    print("Input: quaternionic program with H + CX")
    ir = adapter.lower(build_program())
    print("Quaternionic IR still contains quaternion attributes:")
    for op in ir.operations:
        print(f"  {op.name}: quaternion={op.attributes.get('quaternion')}")
    payload = adapter.emit(build_program())
    artifact = payload.to_dict()
    print("\nOpenQSE-compatible artifact keys:", sorted(artifact.keys()))
    print("Payload instructions (no quaternion field):")
    print(json.dumps(artifact["circuit"]["instructions"], indent=2, default=str))
    print("\nTarget metadata")
    print(json.dumps(artifact["target"], indent=2, sort_keys=True))
    print("\nResource metadata")
    print(json.dumps(artifact["resources"], indent=2, sort_keys=True))
    print("\nDiagnostics")
    print(json.dumps(artifact["diagnostics"], indent=2))
    out = Path(__file__).parent / "openqse-artifact.json"
    out.write_text(payload.to_json())
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
