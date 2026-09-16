"""Adapter configuration for the experimental RQM OpenQSE pipeline."""

from __future__ import annotations

from dataclasses import dataclass


IR_SCHEMA = "rqm-quaternionic-ir/v0.1"
PAYLOAD_SCHEMA = "rqm-openqse-payload/v0.1"
ADAPTER_NAME = "rqm-openqse-adapter"
ADAPTER_VERSION = "0.1.0"


@dataclass(frozen=True)
class AdapterConfig:
    """Tunable prototype behavior. These are implementation knobs, not OpenQSE rules."""

    drop_identity: bool = True
    include_unitaries_in_payload: bool = True
    execute_by_default: bool = False
    max_simulator_qubits: int = 8
    shots: int | None = None
    seed: int | None = 7
    experimental: bool = True
