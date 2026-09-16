"""OpenQSE-compatible payload produced by the adapter.

The payload is an experimental RQM artifact. It is OpenQSE-compatible in the
sense that it exposes standard named operations, explicit unitaries, resource
metadata, and diagnostics — not quaternionic mathematics.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ..config import ADAPTER_NAME, ADAPTER_VERSION, PAYLOAD_SCHEMA
from ..diagnostics import Diagnostics
from ..ir.serialization import _complex_to_json


@dataclass
class OpenQSEPayload:
    circuit: dict[str, Any]
    target: dict[str, Any]
    resources: dict[str, Any]
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    schema: str = PAYLOAD_SCHEMA
    format: str = "openqse-compatible-circuit/v0.1"
    status: str = "experimental"

    def to_dict(self) -> dict[str, Any]:
        return _complex_to_json(
            {
                "schema": self.schema,
                "format": self.format,
                "status": self.status,
                "disclaimer": (
                    "Experimental RQM adapter artifact. Not an official OpenQSE "
                    "standard, reference implementation, or endorsed schema."
                ),
                "circuit": self.circuit,
                "target": self.target,
                "resources": self.resources,
                "diagnostics": list(self.diagnostics),
                "provenance": dict(self.provenance) or default_provenance(),
                "metadata": dict(self.metadata),
            }
        )

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OpenQSEPayload:
        return cls(
            circuit=dict(data.get("circuit", {})),
            target=dict(data.get("target", {})),
            resources=dict(data.get("resources", {})),
            diagnostics=list(data.get("diagnostics", [])),
            provenance=dict(data.get("provenance", {})),
            metadata=dict(data.get("metadata", {})),
            schema=str(data.get("schema", PAYLOAD_SCHEMA)),
            format=str(data.get("format", "openqse-compatible-circuit/v0.1")),
            status=str(data.get("status", "experimental")),
        )


def default_provenance(*, pipeline: list[str] | None = None) -> dict[str, Any]:
    return {
        "adapter": ADAPTER_NAME,
        "version": ADAPTER_VERSION,
        "owner": "RQM Technologies",
        "role": "experimental-reference-adapter",
        "pipeline": list(pipeline or ["validate", "canonicalize", "lower"]),
        "openqse_status": "integration-prototype",
    }


def empty_diagnostics() -> Diagnostics:
    return Diagnostics()
