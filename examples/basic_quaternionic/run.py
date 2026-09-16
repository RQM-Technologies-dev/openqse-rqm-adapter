from __future__ import annotations

import json
from pathlib import Path

from rqm_openqse_adapter import compile, local_simulator_target
from rqm_openqse_adapter.frontend.quaternionic_input import QuaternionicProgram
from rqm_openqse_adapter.ir.operations import SQRT2_INV


def build_program() -> QuaternionicProgram:
    program = QuaternionicProgram(name="basic_quaternionic", num_qubits=1, num_clbits=1)
    # Native unit-quaternion Hadamard: q = (i + k) / √2
    program.u1q(0, 0.0, SQRT2_INV, 0.0, SQRT2_INV)
    program.measure(0, 0)
    program.metadata["intent"] = "Show quaternionic input -> IR -> adapter payload."
    return program


def main() -> None:
    result = compile(build_program(), local_simulator_target(qubit_count=2), execute=True)
    print("Quaternionic IR")
    print(result.ir_json)
    print("\nOpenQSE-compatible payload (quaternion components omitted)")
    print(result.payload.to_json())
    print("\nLocal simulator result")
    print(json.dumps(result.execution.to_dict() if result.execution else {}, indent=2, sort_keys=True))
    out = Path(__file__).parent / "artifact.json"
    out.write_text(result.payload.to_json())
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
