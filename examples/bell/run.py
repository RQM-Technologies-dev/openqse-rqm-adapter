from __future__ import annotations

import json
from pathlib import Path

from rqm_openqse_adapter import compile, local_simulator_target
from rqm_openqse_adapter.frontend.quaternionic_input import QuaternionicProgram


def build_program() -> QuaternionicProgram:
    program = QuaternionicProgram(name="bell_h_cx", num_qubits=2, num_clbits=2)
    program.h(0)
    program.cx(0, 1)
    program.measure_all()
    program.metadata["intent"] = (
        "Demonstrate multi-qubit lowering of a conventional H+CX sequence. "
        "The simulator result matches the usual Bell computational-basis "
        "probabilities for this gate list; this is not a distinct quaternionic Bell primitive."
    )
    return program


def main() -> None:
    result = compile(build_program(), local_simulator_target(qubit_count=4), execute=True)
    print("Lowered IR operations:")
    for op in result.module.operations:
        print(f"  {op.name} qubits={op.qubit_indices()} quat={op.attributes.get('quaternion')}")
    print("\nOpenQSE-compatible circuit")
    print(json.dumps(result.payload.circuit, indent=2, sort_keys=True, default=str))
    print("\nExecution probabilities")
    print(json.dumps(result.execution.probabilities if result.execution else {}, indent=2))
    out = Path(__file__).parent / "artifact.json"
    out.write_text(result.payload.to_json())
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
