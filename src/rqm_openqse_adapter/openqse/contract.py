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
        """Return whether the declared input boundary accepts an artifact."""
        if self.input.artifact_type != artifact.artifact_type:
            return False
        if self.input.encoding != artifact.encoding:
            return False
        required = set(self.input.feature_profiles)
        available = set(artifact.feature_profiles)
        return required.issubset(available)


def rqm_quaternionic_compiler_contract() -> PassContract:
    """Return the baseline RQM transformation contract.

    The current adapter's native boundary is intentionally declared as an RQM
    experimental encoding. OpenQASM3 exchange is planned separately rather
    than falsely claiming that the present JSON payload is an openQSE standard.
    """

    input_artifact = ArtifactContract(
        artifact_type="LogicalCircuit",
        encoding="RQMQuaternionicProgram",
        encoding_version="0.1",
        ir_identity="RQM-Quaternionic-IR",
        ir_version="0.1",
        feature_profiles=("unitary-gates", "measurement"),
        semantic_guarantees=("explicit-qubit-addressing",),
    )
    output_artifact = ArtifactContract(
        artifact_type="LogicalCircuit",
        encoding="RQMPortableCircuitJSON",
        encoding_version="0.1",
        feature_profiles=("unitary-gates", "measurement", "target-metadata"),
        semantic_guarantees=(
            "quaternionic-semantics-encapsulated",
            "computational-semantics-preserved",
        ),
    )
    return PassContract(
        pass_id="rqm.quaternionic.compile",
        version="0.1.0",
        name="RQM Quaternionic Compiler Adapter",
        description=(
            "Compile an RQM quaternionic logical circuit through validation, "
            "canonicalization, and lowering while exposing a portable artifact "
            "at the interoperability boundary."
        ),
        implementation="RQM-Technologies-dev/openqse-rqm-adapter",
        input=input_artifact,
        output=output_artifact,
        capabilities=("validate", "canonicalize", "lower", "emit", "provenance"),
        provenance={
            "owner": "RQM Technologies",
            "inspiration": "openQSE/wg-compiler pass and artifact contract discussion",
            "openqse_status": "experimental-unofficial",
        },
    )
