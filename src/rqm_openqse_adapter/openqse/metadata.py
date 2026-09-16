"""Resource and provenance metadata attached to OpenQSE-compatible artifacts."""

from __future__ import annotations

from typing import Any

from ..ir.model import Module


def resource_metadata(module: Module) -> dict[str, Any]:
    depth = _estimate_depth(module)
    return {
        "qubit_count": module.num_qubits,
        "clbit_count": module.num_clbits,
        "operation_count": len(module.operations),
        "depth_estimate": depth,
        "required_operations": module.required_operations(),
        "has_measurements": any(op.name == "measure" for op in module.operations),
        "has_native_quaternion_ops": any(op.name == "u1q" for op in module.operations),
        "notes": [
            "Resource figures are compiler estimates, not a schedule.",
            "This adapter does not allocate or reserve hardware resources.",
        ],
    }


def _estimate_depth(module: Module) -> int:
    last_use = {q.index: 0 for q in module.qubits}
    depth = 0
    for operation in module.operations:
        if operation.name == "barrier":
            continue
        qubits = operation.qubit_indices()
        layer = 1 + max((last_use.get(q, 0) for q in qubits), default=0)
        for q in qubits:
            last_use[q] = layer
        depth = max(depth, layer)
    return depth
