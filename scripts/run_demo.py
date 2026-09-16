#!/usr/bin/env python3
"""Run the three bundled adapter demonstrations."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rqm_openqse_adapter.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
