"""Explicit target description consumed by the adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..diagnostics import Diagnostics
from ..ir.model import Module


Connectivity = str | list[tuple[int, int]]


@dataclass
class Target:
    name: str
    architecture: str = "simulator"
    modality: str = "logical-statevector"
    qubit_count: int = 8
    supported_operations: list[str] = field(default_factory=list)
    connectivity: Connectivity = "all-to-all"
    accepted_payload_formats: list[str] = field(
        default_factory=lambda: ["openqse-compatible-circuit/v0.1"]
    )
    constraints: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    version: str = "0.1.0"

    def supports(self, operation: str) -> bool:
        if not self.supported_operations:
            return True
        return operation in self.supported_operations

    def connected(self, a: int, b: int) -> bool:
        if self.connectivity == "all-to-all" or self.connectivity is None:
            return True
        edges = {(min(x, y), max(x, y)) for x, y in self.connectivity}
        return (min(a, b), max(a, b)) in edges

    def validate_module(self, module: Module, diagnostics: Diagnostics) -> None:
        if module.num_qubits > self.qubit_count:
            diagnostics.add(
                "error",
                "target_qubit_capacity",
                f"Program uses {module.num_qubits} qubits; target '{self.name}' provides {self.qubit_count}.",
            )
        for operation in module.operations:
            if operation.name == "barrier":
                continue
            if not self.supports(operation.name):
                diagnostics.add(
                    "error",
                    "unsupported_on_target",
                    f"Target '{self.name}' does not accept operation '{operation.name}'.",
                )
            if operation.name in {"cx", "cz", "swap"}:
                qubits = operation.qubit_indices()
                if len(qubits) >= 2 and not self.connected(qubits[0], qubits[-1]):
                    diagnostics.add(
                        "error",
                        "connectivity",
                        f"Target '{self.name}' has no coupling between qubits {qubits[0]} and {qubits[-1]}.",
                    )
        accepted = set(self.accepted_payload_formats)
        if accepted and "openqse-compatible-circuit/v0.1" not in accepted:
            diagnostics.add(
                "warning",
                "payload_format",
                "Target does not list the prototype OpenQSE-compatible circuit format.",
            )

    def to_dict(self) -> dict[str, Any]:
        connectivity: Any = self.connectivity
        if isinstance(connectivity, list):
            connectivity = [list(edge) for edge in connectivity]
        return {
            "name": self.name,
            "architecture": self.architecture,
            "modality": self.modality,
            "qubit_count": self.qubit_count,
            "supported_operations": list(self.supported_operations),
            "connectivity": connectivity,
            "accepted_payload_formats": list(self.accepted_payload_formats),
            "constraints": dict(self.constraints),
            "metadata": dict(self.metadata),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Target:
        raw_conn = data.get("connectivity", "all-to-all")
        connectivity: Connectivity
        if isinstance(raw_conn, list):
            connectivity = [(int(a), int(b)) for a, b in raw_conn]
        else:
            connectivity = str(raw_conn)
        return cls(
            name=str(data["name"]),
            architecture=str(data.get("architecture", "simulator")),
            modality=str(data.get("modality", "logical-statevector")),
            qubit_count=int(data.get("qubit_count", 0)),
            supported_operations=list(data.get("supported_operations", [])),
            connectivity=connectivity,
            accepted_payload_formats=list(
                data.get("accepted_payload_formats", ["openqse-compatible-circuit/v0.1"])
            ),
            constraints=dict(data.get("constraints", {})),
            metadata=dict(data.get("metadata", {})),
            version=str(data.get("version", "0.1.0")),
        )


DEFAULT_OPS: tuple[str, ...] = (
    "i",
    "x",
    "y",
    "z",
    "h",
    "s",
    "t",
    "rx",
    "ry",
    "rz",
    "u1q",
    "cx",
    "cz",
    "swap",
    "measure",
    "barrier",
)


def local_simulator_target(*, qubit_count: int = 8, name: str = "rqm-local-statevector") -> Target:
    return Target(
        name=name,
        architecture="simulator",
        modality="logical-statevector",
        qubit_count=qubit_count,
        supported_operations=list(DEFAULT_OPS),
        connectivity="all-to-all",
        accepted_payload_formats=["openqse-compatible-circuit/v0.1"],
        constraints={"max_qubits": qubit_count, "noise_model": "none"},
        metadata={"owner": "RQM Technologies", "experimental": True},
        version="0.1.0",
    )
