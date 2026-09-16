#!/usr/bin/env python3
"""Fail-closed OpenQSE/RQM ecosystem conformance demonstration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rqm_openqse_adapter.ecosystem import run_clean_demonstration


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ecosystem-root",
        type=Path,
        default=None,
        help="Directory containing sibling RQM git checkouts.",
    )
    parser.add_argument(
        "--save",
        type=Path,
        default=None,
        help="Optional path for the JSON report.",
    )
    args = parser.parse_args(argv)
    report = run_clean_demonstration(ecosystem_root=args.ecosystem_root)
    text = report.to_json()
    print(text)
    target = args.save or Path(__file__).resolve().parent / "conformance-report.json"
    target.write_text(text + "\n", encoding="utf-8")
    print(f"Wrote {target}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
