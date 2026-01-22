#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PY="./.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "[ERR] Python venv not found at $PY" >&2
  exit 1
fi

echo "[1/3] Syntax check"
$PY -m py_compile \
  main.py \
  scientific_molding_6steps.py \
  session_state.py \
  pdf_generator_v2.py \
  smoke_test_ai_to_pdf.py

echo "[2/3] Deterministic smoke test (AI notes -> PDF)"
PDF_DEBUG_NO_COMPRESS=1 $PY smoke_test_ai_to_pdf.py

echo "[3/3] Optional full PDF report generator"
if [[ -f test_pdf_report.py ]]; then
  $PY test_pdf_report.py || true
  echo "[INFO] test_pdf_report.py executed (non-blocking)"
fi

echo "[DONE] Test suite finished"
