"""Central OpenQSE adapter interface.

The adapter accepts RQM quaternionic IR, applies the compiler pipeline, and
emits an OpenQSE-compatible payload plus metadata. Quaternionic semantics stay
on the RQM side of this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..backends.simulator import ExecutionResult, LocalStatevectorBackend
from ..config import AdapterConfig
from ..diagnostics import Diagnostics, UnsupportedConstructError
from ..frontend.quaternionic_input import QuaternionicProgram, program_to_module
from ..ir.model import Module, Operation
from ..ir.serialization import dumps as dumps_ir
from ..passes.pipeline import PassContext, PassManager
from ..targets.target import Target, local_simulator_target
from .metadata import resource_metadata
from .payload import OpenQSEPayload, default_provenance


ProgramLike = QuaternionicProgram | Module | dict[str, Any]


@dataclass
class CompilationResult:
    module: Module
    payload: OpenQSEPayload
    diagnostics: Diagnostics
    ir_json: str
    execution: ExecutionResult | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "module": self.module.to_dict(),
            "payload": self.payload.to_dict(),
            "diagnostics": self.diagnostics.to_list(),
        }
        if self.execution is not None:
            data["execution"] = self.execution.to_dict()
        return data


class OpenQSEAdapter:
    def __init__(
        self,
        target: Target | None = None,
        config: AdapterConfig | None = None,
        backend: LocalStatevectorBackend | None = None,
        passes: PassManager | None = None,
    ) -> None:
        self.config = config or AdapterConfig()
        self.target = target or local_simulator_target(qubit_count=self.config.max_simulator_qubits)
        self.backend = backend or LocalStatevectorBackend(config=self.config)
        self.pass_manager = passes or PassManager()

    def validate(self, program: ProgramLike) -> Diagnostics:
        module = program_to_module(program)
        context = PassContext(target=self.target, config=self.config)
        from ..passes.validate import ValidatePass

        ValidatePass().run(module, context)
        return context.diagnostics

    def lower(self, program: ProgramLike) -> Module:
        module = program_to_module(program)
        context = PassContext(target=self.target, config=self.config)
        lowered = self.pass_manager.run(module, context)
        return lowered

    def emit(self, program: ProgramLike) -> OpenQSEPayload:
        context = PassContext(target=self.target, config=self.config)
        module = self.pass_manager.run(program_to_module(program), context)
        return self._payload_from_module(module, context)

    def compile(self, program: ProgramLike, *, execute: bool | None = None) -> CompilationResult:
        context = PassContext(target=self.target, config=self.config)
        module = self.pass_manager.run(program_to_module(program), context)
        payload = self._payload_from_module(module, context)
        execution = None
        should_execute = self.config.execute_by_default if execute is None else execute
        if should_execute:
            execution = self.backend.run(payload)
        return CompilationResult(
            module=module,
            payload=payload,
            diagnostics=context.diagnostics,
            ir_json=dumps_ir(module),
            execution=execution,
        )

    def _payload_from_module(self, module: Module, context: PassContext) -> OpenQSEPayload:
        instructions = [_instruction_from_operation(op, self.config) for op in module.operations]
        resources = resource_metadata(module)
        resources["required_operations"] = [
            "unitary" if name == "u1q" else name for name in resources["required_operations"]
        ]
        circuit = {
            "name": module.name,
            "num_qubits": module.num_qubits,
            "num_clbits": module.num_clbits,
            "instructions": instructions,
            "metadata": {
                key: value
                for key, value in module.metadata.items()
                if key in {"canonicalized", "lowered", "payload_ready"}
            },
        }
        return OpenQSEPayload(
            circuit=circuit,
            target=self.target.to_dict(),
            resources=resources,
            diagnostics=context.diagnostics.to_list(),
            provenance=default_provenance(pipeline=list(context.applied)),
            metadata={
                "experimental": True,
                "owner": "RQM Technologies",
                "quaternionic_semantics": "encapsulated-in-adapter",
                "source_module": module.name,
            },
        )


def _instruction_from_operation(operation: Operation, config: AdapterConfig) -> dict[str, Any]:
    if operation.name not in {
        "i",
        "x",
        "y",
        "z",
        "h",
        "s",
        "t",
        "rx",
        "ry",
        "rz",
        "u1q",
        "cx",
        "cz",
        "swap",
        "measure",
        "barrier",
    }:
        raise UnsupportedConstructError(f"No OpenQSE-facing encoding for '{operation.name}'.")

    instruction: dict[str, Any] = {"op": operation.name}
    targets = operation.target_indices()
    controls = operation.control_indices()
    if operation.name == "barrier":
        instruction["qubits"] = operation.qubit_indices()
    elif operation.name == "swap":
        instruction["qubits"] = operation.qubit_indices()
    elif operation.name == "measure":
        instruction["qubits"] = targets or operation.qubit_indices()
        instruction["clbits"] = operation.clbit_indices()
    else:
        if targets:
            instruction["qubits"] = targets
        if controls:
            instruction["controls"] = controls
    if operation.parameters and operation.name != "u1q":
        instruction["params"] = {p.name: p.value for p in operation.parameters}
    if config.include_unitaries_in_payload and operation.attributes.get("su2") is not None:
        instruction["unitary"] = operation.attributes.get("su2")
    if operation.name == "u1q":
        instruction["op"] = "unitary"
        instruction["origin"] = "u1q"
        instruction["unitary"] = operation.attributes.get("su2")
        instruction.pop("params", None)
    # Quaternion components are intentionally omitted from the payload.
    return instruction
