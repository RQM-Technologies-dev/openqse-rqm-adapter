"""Lowering pass.

Attaches explicit SU(2) matrices for quaternionic single-qubit operations so
the OpenQSE-facing payload can expose standard artifacts instead of quaternion
semantics.
"""

from __future__ import annotations

from ..ir.model import Module, Operation
from ..ir.operations import named_quaternion, quaternion_to_su2
from .pipeline import PassContext


class LowerPass:
    name = "lower"

    def run(self, module: Module, context: PassContext) -> Module:
        operations: list[Operation] = []
        for operation in module.operations:
            lowered = operation.copy()
            quat = lowered.attributes.get("quaternion")
            if quat is None:
                derived = named_quaternion(lowered.name, lowered.parameter_map())
                if derived is not None:
                    w, x, y, z = derived
                    quat = {"w": w, "x": x, "y": y, "z": z}
                    lowered.attributes.set("quaternion", quat)
            if isinstance(quat, dict) and {"w", "x", "y", "z"} <= set(quat):
                matrix = quaternion_to_su2(float(quat["w"]), float(quat["x"]), float(quat["y"]), float(quat["z"]))
                lowered.attributes.set("su2", matrix)
                lowered.attributes.set("lowered", True)
            elif lowered.name in {"cx", "cz", "swap", "measure", "barrier"}:
                lowered.attributes.set("lowered", True)
            else:
                context.diagnostics.add(
                    "error",
                    "cannot_lower",
                    f"No lowering rule for operation '{lowered.name}'.",
                    location=lowered.name,
                )
            operations.append(lowered)
        # TODO: mapping, routing, and native-gate synthesis belong in later RQM passes.
        # TODO: OpenQASM / Qiskit / MLIR emitters should consume this lowered IR.
        result = module.with_operations(operations)
        result.metadata = dict(module.metadata)
        result.metadata["lowered"] = True
        result.metadata["payload_ready"] = True
        return result
