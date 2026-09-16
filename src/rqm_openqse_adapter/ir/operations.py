"""Stable operation names and the quaternion/SU(2) forms this prototype supports.

The quaternion forms follow the RQM / rqm-circuits convention: a complete unit
quaternion encodes the same single-qubit rotation information as an SU(2)
matrix. Two-qubit operations are ordinary named gates; this prototype does not
assign them a quaternionic algebra.

SU(2) mapping (RQM convention):

    U(q) = [[ w - i z,  -y - i x ],
            [ y - i x,   w + i z ]]

Named-gate matrices derived this way may differ from textbook matrices by a
global phase. Computational-basis probabilities are invariant under that phase.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

SQRT2_INV = 1.0 / math.sqrt(2.0)

ALIAS_NAMES: dict[str, str] = {
    "id": "i",
    "identity": "i",
    "cnot": "cx",
    "cxnot": "cx",
    "measure_z": "measure",
    "mz": "measure",
}

PARAM_ALIASES: dict[str, str] = {
    "theta": "angle",
    "phi": "angle",
    "lambda": "angle",
}


@dataclass(frozen=True)
class OperationSpec:
    name: str
    qubit_count: int
    control_count: int = 0
    param_names: tuple[str, ...] = ()
    has_quaternion_form: bool = False
    categories: tuple[str, ...] = ()
    description: str = ""


OPERATION_SPECS: dict[str, OperationSpec] = {
    "i": OperationSpec("i", 1, has_quaternion_form=True, categories=("clifford", "single_qubit"), description="Identity."),
    "x": OperationSpec("x", 1, has_quaternion_form=True, categories=("clifford", "single_qubit"), description="Pauli X. Quaternion q = i."),
    "y": OperationSpec("y", 1, has_quaternion_form=True, categories=("clifford", "single_qubit"), description="Pauli Y. Quaternion q = j."),
    "z": OperationSpec("z", 1, has_quaternion_form=True, categories=("clifford", "single_qubit"), description="Pauli Z. Quaternion q = k."),
    "h": OperationSpec("h", 1, has_quaternion_form=True, categories=("clifford", "single_qubit"), description="Hadamard. Quaternion q = (i+k)/√2."),
    "s": OperationSpec("s", 1, has_quaternion_form=True, categories=("clifford", "single_qubit"), description="Phase S. Quaternion q = cos(π/4) + k sin(π/4)."),
    "t": OperationSpec("t", 1, has_quaternion_form=True, categories=("single_qubit",), description="T gate. Quaternion q = cos(π/8) + k sin(π/8)."),
    "rx": OperationSpec("rx", 1, param_names=("angle",), has_quaternion_form=True, categories=("rotation", "single_qubit"), description="X-rotation. q = cos(θ/2) + i sin(θ/2)."),
    "ry": OperationSpec("ry", 1, param_names=("angle",), has_quaternion_form=True, categories=("rotation", "single_qubit"), description="Y-rotation. q = cos(θ/2) + j sin(θ/2)."),
    "rz": OperationSpec("rz", 1, param_names=("angle",), has_quaternion_form=True, categories=("rotation", "single_qubit"), description="Z-rotation. q = cos(θ/2) + k sin(θ/2)."),
    "u1q": OperationSpec(
        "u1q",
        1,
        param_names=("w", "x", "y", "z"),
        has_quaternion_form=True,
        categories=("single_qubit", "native_quaternion"),
        description="Native unit-quaternion single-qubit unitary.",
    ),
    "cx": OperationSpec("cx", 1, control_count=1, categories=("clifford", "two_qubit"), description="CNOT. Standard two-qubit gate; no quaternion form."),
    "cz": OperationSpec("cz", 1, control_count=1, categories=("clifford", "two_qubit"), description="Controlled-Z. Standard two-qubit gate; no quaternion form."),
    "swap": OperationSpec("swap", 2, categories=("clifford", "two_qubit"), description="SWAP. Standard two-qubit gate; no quaternion form."),
    "measure": OperationSpec("measure", 1, categories=("measurement",), description="Computational-basis measurement."),
    "barrier": OperationSpec("barrier", 0, categories=("directive",), description="Compiler barrier. Arity is variable."),
}


def canonicalize_name(name: str) -> str:
    key = name.strip().lower()
    return ALIAS_NAMES.get(key, key)


def get_spec(name: str) -> OperationSpec | None:
    return OPERATION_SPECS.get(canonicalize_name(name))


def is_known_operation(name: str) -> bool:
    return get_spec(name) is not None


def named_quaternion(name: str, params: Mapping[str, float] | None = None) -> tuple[float, float, float, float] | None:
    """Return (w, x, y, z) for operations that have an explicit quaternion form."""

    spec_name = canonicalize_name(name)
    params = params or {}
    if spec_name == "i":
        return (1.0, 0.0, 0.0, 0.0)
    if spec_name == "x":
        return (0.0, 1.0, 0.0, 0.0)
    if spec_name == "y":
        return (0.0, 0.0, 1.0, 0.0)
    if spec_name == "z":
        return (0.0, 0.0, 0.0, 1.0)
    if spec_name == "h":
        return (0.0, SQRT2_INV, 0.0, SQRT2_INV)
    if spec_name == "s":
        return (math.cos(math.pi / 4), 0.0, 0.0, math.sin(math.pi / 4))
    if spec_name == "t":
        return (math.cos(math.pi / 8), 0.0, 0.0, math.sin(math.pi / 8))
    if spec_name in {"rx", "ry", "rz"}:
        angle = float(params["angle"])
        half = angle / 2.0
        c, s = math.cos(half), math.sin(half)
        if spec_name == "rx":
            return (c, s, 0.0, 0.0)
        if spec_name == "ry":
            return (c, 0.0, s, 0.0)
        return (c, 0.0, 0.0, s)
    if spec_name == "u1q":
        return (float(params["w"]), float(params["x"]), float(params["y"]), float(params["z"]))
    return None


def quaternion_to_su2(w: float, x: float, y: float, z: float) -> list[list[complex]]:
    """RQM-convention SU(2) matrix for a unit quaternion."""

    return [
        [complex(w, -z), complex(-y, -x)],
        [complex(y, -x), complex(w, z)],
    ]


def quaternion_norm(w: float, x: float, y: float, z: float) -> float:
    return math.sqrt(w * w + x * x + y * y + z * z)


def is_unit_quaternion(w: float, x: float, y: float, z: float, *, atol: float = 1e-8) -> bool:
    return abs(quaternion_norm(w, x, y, z) - 1.0) <= atol
