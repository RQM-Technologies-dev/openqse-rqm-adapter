# Minimal quaternionic program

This example builds a one-qubit program with the native `u1q` gate.

The quaternion `(w, x, y, z) = (0, 1/√2, 0, 1/√2)` is the RQM form of a
Hadamard rotation. The adapter lowers it to an explicit SU(2) unitary in an
OpenQSE-compatible payload. The local simulator then reports computational-basis
probabilities, which should be approximately `0.5` / `0.5` for `|0>` / `|1>`.

```bash
python3 examples/basic_quaternionic/run.py
```
