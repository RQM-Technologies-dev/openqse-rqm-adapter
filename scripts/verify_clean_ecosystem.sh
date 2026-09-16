#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ECOSYSTEM_ROOT="${ECOSYSTEM_ROOT:-${ROOT}/.ecosystem}"
REPORT_PATH="${REPORT_PATH:-${ROOT}/examples/conformance/conformance-report.json}"
REPORTS_DIR="${ROOT}/.ecosystem-reports"
SKIP_CLONE="${SKIP_CLONE:-0}"
SIBLINGS=(rqm-core rqm-circuits rqm-entanglement rqm-compiler rqm-qiskit rqm-optimize)

log() {
  printf '%s\n' "$*"
}

clone_or_update() {
  local name="$1"
  local dest="${ECOSYSTEM_ROOT}/${name}"
  if [[ "${SKIP_CLONE}" == "1" ]]; then
    if [[ ! -f "${dest}/pyproject.toml" ]]; then
      log "SKIP_CLONE=1 but ${dest} is missing pyproject.toml"
      exit 1
    fi
    log "Using pre-checked-out ${name} at ${dest}"
    return 0
  fi
  if [[ -d "${dest}/.git" ]]; then
    git -C "${dest}" fetch origin main
    git -C "${dest}" checkout main
    git -C "${dest}" pull --ff-only origin main
  else
    mkdir -p "${ECOSYSTEM_ROOT}"
    if command -v gh >/dev/null 2>&1; then
      gh repo clone "RQM-Technologies-dev/${name}" "${dest}" -- --branch main --single-branch
    else
      git clone --branch main --single-branch "https://github.com/RQM-Technologies-dev/${name}.git" "${dest}"
    fi
  fi
}

mkdir -p "${ECOSYSTEM_ROOT}" "${REPORTS_DIR}"
for sibling in "${SIBLINGS[@]}"; do
  log "Preparing ${sibling}"
  clone_or_update "${sibling}"
done

create_venv() {
  local dest="$1"
  if "${PYTHON_BIN}" -c "import ensurepip" >/dev/null 2>&1; then
    "${PYTHON_BIN}" -m venv "${dest}"
    return
  fi
  log "ensurepip is unavailable; falling back to virtualenv"
  "${PYTHON_BIN}" -m pip install --user virtualenv
  "${PYTHON_BIN}" -m virtualenv "${dest}"
}

VENV="${ROOT}/.venv-clean-ecosystem"
rm -rf "${VENV}"
create_venv "${VENV}"
# shellcheck disable=SC1091
source "${VENV}/bin/activate"
python -m pip install --upgrade pip wheel setuptools

python -m pip install -e "${ECOSYSTEM_ROOT}/rqm-core"
python -m pip install -e "${ECOSYSTEM_ROOT}/rqm-circuits"
python -m pip install -e "${ECOSYSTEM_ROOT}/rqm-entanglement"
python -m pip install -e "${ECOSYSTEM_ROOT}/rqm-compiler"
python -m pip install -e "${ECOSYSTEM_ROOT}/rqm-qiskit[dev]"
python -m pip install -e "${ECOSYSTEM_ROOT}/rqm-optimize"
python -m pip install -e "${ROOT}[dev]"

log "Python: $(python -c 'import sys; print(sys.version)')"
log "Import checks"
python - <<'PY'
import importlib
modules = [
    "rqm_core",
    "rqm_circuits",
    "rqm_compiler",
    "rqm_entanglement",
    "rqm_qiskit",
    "rqm_optimize",
    "rqm_openqse_adapter",
]
for name in modules:
    module = importlib.import_module(name)
    print(f"imported {name} from {module.__file__}")
PY

log "Adapter test suite"
python -m pytest "${ROOT}/tests" -q --tb=short --junitxml="${REPORTS_DIR}/adapter.xml"

log "Conformance demonstration"
python "${ROOT}/examples/conformance/run.py" --ecosystem-root "${ECOSYSTEM_ROOT}" --save "${REPORT_PATH}"

log "Sibling package tests required for this integration"
python -m pytest "${ECOSYSTEM_ROOT}/rqm-core/tests" -q --tb=short --junitxml="${REPORTS_DIR}/rqm-core.xml"
python -m pytest "${ECOSYSTEM_ROOT}/rqm-circuits/tests" -q --tb=short --junitxml="${REPORTS_DIR}/rqm-circuits.xml"
python -m pytest "${ECOSYSTEM_ROOT}/rqm-entanglement/tests" -q --tb=short --junitxml="${REPORTS_DIR}/rqm-entanglement.xml"
python -m pytest "${ECOSYSTEM_ROOT}/rqm-compiler/tests" -q --tb=short --junitxml="${REPORTS_DIR}/rqm-compiler.xml"
python -m pytest "${ECOSYSTEM_ROOT}/rqm-optimize/tests" -q --tb=short --junitxml="${REPORTS_DIR}/rqm-optimize.xml"
python -m pytest "${ECOSYSTEM_ROOT}/rqm-qiskit/tests" -q --tb=short --junitxml="${REPORTS_DIR}/rqm-qiskit.xml"

log "Recording test counts in conformance report"
REPORT_PATH="${REPORT_PATH}" REPORTS_DIR="${REPORTS_DIR}" python - <<'PY'
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

report_path = Path(os.environ["REPORT_PATH"])
reports_dir = Path(os.environ["REPORTS_DIR"])
payload = json.loads(report_path.read_text(encoding="utf-8"))
counts = {}
totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
for xml_path in sorted(reports_dir.glob("*.xml")):
    tree = ET.parse(xml_path)
    tests = failures = errors = skipped = 0
    for suite in tree.iter("testsuite"):
        tests += int(suite.attrib.get("tests", 0))
        failures += int(suite.attrib.get("failures", 0))
        errors += int(suite.attrib.get("errors", 0))
        skipped += int(suite.attrib.get("skipped", 0))
    counts[xml_path.stem] = {
        "tests": tests,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "passed": tests - failures - errors - skipped,
    }
    for key in totals:
        totals[key] += counts[xml_path.stem][key]
totals["passed"] = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
payload["test_counts"] = {"suites": counts, "totals": totals}
report_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
print(json.dumps(payload["test_counts"], indent=2, sort_keys=True))
PY

log "Clean ecosystem verification passed"
log "Report: ${REPORT_PATH}"
