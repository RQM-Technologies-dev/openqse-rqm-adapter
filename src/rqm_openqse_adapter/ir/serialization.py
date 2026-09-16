"""JSON serialization for the quaternionic IR.

JSON is the debugging and example format for this prototype. It is not an
OpenQSE standard schema.
"""

from __future__ import annotations

import json
from typing import Any

from ..config import IR_SCHEMA
from .model import Module


def _complex_to_json(value: Any) -> Any:
    if isinstance(value, complex):
        return {"re": value.real, "im": value.imag}
    if isinstance(value, list):
        return [_complex_to_json(item) for item in value]
    if isinstance(value, tuple):
        return [_complex_to_json(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _complex_to_json(v) for k, v in value.items()}
    return value


def _complex_from_json(value: Any) -> Any:
    if isinstance(value, dict) and set(value.keys()) == {"re", "im"}:
        return complex(float(value["re"]), float(value["im"]))
    if isinstance(value, list):
        return [_complex_from_json(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _complex_from_json(v) for k, v in value.items()}
    return value


def module_to_dict(module: Module) -> dict[str, Any]:
    return {
        "schema": IR_SCHEMA,
        "status": "experimental",
        "module": _complex_to_json(module.to_dict()),
    }


def module_from_dict(data: dict[str, Any]) -> Module:
    if "module" in data:
        body = data["module"]
    else:
        body = data
    return Module.from_dict(_complex_from_json(body))


def dumps(module: Module, *, indent: int = 2) -> str:
    return json.dumps(module_to_dict(module), indent=indent, sort_keys=True)


def loads(text: str) -> Module:
    return module_from_dict(json.loads(text))
