"""RQM OpenQSE Adapter — experimental quaternionic compiler adapter.

RQM owns this implementation. OpenQSE is the architectural/interoperability
context. This package is an experimental prototype, not an official OpenQSE
compiler or standard.
"""

from .api import compile, emit, lower, validate
from .config import AdapterConfig
from .diagnostics import AdapterError, Diagnostics, UnsupportedConstructError, ValidationError
from .frontend.quaternionic_input import QuaternionicProgram
from .ir.model import Module
from .openqse.adapter import OpenQSEAdapter
from .openqse.payload import OpenQSEPayload
from .targets.target import Target, local_simulator_target

__all__ = [
    "AdapterConfig",
    "AdapterError",
    "Diagnostics",
    "Module",
    "OpenQSEAdapter",
    "OpenQSEPayload",
    "QuaternionicProgram",
    "Target",
    "UnsupportedConstructError",
    "ValidationError",
    "compile",
    "emit",
    "local_simulator_target",
    "lower",
    "validate",
]

__version__ = "0.1.1"
