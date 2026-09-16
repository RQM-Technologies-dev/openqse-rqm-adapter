"""Ideal local statevector backend.

This is a small RQM-owned simulator used to prove the adapter pipeline. It is
not a hardware backend and does not implement OpenQSE runtime behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..config import AdapterConfig
from ..diagnostics import AdapterError
from ..ir.operations import quaternion_to_su2
from ..openqse.payload import OpenQSEPayload


@dataclass
class ExecutionResult:
    backend: str
    kind: str
    probabilities: dict[str, float]
    statevector: list[complex] | None = None
    shots: int | None = None
    counts: dict[str, int] | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "backend": self.backend,
            "kind": self.kind,
            "probabilities": dict(self.probabilities),
            "notes": list(self.notes),
        }
        if self.statevector is not None:
            payload["statevector"] = [{"re": z.real, "im": z.imag} for z in self.statevector]
        if self.shots is not None:
            payload["shots"] = self.shots
        if self.counts is not None:
            payload["counts"] = dict(self.counts)
        return payload


class LocalStatevectorBackend:
    name = "rqm-local-statevector"

    def __init__(self, config: AdapterConfig | None = None) -> None:
        self.config = config or AdapterConfig()

    def run(self, payload: OpenQSEPayload) -> ExecutionResult:
        circuit = payload.circuit
        n = int(circuit["num_qubits"])
        if n > self.config.max_simulator_qubits:
            raise AdapterError(
                f"Simulator refuses {n} qubits (max {self.config.max_simulator_qubits})."
            )
        state = np.zeros(1 << n, dtype=complex)
        state[0] = 1.0
        for instruction in circuit["instructions"]:
            state = _apply(state, instruction, n)
        probabilities = _bitstring_probs(state, n)
        notes = [
            "Ideal noiseless statevector evolution.",
            "Single-qubit unitaries come from the adapter payload (RQM SU(2) convention when present).",
            "Results are computational-basis probabilities, not hardware counts.",
            "This backend is an RQM prototype helper, not an OpenQSE runtime.",
        ]
        counts = None
        shots = self.config.shots
        if shots:
            rng = np.random.default_rng(self.config.seed)
            labels = list(probabilities)
            weights = np.array([probabilities[label] for label in labels], dtype=float)
            if weights.sum() == 0:
                raise AdapterError("Statevector has zero total probability.")
            weights /= weights.sum()
            sampled = rng.choice(labels, size=shots, p=weights)
            counts = {label: int(np.count_nonzero(sampled == label)) for label in labels if label in sampled}
            notes.append(f"Optional multinomial sampling used shots={shots} with seed={self.config.seed}.")
        return ExecutionResult(
            backend=self.name,
            kind="ideal-statevector-probabilities",
            probabilities=probabilities,
            statevector=list(state),
            shots=shots,
            counts=counts,
            notes=notes,
        )


def _apply(state: np.ndarray, instruction: dict[str, Any], n: int) -> np.ndarray:
    op = instruction["op"]
    if op == "barrier":
        return state
    if op == "measure":
        return state
    qubits = list(instruction.get("qubits", []))
    controls = list(instruction.get("controls", []))
    if op == "unitary":
        matrix = _as_matrix(instruction["unitary"])
        return _apply_1q(state, matrix, qubits[0], n)
    if op in {"x", "y", "z", "h", "s", "t", "i", "rx", "ry", "rz", "u1q"}:
        if instruction.get("unitary") is not None:
            matrix = _as_matrix(instruction["unitary"])
        else:
            matrix = _named_matrix(op, instruction.get("params") or {})
        return _apply_1q(state, matrix, qubits[0], n)
    if op == "cx":
        return _apply_cx(state, controls[0], qubits[0], n)
    if op == "cz":
        return _apply_cz(state, controls[0], qubits[0], n)
    if op == "swap":
        return _apply_swap(state, qubits[0], qubits[1], n)
    raise AdapterError(f"Simulator has no implementation for '{op}'.")


def _named_matrix(op: str, params: dict[str, Any]) -> np.ndarray:
    from ..ir.operations import named_quaternion

    quat = named_quaternion(op, {k: float(v) for k, v in params.items() if v is not None})
    if quat is None:
        raise AdapterError(f"No matrix for operation '{op}'.")
    return np.array(quaternion_to_su2(*quat), dtype=complex)


def _as_matrix(value: Any) -> np.ndarray:
    def cell(item: Any) -> complex:
        if isinstance(item, dict) and "re" in item and "im" in item:
            return complex(item["re"], item["im"])
        return complex(item)

    return np.array([[cell(x) for x in row] for row in value], dtype=complex)


def _apply_1q(state: np.ndarray, matrix: np.ndarray, qubit: int, n: int) -> np.ndarray:
    out = np.zeros_like(state)
    dim = 1 << n
    for index in range(dim):
        bit = (index >> qubit) & 1
        rest = index & ~(1 << qubit)
        amplitude = state[index]
        if amplitude == 0:
            continue
        for row in range(2):
            out[rest | (row << qubit)] += matrix[row, bit] * amplitude
    return out


def _apply_cx(state: np.ndarray, control: int, target: int, n: int) -> np.ndarray:
    out = np.zeros_like(state)
    dim = 1 << n
    for index in range(dim):
        if (index >> control) & 1:
            flipped = index ^ (1 << target)
            out[flipped] += state[index]
        else:
            out[index] += state[index]
    return out


def _apply_cz(state: np.ndarray, control: int, target: int, n: int) -> np.ndarray:
    out = state.copy()
    dim = 1 << n
    for index in range(dim):
        if ((index >> control) & 1) and ((index >> target) & 1):
            out[index] = -state[index]
    return out


def _apply_swap(state: np.ndarray, a: int, b: int, n: int) -> np.ndarray:
    out = np.zeros_like(state)
    dim = 1 << n
    for index in range(dim):
        bit_a = (index >> a) & 1
        bit_b = (index >> b) & 1
        swapped = index
        swapped = (swapped & ~(1 << a)) | (bit_b << a)
        swapped = (swapped & ~(1 << b)) | (bit_a << b)
        out[swapped] += state[index]
    return out


def _bitstring_probs(state: np.ndarray, n: int) -> dict[str, float]:
    probs = np.abs(state) ** 2
    result: dict[str, float] = {}
    for index, prob in enumerate(probs):
        if prob <= 1e-15:
            continue
        bits = "".join("1" if (index >> q) & 1 else "0" for q in range(n - 1, -1, -1))
        result[bits] = float(prob.real)
    return result
