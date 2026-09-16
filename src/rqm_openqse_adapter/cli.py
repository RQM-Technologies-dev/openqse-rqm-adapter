from __future__ import annotations

import argparse
import json
from pathlib import Path

from .api import compile
from .frontend.quaternionic_input import QuaternionicProgram
from .ir.operations import SQRT2_INV
from .targets.target import local_simulator_target


def basic_program() -> QuaternionicProgram:
    program = QuaternionicProgram(name="basic_u1q", num_qubits=1, num_clbits=1)
    program.u1q(0, 0.0, SQRT2_INV, 0.0, SQRT2_INV)
    program.measure(0, 0)
    program.metadata["description"] = "Native u1q Hadamard quaternion followed by Z-measurement."
    return program


def bell_program() -> QuaternionicProgram:
    program = QuaternionicProgram(name="bell_h_cx", num_qubits=2, num_clbits=2)
    program.h(0)
    program.cx(0, 1)
    program.measure_all()
    program.metadata["description"] = (
        "Standard H+CX circuit used to demonstrate two-qubit lowering. "
        "This prototype establishes the usual computational-basis Bell probabilities "
        "for this gate sequence; it does not introduce a distinct quaternionic Bell gate."
    )
    return program


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run RQM OpenQSE adapter demonstrations.")
    parser.add_argument(
        "example",
        nargs="?",
        default="all",
        choices=["all", "basic", "bell", "openqse"],
        help="Which demonstration to run.",
    )
    parser.add_argument(
        "--save",
        type=Path,
        default=None,
        help="Optional directory to write IR and payload JSON files.",
    )
    return parser


def run_example(name: str, *, save_dir: Path | None = None) -> dict:
    programs = {
        "basic": basic_program,
        "bell": bell_program,
        "openqse": bell_program,
    }
    program = programs[name]()
    if name == "openqse":
        program.name = "openqse_boundary"
        program.metadata["boundary"] = "quaternionic-ir -> rqm-passes -> openqse-payload"
    result = compile(program, local_simulator_target(qubit_count=4), execute=True)
    payload = result.payload.to_dict()
    output = {
        "example": name,
        "ir": result.module.to_dict(),
        "payload": payload,
        "execution": result.execution.to_dict() if result.execution else None,
        "pipeline": payload["provenance"]["pipeline"],
    }
    if save_dir is not None:
        save_dir.mkdir(parents=True, exist_ok=True)
        (save_dir / f"{name}-ir.json").write_text(result.ir_json)
        (save_dir / f"{name}-payload.json").write_text(result.payload.to_json())
    return output


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    names = ["basic", "bell", "openqse"] if args.example == "all" else [args.example]
    for name in names:
        output = run_example(name, save_dir=args.save)
        print(f"=== {name} ===")
        print(json.dumps(
            {
                "pipeline": output["pipeline"],
                "circuit": output["payload"]["circuit"],
                "resources": output["payload"]["resources"],
                "execution": output["execution"],
            },
            indent=2,
            sort_keys=True,
        ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
