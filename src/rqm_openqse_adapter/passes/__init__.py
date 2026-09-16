"""Compiler pass pipeline.

Current passes are intentionally small: validation, canonicalization, and
lowering. Additional RQM compiler passes should implement `CompilerPass` and
be inserted into a `PassManager`.
"""

from .canonicalize import CanonicalizePass
from .lower import LowerPass
from .pipeline import CompilerPass, PassContext, PassManager, default_pipeline
from .validate import ValidatePass

__all__ = [
    "CanonicalizePass",
    "CompilerPass",
    "LowerPass",
    "PassContext",
    "PassManager",
    "ValidatePass",
    "default_pipeline",
]
