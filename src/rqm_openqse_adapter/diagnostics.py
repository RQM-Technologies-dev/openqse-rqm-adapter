"""Diagnostics and adapter errors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator, Literal

Severity = Literal["error", "warning", "info"]


class AdapterError(Exception):
    """Base error for the RQM OpenQSE adapter."""


class ValidationError(AdapterError):
    """The program, IR, or target failed validation."""


class UnsupportedConstructError(AdapterError):
    """A construct is recognized but not supported by this prototype."""


class TargetMismatchError(AdapterError):
    """The compiled artifact is incompatible with the selected target."""


@dataclass(frozen=True)
class Diagnostic:
    severity: Severity
    code: str
    message: str
    location: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.location:
            payload["location"] = self.location
        if self.data:
            payload["data"] = dict(self.data)
        return payload


@dataclass
class Diagnostics:
    items: list[Diagnostic] = field(default_factory=list)

    def add(
        self,
        severity: Severity,
        code: str,
        message: str,
        *,
        location: str | None = None,
        **data: Any,
    ) -> Diagnostic:
        item = Diagnostic(severity, code, message, location, data)
        self.items.append(item)
        return item

    def extend(self, other: Diagnostics | Iterable[Diagnostic]) -> None:
        if isinstance(other, Diagnostics):
            self.items.extend(other.items)
        else:
            self.items.extend(other)

    def errors(self) -> list[Diagnostic]:
        return [item for item in self.items if item.severity == "error"]

    def warnings(self) -> list[Diagnostic]:
        return [item for item in self.items if item.severity == "warning"]

    def ok(self) -> bool:
        return not self.errors()

    def raise_if_errors(self) -> None:
        errors = self.errors()
        if not errors:
            return
        summary = "; ".join(item.message for item in errors)
        raise ValidationError(summary)

    def to_list(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.items]

    def __iter__(self) -> Iterator[Diagnostic]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)
