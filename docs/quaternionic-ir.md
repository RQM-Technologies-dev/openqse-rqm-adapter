# Quaternionic IR

This document describes the IR **actually implemented** in this repository
(`rqm-quaternionic-ir/v0.1`). It is an adapter-internal representation, not an
OpenQSE IR and not the production `rqm-circuits` wire format.

## Objects

| Object | Role |
| --- | --- |
| `Module` | Named program with qubits, clbits, operations, metadata, target requirements |
| `Qubit` | Indexed qubit or classical bit (`index`, optional `name`) |
| `Operation` | Named instruction with operands, parameters, attributes, source |
| `Operand` | `kind` (`qubit`/`clbit`), `index`, `role` |
| `Parameter` | Named numeric value; unbound parameters are rejected |
| `Attribute` | Free-form dict; holds `quaternion` and `su2` when present |
| `Measurement` | Helper that becomes a `measure` operation |
| `TargetRequirements` | `min_qubits`, `min_clbits`, `required_operations` |
| `SourceLocation` | Optional file/line/note |

## Supported operations

| Name | Qubits | Parameters | Quaternion form |
| --- | --- | --- | --- |
| `i` | 1 | — | `q = 1` |
| `x` | 1 | — | `q = i` |
| `y` | 1 | — | `q = j` |
| `z` | 1 | — | `q = k` |
| `h` | 1 | — | `q = (i+k)/√2` |
| `s` | 1 | — | `q = cos(π/4) + k sin(π/4)` |
| `t` | 1 | — | `q = cos(π/8) + k sin(π/8)` |
| `rx` | 1 | `angle` | `q = cos(θ/2) + i sin(θ/2)` |
| `ry` | 1 | `angle` | `q = cos(θ/2) + j sin(θ/2)` |
| `rz` | 1 | `angle` | `q = cos(θ/2) + k sin(θ/2)` |
| `u1q` | 1 | `w,x,y,z` | native unit quaternion |
| `cx` | control+target | — | none (standard CNOT) |
| `cz` | control+target | — | none |
| `swap` | 2 | — | none |
| `measure` | qubit+clbit | — | none |
| `barrier` | variable | — | none |

Aliases accepted on ingest: `id`/`identity` → `i`, `cnot` → `cx`,
`theta`/`phi` → `angle`.

## Quaternion / SU(2) convention

A unit quaternion `q = w + x i + y j + z k` maps to SU(2) as:

```
U(q) = [[ w - i z,  -y - i x ],
        [ y - i x,   w + i z ]]
```

This matches the documented RQM / `rqm-core` convention. The resulting matrix
may differ from a textbook named-gate matrix by a global phase.
Computational-basis probabilities are invariant under that phase.

`u1q` requires `|q| = 1` within `1e-8`.

Two-qubit operations are **not** given quaternion forms. This prototype does
not define a quaternionic replacement for CNOT.

## JSON

```json
{
  "schema": "rqm-quaternionic-ir/v0.1",
  "status": "experimental",
  "module": {
    "name": "bell_h_cx",
    "qubits": [{"index": 0, "name": "q0"}, {"index": 1, "name": "q1"}],
    "clbits": [{"index": 0, "name": "c0"}, {"index": 1, "name": "c1"}],
    "operations": [
      {
        "name": "h",
        "operands": [{"kind": "qubit", "index": 0, "role": "target"}],
        "parameters": [],
        "attributes": {
          "quaternion": {"w": 0.0, "x": 0.7071067811865475, "y": 0.0, "z": 0.7071067811865475}
        }
      }
    ],
    "metadata": {},
    "target_requirements": {
      "min_qubits": 2,
      "min_clbits": 2,
      "required_operations": ["h", "cx", "measure"]
    }
  }
}
```

Complex SU(2) entries serialize as `{"re": ..., "im": ...}`.

## Semantics that are not claimed

- No alternative quantum mechanics
- No extra information beyond ordinary SU(2) for single-qubit rotations
- No physical-hardware advantage
- No complete multi-qubit quaternionic calculus
