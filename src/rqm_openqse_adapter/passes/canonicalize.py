"""Canonicalization pass.

Normalizes names, parameter aliases, and attaches documented quaternion forms.
This is not an optimization pass.
"""

from __future__ import annotations

from ..ir.model import Attribute, Module, Operation, Parameter
from ..ir.operations import PARAM_ALIASES, canonicalize_name, get_spec, named_quaternion
from .pipeline import PassContext


class CanonicalizePass:
    name = "canonicalize"

    def run(self, module: Module, context: PassContext) -> Module:
        operations: list[Operation] = []
        for operation in module.operations:
            name = canonicalize_name(operation.name)
            parameters = [
                Parameter(PARAM_ALIASES.get(param.name, param.name), param.value)
                for param in operation.parameters
            ]
            attributes = Attribute(dict(operation.attributes.values))
            spec = get_spec(name)
            if spec and spec.has_quaternion_form and "quaternion" not in attributes.values:
                quat = named_quaternion(name, {p.name: p.value for p in parameters if p.value is not None})
                if quat is not None:
                    w, x, y, z = quat
                    attributes.set("quaternion", {"w": w, "x": x, "y": y, "z": z})
                    attributes.set("quaternion_convention", "rqm-su2-unit-quaternion")
            canonical = Operation(
                name=name,
                operands=list(operation.operands),
                parameters=parameters,
                attributes=attributes,
                source=operation.source,
            )
            if context.config.drop_identity and canonical.name == "i":
                context.diagnostics.add(
                    "info",
                    "dropped_identity",
                    "Dropped identity operation during canonicalization.",
                    location=canonical.source.note if canonical.source else None,
                )
                continue
            operations.append(canonical)
        # TODO: commutation / fusion / quaternion composition passes belong here later.
        result = module.with_operations(operations)
        result.metadata = dict(module.metadata)
        result.metadata["canonicalized"] = True
        return result
