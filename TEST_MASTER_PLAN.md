# SmartMold Pilot — Master Test Plan (MTP)

Version: 1.0  
Date: 2026-01-14  
Scope: End-to-end validation of SmartMold Pilot (NiceGUI app) including AI settings/failover, Scientific Molding workflow, machine performance testing, DB persistence, and PDF report generation.

## 1. Objectives
- Validate core user journeys work reliably across cold start, missing config, partial config, and error scenarios.
- Ensure realtime AI is called only during workflow steps (not during PDF generation) and that captured AI notes are embedded into the PDF.
- Verify data integrity across steps 0–7, including the “unreasonable data” paths and skipped steps.
- Confirm performance and stability for typical dataset sizes.

## 2. In Scope
- UI routes: `/`, `/scientific-molding`, `/machine-check`, `/settings`, `/about`.
- API key configuration and failover order.
- Scientific Molding 7-step workflow state (`SevenStepSessionState`) and derived metrics.
- PDF generation via `pdf_generator_v2.py` including “Realtime AI Notes” section.
- DB init and basic CRUD paths used by dashboards/history.

## 3. Out of Scope (for this plan)
- Deep security pen-test of infra (network perimeter, auth, etc.).
- Cross-browser pixel-perfect UI layout verification.

## 4. Test Environments
- Local macOS (primary): Python 3.9+ in `.venv`.
- Optional: Linux runner (CI) for non-GUI smoke tests.

## 5. Test Data
- Seeded datasets: `seed_data.py` and existing generated JSON/HTML under `static/`.
- Synthetic “AI assessments” dictionaries stored in session to avoid external API dependence.

## 6. Test Strategy
### 6.1 Automated (fast, deterministic)
- Static checks: `python -m py_compile ...`
- Smoke tests:
  - `smoke_test_ai_to_pdf.py` (AI notes captured -> PDF includes section, no live AI call)
- Report generation regression:
  - `test_pdf_report.py` (seeded full report)

### 6.2 Manual (UI + integration)
- Settings page tests (real API optional): verify key apply, model config, failover messaging.
- Scientific Molding workflow: step navigation, state inheritance, “mark unreasonable,” “skip step,” and PDF export.
- Machine-check module: run tests, verify charts, ensure history table updates.

## 7. Entry / Exit Criteria
### Entry
- App launches without tracebacks.
- DB init succeeds or error is displayed clearly.
- `py_compile` passes for changed files.

### Exit
- All P0 and P1 test cases pass.
- No crashes in main user journeys.
- PDF export always succeeds for valid sessions.

## 8. Risk-Based Prioritization
- P0: Workflow and PDF export correctness; no blocking popups; settings apply keys.
- P1: Machine-check calculations and history.
- P2: Visual polish, non-critical copy, edge-case UI layout.

## 9. Release Checklist
- Run: `PDF_DEBUG_NO_COMPRESS=1 ./.venv/bin/python smoke_test_ai_to_pdf.py`
- Run: `./.venv/bin/python test_pdf_report.py` (optional if it writes local outputs)
- Run: `./.venv/bin/python -m py_compile main.py scientific_molding_6steps.py pdf_generator_v2.py session_state.py`
- Manual sanity:
  - Open `/settings`, verify no crash; save keys (optional), verify current API.
  - Open `/scientific-molding`, ensure no API config popup on entry.
  - Generate PDF and confirm “实时AI点评摘录 (Realtime AI Notes)” appears when AI notes exist.

