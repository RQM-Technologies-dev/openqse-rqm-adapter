"""Thin conversions between rqm-circuits and rqm-compiler.

Gate semantics stay in the sibling packages. This module only maps fields.
"""

from __future__ import annotations

from typing import Any

from ..diagnostics import AdapterError


def compiler_to_circuits(circuit: Any) -> Any:
    from rqm_circuits import Circuit as CircuitsCircuit
    from rqm_circuits import Parameter, make_instruction, validate_public_circuit

    out = CircuitsCircuit(
        num_qubits=circuit.num_qubits,
        name=str(circuit.metadata.get("name", "compiler-import")),
        metadata=dict(circuit.metadata),
    )
    for operation in circuit.operations:
        out.add(_compiler_op_to_instruction(operation, make_instruction, Parameter))
    validate_public_circuit(out)
    return out


def circuits_to_compiler(circuit: Any) -> Any:
    from rqm_compiler import Circuit as CompilerCircuit
    from rqm_compiler.ops import Operation

    out = CompilerCircuit(circuit.num_qubits, metadata=dict(circuit.metadata or {}))
    if getattr(circuit, "name", ""):
        out.metadata.setdefault("name", circuit.name)
    for instruction in circuit.instructions:
        out.add(_circuits_instruction_to_operation(instruction, Operation))
    return out


def _compiler_op_to_instruction(operation: Any, make_instruction: Any, Parameter: Any) -> Any:
    name = operation.gate
    params = [
        Parameter(str(key), value=float(value) if isinstance(value, (int, float)) else value)
        for key, value in dict(operation.params or {}).items()
        if key != "block"
    ]
    if name == "u1q":
        ordered = []
        raw = dict(operation.params or {})
        for key in ("w", "x", "y", "z"):
            if key not in raw:
                raise AdapterError(f"compiler u1q is missing quaternion component {key!r}.")
            ordered.append(Parameter(key, value=float(raw[key])))
        return make_instruction(name, list(operation.targets), params=ordered)
    if name in {"cx", "cy", "cz"}:
        return make_instruction(
            name,
            list(operation.targets),
            controls=list(operation.controls),
            params=params or None,
        )
    if name == "measure":
        clbit = int(operation.params.get("key", f"m{operation.targets[0]}").replace("m", "") or 0)
        return make_instruction(name, list(operation.targets), clbits=[clbit])
    return make_instruction(name, list(operation.targets), params=params or None)


def _circuits_instruction_to_operation(instruction: Any, Operation: Any) -> Any:
    name = instruction.gate.name
    targets = [ref.index for ref in instruction.targets]
    controls = [ref.index for ref in instruction.controls]
    params: dict[str, Any] = {}
    for parameter in instruction.params:
        if parameter.value is None:
            raise AdapterError(f"Unbound rqm-circuits parameter {parameter.name!r}.")
        params[parameter.name] = parameter.value
    return Operation(gate=name, targets=targets, controls=controls, params=params)
