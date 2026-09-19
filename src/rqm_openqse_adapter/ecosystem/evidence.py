"""Evidence ledger for installed / imported / executed / verified capabilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from ..diagnostics import AdapterError


@dataclass
class CapabilityEvidence:
    name: str
    installed: bool = False
    imported: bool = False
    executed: bool = False
    verified: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "installed": self.installed,
            "imported": self.imported,
            "executed": self.executed,
            "verified": self.verified,
            "details": dict(self.details),
        }


class EvidenceLedger:
    def __init__(self) -> None:
        self.capabilities: dict[str, CapabilityEvidence] = {}

    def ensure(self, name: str) -> CapabilityEvidence:
        if name not in self.capabilities:
            self.capabilities[name] = CapabilityEvidence(name=name)
        return self.capabilities[name]

    def mark_installed(self, name: str, *, distribution: str | None = None, **details: Any) -> None:
        cap = self.ensure(name)
        dist = distribution or name
        try:
            cap.details["version"] = version(dist)
            cap.installed = True
        except PackageNotFoundError:
            cap.installed = False
            cap.details["version"] = None
        cap.details.update(details)

    def mark_imported(self, name: str, **details: Any) -> None:
        cap = self.ensure(name)
        cap.imported = True
        cap.details.update(details)

    def mark_executed(self, name: str, **details: Any) -> None:
        cap = self.ensure(name)
        cap.executed = True
        cap.details.update(details)

    def mark_verified(self, name: str, **details: Any) -> None:
        cap = self.ensure(name)
        if not cap.executed:
            raise AdapterError(f"Cannot verify {name}: capability was not executed.")
        cap.verified = True
        cap.details.update(details)

    def inherit_from_package(self, name: str, package: str, **details: Any) -> None:
        """Copy installed/imported flags from a real distribution onto an API surface."""
        src = self.ensure(package)
        cap = self.ensure(name)
        cap.installed = src.installed
        cap.imported = src.imported
        cap.details["owning_package"] = package
        if "version" in src.details:
            cap.details["package_version"] = src.details["version"]
        cap.details.update(details)

    def require_executed_and_verified(self, names: list[str]) -> None:
        failures: list[str] = []
        for name in names:
            cap = self.capabilities.get(name) or CapabilityEvidence(name=name)
            missing = [
                flag
                for flag, ok in (
                    ("installed", cap.installed),
                    ("imported", cap.imported),
                    ("executed", cap.executed),
                    ("verified", cap.verified),
                )
                if not ok
            ]
            if missing:
                failures.append(f"{name}: missing {', '.join(missing)}")
        if failures:
            raise AdapterError(
                "Clean ecosystem demonstration failed closed. Required capabilities "
                "were not fully exercised:\n  " + "\n  ".join(failures)
            )

    def to_dict(self) -> dict[str, Any]:
        return {name: cap.to_dict() for name, cap in sorted(self.capabilities.items())}
