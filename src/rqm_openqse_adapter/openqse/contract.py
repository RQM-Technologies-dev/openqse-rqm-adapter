"""Experimental pass/artifact contract model inspired by openQSE wg-compiler.

This module implements an RQM experiment based on concepts discussed in
openQSE/wg-compiler's Compiler and Optimization Pass Infrastructure document.
It is not an official openQSE schema or standard.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ArtifactContract:
    """Describes one side of a transformation boundary."""

    artifact_type: str
    encoding: str
    encoding_version: str | None = None
    ir_identity: str | None = None
    ir_version: str | None = None
    feature_profiles: tuple[str, ...] = ()
    semantic_guarantees: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PassContract:
    """Machine-readable declaration for a discoverable compiler pass."""

    pass_id: str
    version: str
    name: str
    description: str
    implementation: str
    input: ArtifactContract
    output: ArtifactContract
    capabilities: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    experimental: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def accepts(self, artifact: ArtifactContract) -> bool:
        if self.input.artifact_type != artifact.artifact_type:
            return False
        if self.input.encoding != artifact.encoding:
            return False
        return set(self.input.feature_profiles).issubset(artifact.feature_profiles)


def rqm_quaternionic_compiler_contract() -> PassContract:
    """Return the principal OpenQASM 3 exchange contract for the RQM pass."""

    common_features = ("unitary-gates", "measurement")
    return PassContract(
        pass_id="rqm.quaternionic.compile",
        version="0.2.0",
        name="RQM Quaternionic Compiler Adapter",
        description=(
            "Transform a supported OpenQASM 3 logical circuit through the RQM "
            "quaternionic IR and compiler pipeline, then return OpenQASM 3."
        ),
        implementation="RQM-Technologies-dev/openqse-rqm-adapter",
        input=ArtifactContract(
            artifact_type="LogicalCircuit",
            encoding="OpenQASM3",
            encoding_version="3",
            feature_profiles=common_features,
            semantic_guarantees=("explicit-qubit-addressing",),
        ),
        output=ArtifactContract(
            artifact_type="LogicalCircuit",
            encoding="OpenQASM3",
            encoding_version="3",
            feature_profiles=common_features,
            semantic_guarantees=(
                "quaternionic-semantics-encapsulated",
                "computational-semantics-preserved-for-supported-subset",
            ),
        ),
        capabilities=("validate", "canonicalize", "lower", "emit", "provenance", "openqasm3-exchange"),
        provenance={
            "owner": "RQM Technologies",
            "internal_ir": "RQM-Quaternionic-IR/0.1",
            "inspiration": "openQSE/wg-compiler pass and artifact contract discussion",
            "openqse_status": "experimental-unofficial",
        },
    )
