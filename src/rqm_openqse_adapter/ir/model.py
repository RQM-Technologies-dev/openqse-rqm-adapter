"""Explicit objects for the prototype quaternionic IR."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Iterable, Literal

from .operations import OPERATION_SPECS, canonicalize_name, get_spec


OperandKind = Literal["qubit", "clbit"]
OperandRole = Literal["target", "control", "measure_qubit", "measure_clbit", "barrier"]


@dataclass(frozen=True)
class SourceLocation:
    file: str | None = None
    line: int | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.file:
            data["file"] = self.file
        if self.line is not None:
            data["line"] = self.line
        if self.note:
            data["note"] = self.note
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SourceLocation | None:
        if not data:
            return None
        return cls(file=data.get("file"), line=data.get("line"), note=data.get("note"))


@dataclass(frozen=True)
class Qubit:
    index: int
    name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"index": self.index}
        if self.name:
            payload["name"] = self.name
        return payload


@dataclass(frozen=True)
class Parameter:
    name: str
    value: float | None = None

    @property
    def bound(self) -> bool:
        return self.value is not None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": self.name}
        if self.value is not None:
            payload["value"] = self.value
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Parameter:
        return cls(name=str(data["name"]), value=data.get("value"))


@dataclass
class Attribute:
    """Free-form IR attribute. Quaternion and SU(2) data live here when present."""

    values: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.values[key] = value

    def without(self, *keys: str) -> Attribute:
        values = {k: v for k, v in self.values.items() if k not in keys}
        return Attribute(values)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.values)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Attribute:
        return cls(dict(data or {}))


@dataclass(frozen=True)
class Operand:
    kind: OperandKind
    index: int
    role: OperandRole = "target"

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "index": self.index, "role": self.role}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Operand:
        return cls(kind=data["kind"], index=int(data["index"]), role=data.get("role", "target"))


@dataclass
class Operation:
    name: str
    operands: list[Operand] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    attributes: Attribute = field(default_factory=Attribute)
    source: SourceLocation | None = None

    def __post_init__(self) -> None:
        self.name = canonicalize_name(self.name)

    @property
    def spec(self):
        return get_spec(self.name)

    def parameter_map(self) -> dict[str, float]:
        return {item.name: float(item.value) for item in self.parameters if item.value is not None}

    def qubit_indices(self) -> list[int]:
        return [op.index for op in self.operands if op.kind == "qubit"]

    def clbit_indices(self) -> list[int]:
        return [op.index for op in self.operands if op.kind == "clbit"]

    def control_indices(self) -> list[int]:
        return [op.index for op in self.operands if op.kind == "qubit" and op.role == "control"]

    def target_indices(self) -> list[int]:
        return [op.index for op in self.operands if op.kind == "qubit" and op.role in {"target", "measure_qubit"}]

    def copy(self, **changes: Any) -> Operation:
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "operands": [op.to_dict() for op in self.operands],
            "parameters": [param.to_dict() for param in self.parameters],
            "attributes": self.attributes.to_dict(),
        }
        if self.source:
            payload["source"] = self.source.to_dict()
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Operation:
        return cls(
            name=str(data["name"]),
            operands=[Operand.from_dict(item) for item in data.get("operands", [])],
            parameters=[Parameter.from_dict(item) for item in data.get("parameters", [])],
            attributes=Attribute.from_dict(data.get("attributes")),
            source=SourceLocation.from_dict(data.get("source")),
        )


@dataclass
class Measurement:
    qubit: int
    clbit: int
    source: SourceLocation | None = None

    def to_operation(self) -> Operation:
        return Operation(
            name="measure",
            operands=[
                Operand("qubit", self.qubit, "measure_qubit"),
                Operand("clbit", self.clbit, "measure_clbit"),
            ],
            source=self.source,
        )


@dataclass
class TargetRequirements:
    min_qubits: int = 0
    min_clbits: int = 0
    required_operations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_qubits": self.min_qubits,
            "min_clbits": self.min_clbits,
            "required_operations": list(self.required_operations),
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> TargetRequirements:
        data = data or {}
        return cls(
            min_qubits=int(data.get("min_qubits", 0)),
            min_clbits=int(data.get("min_clbits", 0)),
            required_operations=list(data.get("required_operations", [])),
            notes=list(data.get("notes", [])),
        )


@dataclass
class Module:
    """Adapter-facing quaternionic IR module."""

    name: str = "unnamed"
    qubits: list[Qubit] = field(default_factory=list)
    clbits: list[Qubit] = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    target_requirements: TargetRequirements = field(default_factory=TargetRequirements)
    source: SourceLocation | None = None

    @property
    def num_qubits(self) -> int:
        return len(self.qubits)

    @property
    def num_clbits(self) -> int:
        return len(self.clbits)

    def qubit_index_set(self) -> set[int]:
        return {q.index for q in self.qubits}

    def clbit_index_set(self) -> set[int]:
        return {q.index for q in self.clbits}

    def required_operations(self) -> list[str]:
        names = []
        seen: set[str] = set()
        for op in self.operations:
            if op.name not in seen and op.name in OPERATION_SPECS:
                seen.add(op.name)
                names.append(op.name)
        return names

    def with_operations(self, operations: Iterable[Operation]) -> Module:
        clone = replace(self, operations=list(operations), metadata=dict(self.metadata))
        clone.refresh_target_requirements()
        return clone

    def refresh_target_requirements(self) -> None:
        self.target_requirements = TargetRequirements(
            min_qubits=self.num_qubits,
            min_clbits=self.num_clbits,
            required_operations=self.required_operations(),
            notes=list(self.target_requirements.notes),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "qubits": [q.to_dict() for q in self.qubits],
            "clbits": [q.to_dict() for q in self.clbits],
            "operations": [op.to_dict() for op in self.operations],
            "parameters": [param.to_dict() for param in self.parameters],
            "metadata": dict(self.metadata),
            "target_requirements": self.target_requirements.to_dict(),
        }
        if self.source:
            payload["source"] = self.source.to_dict()
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Module:
        module = cls(
            name=str(data.get("name", "unnamed")),
            qubits=[Qubit(index=int(item["index"]), name=item.get("name")) for item in data.get("qubits", [])],
            clbits=[Qubit(index=int(item["index"]), name=item.get("name")) for item in data.get("clbits", [])],
            operations=[Operation.from_dict(item) for item in data.get("operations", [])],
            parameters=[Parameter.from_dict(item) for item in data.get("parameters", [])],
            metadata=dict(data.get("metadata", {})),
            target_requirements=TargetRequirements.from_dict(data.get("target_requirements")),
            source=SourceLocation.from_dict(data.get("source")),
        )
        if not module.qubits and "num_qubits" in data:
            n = int(data["num_qubits"])
            module.qubits = [Qubit(i, f"q{i}") for i in range(n)]
        if not module.clbits and "num_clbits" in data:
            n = int(data["num_clbits"])
            module.clbits = [Qubit(i, f"c{i}") for i in range(n)]
        module.refresh_target_requirements()
        return module
