from __future__ import annotations

import pytest

from rqm_openqse_adapter.diagnostics import AdapterError
from rqm_openqse_adapter.ecosystem.evidence import EvidenceLedger


def test_inherit_from_package_copies_installed_and_imported_only() -> None:
    ledger = EvidenceLedger()
    owner = ledger.ensure("rqm-compiler")
    owner.installed = True
    owner.imported = True
    owner.details["version"] = "0.3.0"
    ledger.inherit_from_package("to_u1q", "rqm-compiler", module="rqm_compiler.passes.to_u1q")
    cap = ledger.capabilities["to_u1q"]
    assert cap.installed is True
    assert cap.imported is True
    assert cap.executed is False
    assert cap.verified is False
    assert cap.details["owning_package"] == "rqm-compiler"
    assert cap.details["package_version"] == "0.3.0"


def test_require_fails_closed_when_a_capability_was_only_imported() -> None:
    ledger = EvidenceLedger()
    cap = ledger.ensure("rqm-compiler")
    cap.installed = True
    cap.imported = True
    with pytest.raises(AdapterError, match="missing executed, verified"):
        ledger.require_executed_and_verified(["rqm-compiler"])


def test_require_fails_closed_for_unknown_capability() -> None:
    ledger = EvidenceLedger()
    with pytest.raises(AdapterError, match="AxisHinge.promote"):
        ledger.require_executed_and_verified(["AxisHinge.promote"])
