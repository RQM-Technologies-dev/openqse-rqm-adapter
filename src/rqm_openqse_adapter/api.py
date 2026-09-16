"""Small public API for the RQM OpenQSE adapter."""

from __future__ import annotations

from .config import AdapterConfig
from .diagnostics import Diagnostics
from .frontend.quaternionic_input import QuaternionicProgram
from .ir.model import Module
from .openqse.adapter import CompilationResult, OpenQSEAdapter, ProgramLike
from .openqse.payload import OpenQSEPayload
from .targets.target import Target, local_simulator_target


def _adapter(target: Target | None = None, config: AdapterConfig | None = None) -> OpenQSEAdapter:
    return OpenQSEAdapter(target=target or local_simulator_target(), config=config)


def validate(program: ProgramLike, target: Target | None = None, config: AdapterConfig | None = None) -> Diagnostics:
    return _adapter(target, config).validate(program)


def lower(program: ProgramLike, target: Target | None = None, config: AdapterConfig | None = None) -> Module:
    return _adapter(target, config).lower(program)


def emit(program: ProgramLike, target: Target | None = None, config: AdapterConfig | None = None) -> OpenQSEPayload:
    return _adapter(target, config).emit(program)


def compile(
    program: ProgramLike,
    target: Target | None = None,
    config: AdapterConfig | None = None,
    *,
    execute: bool = False,
) -> CompilationResult:
    """Compile a quaternionic program through the adapter pipeline.

    If ``execute`` is true, the local statevector backend runs the emitted
    payload. This shadows the Python builtin name intentionally to match the
    adapter's public contract; use ``rqm_openqse_adapter.compile``.
    """

    return _adapter(target, config).compile(program, execute=execute)


__all__ = [
    "CompilationResult",
    "OpenQSEAdapter",
    "OpenQSEPayload",
    "ProgramLike",
    "QuaternionicProgram",
    "compile",
    "emit",
    "lower",
    "validate",
]
