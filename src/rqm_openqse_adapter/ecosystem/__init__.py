"""Cross-repository RQM ecosystem interoperability.

This package does not reimplement quaternion mathematics, compiler passes, or
OpenQASM parsing. It converts and sequences the real sibling packages.
"""

from .pipeline import CleanDemonstrationReport, run_clean_demonstration

__all__ = ["CleanDemonstrationReport", "run_clean_demonstration"]
