"""Small, dependency-free OpenQASM 3 exchange boundary.

This intentionally supports the adapter's current logical-circuit subset rather
than claiming complete OpenQASM 3 coverage. Unsupported syntax fails clearly.
"""

from __future__ import annotations

import math
import re
from typing import Any

from .diagnostics import UnsupportedConstructError
from .frontend.quaternionic_input import QuaternionicProgram, program_to_module
from .ir.model import Module, Operation

_HEADER = re.compile(r"^OPENQASM\s+3(?:\.0)?\s*;$", re.I)
_QREG = re.compile(r"^qubit\[(\d+)\]\s+(\w+)\s*;$", re.I)
_CREG = re.compile(r"^bit\[(\d+)\]\s+(\w+)\s*;$", re.I)
_MEASURE = re.compile(r"^(\w+)\[(\d+)\]\s*=\s*measure\s+(\w+)\[(\d+)\]\s*;$", re.I)
_GATE = re.compile(r"^(\w+)(?:\(([^)]*)\))?\s+(.+)\s*;$")
_REF = re.compile(r"^(\w+)\[(\d+)\]$")
_SUPPORTED = {"i", "x", "y", "z", "h", "s", "t", "rx", "ry", "rz", "cx", "cz", "swap", "barrier"}


def _strip(source: str) -> list[str]:
    lines: list[str] = []
    for raw in source.splitlines():
        line = raw.split("//", 1)[0].strip()
        if line:
            lines.append(line)
    return lines


def _angle(expr: str) -> float:
    """Evaluate the small numeric/pi expression subset used by this prototype."""
    expr = expr.strip().replace("π", "pi")
    if not re.fullmatch(r"[0-9eE+\-*/(). pi]+", expr):
        raise UnsupportedConstructError(f"Unsupported OpenQASM angle expression: {expr!r}")
    try:
        return float(eval(expr, {"__builtins__": {}}, {"pi": math.pi}))
    except Exception as exc:
        raise UnsupportedConstructError(f"Invalid OpenQASM angle expression: {expr!r}") from exc


def _ref(token: str, expected: str) -> int:
    match = _REF.match(token.strip())
    if not match or match.group(1) != expected:
        raise UnsupportedConstructError(f"Expected {expected}[index], got {token!r}")
    return int(match.group(2))


def loads_openqasm3(source: str, *, name: str = "openqasm3") -> QuaternionicProgram:
    """Parse the supported OpenQASM 3 subset into an RQM program."""
    lines = _strip(source)
    if not lines or not _HEADER.match(lines[0]):
        raise UnsupportedConstructError("OpenQASM 3 input must begin with 'OPENQASM 3;'.")

    program = QuaternionicProgram(name=name)
    qname = "q"
    cname = "c"
    for line in lines[1:]:
        if line.lower() == 'include "stdgates.inc";':
            continue
        match = _QREG.match(line)
        if match:
            program.num_qubits = int(match.group(1))
            qname = match.group(2)
            continue
        match = _CREG.match(line)
        if match:
            program.num_clbits = int(match.group(1))
            cname = match.group(2)
            continue
        match = _MEASURE.match(line)
        if match:
            if match.group(1) != cname or match.group(3) != qname:
                raise UnsupportedConstructError(f"Unsupported register reference in {line!r}")
            program.measure(int(match.group(4)), int(match.group(2)))
            continue
        match = _GATE.match(line)
        if not match:
            raise UnsupportedConstructError(f"Unsupported OpenQASM 3 statement: {line!r}")
        gate = match.group(1).lower()
        if gate not in _SUPPORTED:
            raise UnsupportedConstructError(f"Unsupported OpenQASM 3 gate: {gate!r}")
        params = [] if match.group(2) is None else [_angle(x) for x in match.group(2).split(",")]
        refs = [item.strip() for item in match.group(3).split(",")]
        qubits = [_ref(item, qname) for item in refs]
        if gate in {"cx", "cz"}:
            if len(qubits) != 2:
                raise UnsupportedConstructError(f"{gate} requires two qubits")
            program.op(gate, qubits[1], controls=qubits[0], params=params)
        else:
            program.op(gate, qubits, params=params)
    program.metadata["exchange_input"] = "OpenQASM3"
    return program


def _format_number(value: Any) -> str:
    if value is None:
        raise UnsupportedConstructError("Symbolic/unbound parameters are not yet supported by the OpenQASM emitter.")
    return format(float(value), ".17g")


def dumps_openqasm3(program: QuaternionicProgram | Module | dict[str, Any]) -> str:
    """Emit the supported RQM logical-circuit subset as OpenQASM 3."""
    module = program_to_module(program)
    lines = ["OPENQASM 3;", 'include "stdgates.inc";', f"qubit[{module.num_qubits}] q;"]
    if module.num_clbits:
        lines.append(f"bit[{module.num_clbits}] c;")
    for op in module.operations:
        lines.append(_emit_operation(op))
    return "\n".join(lines) + "\n"


def _emit_operation(op: Operation) -> str:
    name = op.name.lower()
    if name == "u1q":
        raise UnsupportedConstructError(
            "Native u1q has no direct stdgates.inc spelling; lower it before OpenQASM 3 exchange."
        )
    if name == "measure":
        qs, cs = op.target_indices() or op.qubit_indices(), op.clbit_indices()
        if len(qs) != len(cs):
            raise UnsupportedConstructError("Measurement qubit/classical operands do not match.")
        return "\n".join(f"c[{c}] = measure q[{q}];" for q, c in zip(qs, cs))
    if name not in _SUPPORTED:
        raise UnsupportedConstructError(f"No OpenQASM 3 exchange spelling for {name!r}")
    qubits = op.qubit_indices() if name in {"swap", "barrier"} else op.control_indices() + op.target_indices()
    args = ", ".join(f"q[{q}]" for q in qubits)
    if op.parameters:
        values = ", ".join(_format_number(p.value) for p in op.parameters)
        return f"{name}({values}) {args};"
    return f"{name} {args};"
