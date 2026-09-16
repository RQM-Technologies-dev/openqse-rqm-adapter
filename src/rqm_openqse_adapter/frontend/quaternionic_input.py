"""Minimal quaternionic program input.

This frontend is a convenience builder and JSON ingest path. It does not claim
a complete quaternionic programming language. Supported operations are the
named single-qubit gates with documented quaternion forms, the native `u1q`
gate, and ordinary two-qubit / measurement operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from ..ir.model import (
    Attribute,
    Module,
    Operand,
    Operation,
    Parameter,
    Qubit,
    SourceLocation,
    TargetRequirements,
)
from ..ir.operations import PARAM_ALIASES, canonicalize_name, get_spec


def _qubits(count: int, prefix: str) -> list[Qubit]:
    return [Qubit(index=i, name=f"{prefix}{i}") for i in range(count)]


def _as_params(spec_name: str, raw: Sequence[Any] | MappingLike | None) -> list[Parameter]:
    spec = get_spec(spec_name)
    expected = list(spec.param_names) if spec else []
    if raw is None:
        return []
    if isinstance(raw, dict):
        params = []
        for name, value in raw.items():
            canon = PARAM_ALIASES.get(str(name), str(name))
            params.append(Parameter(canon, None if value is None else float(value)))
        return params
    values = list(raw)
    if expected and len(values) != len(expected):
        # Leave the mismatch for validation; still record positional values.
        expected = [f"p{i}" for i in range(len(values))] or expected
    names = expected or [f"p{i}" for i in range(len(values))]
    return [Parameter(names[i], None if values[i] is None else float(values[i])) for i in range(len(values))]


MappingLike = dict[str, Any]


@dataclass
class QuaternionicProgram:
    """Builder for a small quaternionic quantum program."""

    name: str = "unnamed"
    num_qubits: int = 0
    num_clbits: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    source_file: str | None = None
    _operations: list[Operation] = field(default_factory=list, repr=False)

    def op(
        self,
        name: str,
        qubits: Sequence[int] | int,
        *,
        controls: Sequence[int] | int | None = None,
        clbits: Sequence[int] | int | None = None,
        params: Sequence[Any] | MappingLike | None = None,
        attributes: dict[str, Any] | None = None,
        source: SourceLocation | None = None,
    ) -> QuaternionicProgram:
        spec_name = canonicalize_name(name)
        qubit_list = _as_index_list(qubits)
        control_list = _as_index_list(controls)
        clbit_list = _as_index_list(clbits)
        operands: list[Operand] = []
        if spec_name == "measure":
            if not clbit_list and qubit_list:
                clbit_list = list(qubit_list)
                self.num_clbits = max(self.num_clbits, max(clbit_list) + 1 if clbit_list else 0)
            for q, c in zip(qubit_list, clbit_list):
                operands.extend(
                    [
                        Operand("qubit", q, "measure_qubit"),
                        Operand("clbit", c, "measure_clbit"),
                    ]
                )
        elif spec_name in {"cx", "cz"}:
            if not control_list and len(qubit_list) == 2:
                control_list = [qubit_list[0]]
                qubit_list = [qubit_list[1]]
            operands.extend(Operand("qubit", idx, "control") for idx in control_list)
            operands.extend(Operand("qubit", idx, "target") for idx in qubit_list)
        elif spec_name == "barrier":
            operands.extend(Operand("qubit", idx, "barrier") for idx in qubit_list)
        else:
            operands.extend(Operand("qubit", idx, "control") for idx in control_list)
            operands.extend(Operand("qubit", idx, "target") for idx in qubit_list)
        operation = Operation(
            name=spec_name,
            operands=operands,
            parameters=_as_params(spec_name, params),
            attributes=Attribute(dict(attributes or {})),
            source=source,
        )
        self._operations.append(operation)
        used_qubits = operation.qubit_indices()
        if used_qubits:
            self.num_qubits = max(self.num_qubits, max(used_qubits) + 1)
        used_clbits = operation.clbit_indices()
        if used_clbits:
            self.num_clbits = max(self.num_clbits, max(used_clbits) + 1)
        return self

    def i(self, qubit: int) -> QuaternionicProgram:
        return self.op("i", qubit)

    def x(self, qubit: int) -> QuaternionicProgram:
        return self.op("x", qubit)

    def y(self, qubit: int) -> QuaternionicProgram:
        return self.op("y", qubit)

    def z(self, qubit: int) -> QuaternionicProgram:
        return self.op("z", qubit)

    def h(self, qubit: int) -> QuaternionicProgram:
        return self.op("h", qubit)

    def s(self, qubit: int) -> QuaternionicProgram:
        return self.op("s", qubit)

    def t(self, qubit: int) -> QuaternionicProgram:
        return self.op("t", qubit)

    def rx(self, qubit: int, angle: float) -> QuaternionicProgram:
        return self.op("rx", qubit, params={"angle": angle})

    def ry(self, qubit: int, angle: float) -> QuaternionicProgram:
        return self.op("ry", qubit, params={"angle": angle})

    def rz(self, qubit: int, angle: float) -> QuaternionicProgram:
        return self.op("rz", qubit, params={"angle": angle})

    def u1q(self, qubit: int, w: float, x: float, y: float, z: float) -> QuaternionicProgram:
        return self.op("u1q", qubit, params={"w": w, "x": x, "y": y, "z": z})

    def cx(self, control: int, target: int) -> QuaternionicProgram:
        return self.op("cx", target, controls=control)

    def cz(self, control: int, target: int) -> QuaternionicProgram:
        return self.op("cz", target, controls=control)

    def swap(self, q0: int, q1: int) -> QuaternionicProgram:
        return self.op("swap", [q0, q1])

    def measure(self, qubit: int, clbit: int | None = None) -> QuaternionicProgram:
        if clbit is None:
            clbit = qubit
        return self.op("measure", qubit, clbits=clbit)

    def measure_all(self) -> QuaternionicProgram:
        self.num_clbits = max(self.num_clbits, self.num_qubits)
        for i in range(self.num_qubits):
            self.measure(i, i)
        return self

    def to_module(self) -> Module:
        module = Module(
            name=self.name,
            qubits=_qubits(self.num_qubits, "q"),
            clbits=_qubits(self.num_clbits, "c"),
            operations=list(self._operations),
            metadata=dict(self.metadata),
            source=SourceLocation(file=self.source_file) if self.source_file else None,
        )
        module.refresh_target_requirements()
        return module


def _as_index_list(value: Sequence[int] | int | None) -> list[int]:
    if value is None:
        return []
    if isinstance(value, int):
        return [value]
    return [int(item) for item in value]


def program_to_module(program: QuaternionicProgram | Module | dict[str, Any]) -> Module:
    if isinstance(program, Module):
        return program
    if isinstance(program, QuaternionicProgram):
        return program.to_module()
    return program_from_dict(program).to_module()


def program_from_dict(data: dict[str, Any]) -> QuaternionicProgram:
    body = data.get("program", data)
    program = QuaternionicProgram(
        name=str(body.get("name", "unnamed")),
        num_qubits=int(body.get("num_qubits", body.get("qubits", 0) if isinstance(body.get("qubits"), int) else 0)),
        num_clbits=int(body.get("num_clbits", 0)),
        metadata=dict(body.get("metadata", {})),
        source_file=body.get("source_file"),
    )
    if isinstance(body.get("qubits"), list):
        program.num_qubits = max(program.num_qubits, len(body["qubits"]))
    if isinstance(body.get("clbits"), list):
        program.num_clbits = max(program.num_clbits, len(body["clbits"]))
    for item in body.get("operations", body.get("ops", [])):
        name = item.get("op", item.get("name"))
        qubits = item.get("qubits", item.get("targets", item.get("qubit")))
        program.op(
            name,
            qubits if qubits is not None else [],
            controls=item.get("controls", item.get("control")),
            clbits=item.get("clbits", item.get("clbit")),
            params=item.get("params", item.get("parameters")),
            attributes=item.get("attributes"),
        )
    return program
