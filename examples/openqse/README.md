# OpenQSE integration example

This example is the adapter boundary demonstration:

```
quaternionic program
    -> quaternionic IR
    -> RQM passes
    -> OpenQSE adapter
    -> OpenQSE-compatible artifact
```

It prints:

* quaternion attributes that remain on the RQM IR
* the emitted artifact and target metadata
* diagnostics

The saved JSON file is an experimental RQM payload. It is not an official
OpenQSE schema.

```bash
python examples/openqse/run.py
```
