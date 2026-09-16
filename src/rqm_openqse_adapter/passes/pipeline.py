"""Pass manager and shared pass context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..config import AdapterConfig
from ..diagnostics import Diagnostics
from ..ir.model import Module
from ..targets.target import Target


@dataclass
class PassContext:
    target: Target | None
    diagnostics: Diagnostics = field(default_factory=Diagnostics)
    config: AdapterConfig = field(default_factory=AdapterConfig)
    applied: list[str] = field(default_factory=list)


class CompilerPass(Protocol):
    name: str

    def run(self, module: Module, context: PassContext) -> Module:
        ...


class PassManager:
    def __init__(self, passes: list[CompilerPass] | None = None) -> None:
        self.passes = list(passes) if passes is not None else default_pipeline()

    def run(self, module: Module, context: PassContext | None = None) -> Module:
        ctx = context or PassContext(target=None)
        current = module
        for compiler_pass in self.passes:
            current = compiler_pass.run(current, ctx)
            ctx.applied.append(compiler_pass.name)
            ctx.diagnostics.raise_if_errors()
        return current


def default_pipeline() -> list[CompilerPass]:
    from .canonicalize import CanonicalizePass
    from .lower import LowerPass
    from .validate import ValidatePass

    return [ValidatePass(), CanonicalizePass(), LowerPass()]
