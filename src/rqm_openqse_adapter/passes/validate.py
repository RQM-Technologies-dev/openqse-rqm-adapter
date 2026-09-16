"""Structural validation of quaternionic IR and target assumptions."""

from __future__ import annotations

from ..diagnostics import Diagnostics
from ..ir.model import Module, Operation
from ..ir.operations import get_spec, is_unit_quaternion
from .pipeline import PassContext


class ValidatePass:
    name = "validate"

    def run(self, module: Module, context: PassContext) -> Module:
        diagnostics = context.diagnostics
        if module.num_qubits <= 0:
            diagnostics.add("error", "empty_program", "Program has no qubits.")
        seen_q = set()
        for qubit in module.qubits:
            if qubit.index in seen_q:
                diagnostics.add("error", "duplicate_qubit", f"Duplicate qubit index {qubit.index}.")
            seen_q.add(qubit.index)
        for index, operation in enumerate(module.operations):
            _validate_operation(module, operation, index, diagnostics)
        if context.target is not None:
            context.target.validate_module(module, diagnostics)
        return module


def _validate_operation(module: Module, operation: Operation, index: int, diagnostics: Diagnostics) -> None:
    location = f"operations[{index}] ({operation.name})"
    spec = get_spec(operation.name)
    if spec is None:
        diagnostics.add(
            "error",
            "unknown_operation",
            f"Unknown operation '{operation.name}'.",
            location=location,
        )
        return
    qubit_indices = operation.qubit_indices()
    clbit_indices = operation.clbit_indices()
    known_qubits = module.qubit_index_set()
    known_clbits = module.clbit_index_set()
    for q in qubit_indices:
        if q not in known_qubits:
            diagnostics.add("error", "qubit_out_of_range", f"Qubit {q} is not in the module.", location=location)
    for c in clbit_indices:
        if c not in known_clbits:
            diagnostics.add("error", "clbit_out_of_range", f"Classical bit {c} is not in the module.", location=location)
    if spec.name != "barrier" and spec.qubit_count and not spec.control_count:
        expected = spec.qubit_count
        if spec.name != "measure" and len(operation.target_indices()) != expected:
            diagnostics.add(
                "error",
                "operand_count",
                f"Operation '{spec.name}' expects {expected} target qubit(s).",
                location=location,
            )
    if spec.control_count and len(operation.control_indices()) != spec.control_count:
        diagnostics.add(
            "error",
            "control_count",
            f"Operation '{spec.name}' expects {spec.control_count} control qubit(s).",
            location=location,
        )
    if spec.name in {"cx", "cz", "swap"} and len(set(qubit_indices)) != len(qubit_indices):
        diagnostics.add("error", "duplicate_operands", f"Operation '{spec.name}' cannot reuse the same qubit.", location=location)
    if spec.name == "measure":
        if not operation.target_indices() or not clbit_indices:
            diagnostics.add("error", "measure_operands", "measure requires a qubit and a classical bit.", location=location)
    expected_params = spec.param_names
    param_map = operation.parameter_map()
    unbound = [p.name for p in operation.parameters if not p.bound]
    if unbound:
        diagnostics.add(
            "error",
            "unbound_parameter",
            f"Unbound parameter(s) {unbound}. This prototype requires bound values.",
            location=location,
        )
    if expected_params:
        missing = [name for name in expected_params if name not in param_map]
        if missing:
            diagnostics.add(
                "error",
                "missing_parameters",
                f"Operation '{spec.name}' missing parameter(s) {missing}.",
                location=location,
            )
    if spec.name == "u1q" and set(expected_params).issubset(param_map):
        quat = tuple(param_map[name] for name in expected_params)
        if not is_unit_quaternion(*quat):
            diagnostics.add(
                "error",
                "non_unit_quaternion",
                "u1q requires a unit quaternion (w, x, y, z).",
                location=location,
            )
    # TODO: reject mid-circuit measurement / feed-forward once those constructs exist.
    # TODO: reject classical control flow; this prototype is a straight-line circuit.
