"""Quaternionic intermediate representation used inside the adapter."""

from .model import (
    Attribute,
    Measurement,
    Module,
    Operand,
    Operation,
    Parameter,
    Qubit,
    SourceLocation,
    TargetRequirements,
)
from .serialization import dumps, loads, module_from_dict, module_to_dict

__all__ = [
    "Attribute",
    "Measurement",
    "Module",
    "Operand",
    "Operation",
    "Parameter",
    "Qubit",
    "SourceLocation",
    "TargetRequirements",
    "dumps",
    "loads",
    "module_from_dict",
    "module_to_dict",
]
