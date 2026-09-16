"""Target and resource requirement model.

This is compiler-facing target metadata, not a scheduler or resource allocator.
"""

from .target import Target, local_simulator_target

__all__ = ["Target", "local_simulator_target"]
