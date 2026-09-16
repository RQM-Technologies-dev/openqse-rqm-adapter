# Compiler pipeline

Default order:

```
program
  -> validate
  -> canonicalize
  -> lower
  -> OpenQSE payload
```

These passes are real and have tests. They are not a production optimizer.

## Pass interface

```python
class CompilerPass:
    name: str
    def run(self, module: Module, context: PassContext) -> Module: ...
```

`PassContext` carries the selected `Target`, `AdapterConfig`, and
`Diagnostics`. `PassManager` runs passes in order and stops on errors.

## validate

Checks:

- known operation names
- qubit/clbit ranges
- operand and control counts
- bound parameters
- unit quaternion for `u1q`
- target capacity, supported operations, and connectivity

Does not: type-check hybrid programs, verify unitaries numerically beyond the
quaternion norm, or prove semantic equivalence.

## canonicalize

- lowercases names and applies aliases
- renames `theta`/`phi` to `angle`
- attaches documented quaternion forms to single-qubit ops
- drops identity operations when `AdapterConfig.drop_identity` is true

TODO: commutation, gate fusion, quaternion composition, inverse cancellation.

## lower

- derives the RQM SU(2) matrix from each quaternion form
- marks operations `lowered`
- leaves two-qubit named gates as named gates
- records `metadata["payload_ready"] = True`

TODO: native-gate synthesis, mapping/routing, OpenQASM/Qiskit/MLIR emitters,
QEC-aware lowering.

## Extension points

Insert a pass:

```python
from rqm_openqse_adapter.passes import (
    CanonicalizePass,
    LowerPass,
    PassManager,
    ValidatePass,
)

manager = PassManager([
    ValidatePass(),
    CanonicalizePass(),
    MyRewritePass(),  # additional RQM pass
    LowerPass(),
])
```

Then pass that manager into `OpenQSEAdapter(passes=manager)`.

Keep quaternion-specific rewrites **before** lowering. After lowering, prefer
transforms that operate on named gates or explicit unitaries so the OpenQSE
side never has to recover quaternion semantics.
