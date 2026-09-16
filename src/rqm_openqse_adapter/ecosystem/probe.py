"""Record real sibling-function calls without replacing their implementations."""

from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Iterator


class CallProbe:
    def __init__(self) -> None:
        self.calls: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._restores: list[tuple[Any, str, Any]] = []

    def record(self, label: str, **payload: Any) -> None:
        self.calls[label].append(payload)

    def wrap_function(self, module: Any, name: str, label: str | None = None) -> None:
        original = getattr(module, name)
        key = label or f"{module.__name__}.{name}"

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            result = original(*args, **kwargs)
            self.record(
                key,
                arg_types=[type(arg).__name__ for arg in args],
                result_type=type(result).__name__,
            )
            return result

        setattr(module, name, wrapped)
        self._restores.append((module, name, original))

    def wrap_method(self, cls: type, name: str, label: str | None = None) -> None:
        original = getattr(cls, name)
        key = label or f"{cls.__name__}.{name}"

        def wrapped(self_or_cls: Any, *args: Any, **kwargs: Any) -> Any:
            result = original(self_or_cls, *args, **kwargs)
            extra = {}
            if hasattr(self_or_cls, "axis"):
                extra["axis"] = getattr(self_or_cls, "axis", None)
            if hasattr(self_or_cls, "theta"):
                extra["theta"] = getattr(self_or_cls, "theta", None)
            self.record(key, result_type=type(result).__name__, **extra)
            return result

        setattr(cls, name, wrapped)
        self._restores.append((cls, name, original))

    def restore(self) -> None:
        for owner, name, original in reversed(self._restores):
            setattr(owner, name, original)
        self._restores.clear()

    def count(self, label: str) -> int:
        return len(self.calls.get(label, []))


@contextmanager
def installed_probes() -> Iterator[CallProbe]:
    probe = CallProbe()
    try:
        yield probe
    finally:
        probe.restore()
