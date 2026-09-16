# Entanglement / Bell-style example

This example uses the ordinary two-qubit sequence `H q0; CX q0,q1`.

The adapter:

1. Records the documented quaternion form of `H`.
2. Leaves `CX` as a standard named two-qubit operation (no quaternion form).
3. Emits an OpenQSE-compatible payload without quaternion components.
4. Executes the payload on the local statevector simulator.

For this gate sequence the ideal computational-basis probabilities are
`P(00) = P(11) = 0.5`. That is the usual Bell-state measurement distribution
for `H+CX` on `|00>`. This repository does not introduce a separate
quaternionic entanglement primitive.

```bash
python3 examples/bell/run.py
```
