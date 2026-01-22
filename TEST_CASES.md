# SmartMold Pilot — Test Cases (Professional Suite)

This document is a comprehensive test-case suite designed to validate functionality, reliability, and release readiness.

Conventions:
- Priority: P0 (blocker) / P1 (high) / P2 (medium) / P3 (low)
- Type: UI / Integration / Unit / Regression / Performance
- Result fields: Expected outcome must be objectively verifiable.

---

## A. Smoke & Sanity (P0)

### TC-A01 — App cold start
- Priority: P0 | Type: Integration
- Preconditions: `.venv` exists; working directory is project root.
- Steps:
  1. Start app using the standard startup script (e.g., `./start_app.sh` or `python main.py`).
  2. Observe console for exceptions.
  3. Open `/`.
- Expected:
  - No traceback; app serves pages.
  - Dashboard renders (even if DB not initialized, warning is shown).

### TC-A02 — DB initialization status shown
- Priority: P0 | Type: UI/Integration
- Steps:
  1. Open `/`.
- Expected:
  - If DB init succeeded: shows “Database connected successfully”.
  - If DB init failed: shows “Database not initialized” warning but does not crash.

### TC-A03 — Scientific Molding page does not auto-open API popup
- Priority: P0 | Type: UI
- Steps:
  1. Open `/scientific-molding`.
- Expected:
  - Page loads without blocking API key modal/dialog.
  - If keys missing, user sees non-blocking guidance to `/settings`.

### TC-A04 — Settings page loads and shows current API
- Priority: P0 | Type: UI
- Steps:
  1. Open `/settings`.
- Expected:
  - No crash.
  - “当前 API: …” label renders.

---

## B. API Configuration & Failover (P0/P1)

### TC-B01 — OpenAI test applies key and model to runtime
- Priority: P0 | Type: Integration
- Preconditions: Have a valid OpenAI API key (optional for manual verification).
- Steps:
  1. Open `/settings`.
  2. Set model to a known-available model (e.g., `gpt-4o-mini`).
  3. Paste OpenAI key.
  4. Click “测试”.
- Expected:
  - Test returns success.
  - Subsequent realtime AI in workflow can read key without needing extra “save” steps.

### TC-B02 — OpenAI test detects invalid key
- Priority: P1 | Type: Integration
- Steps:
  1. Enter a fake key.
  2. Click test.
- Expected:
  - Shows 401 invalid key (or equivalent) clearly.

### TC-B03 — Model-name mismatch detection
- Priority: P1 | Type: Integration
- Steps:
  1. Set an invalid model name.
  2. Click OpenAI test.
- Expected:
  - Test fails with a clear HTTP error; user can correct model.

### TC-B04 — Failover order honored (simulation)
- Priority: P1 | Type: Integration
- Preconditions: Configure multiple providers but intentionally break first provider.
- Steps:
  1. Ensure the first provider fails (e.g., invalid key).
  2. Trigger realtime comment in Step 0.
- Expected:
  - System tries next provider.
  - UI indicates which provider was used.

---

## C. Scientific Molding Workflow (Steps 0–7) (P0/P1)

### TC-C01 — Step 0 captures machine snapshot
- Priority: P0 | Type: Integration
- Steps:
  1. Open `/scientific-molding`.
  2. Complete Step 0 machine fields.
  3. Proceed to next step.
- Expected:
  - Session contains `machine_snapshot`.
  - No crash.

### TC-C02 — Step-to-step inheritance
- Priority: P0 | Type: Integration
- Steps:
  1. Complete Step 1.
  2. Navigate Step 2 and confirm Step 1 results are still present.
- Expected:
  - `optimal_injection_speed` persists.
  - No step result resets unexpectedly.

### TC-C03 — Mark “unreasonable” data path
- Priority: P1 | Type: UI/Integration
- Steps:
  1. In any step, mark data as unreasonable and provide remark.
- Expected:
  - Session `step_remarks` updated.
  - Step status reflects “unreasonable”.
  - PDF shows it in assessment metrics/remarks.

### TC-C04 — Step skipped path
- Priority: P1 | Type: UI/Integration
- Steps:
  1. Skip a step.
  2. Continue.
- Expected:
  - `step_skipped[step]=True`.
  - PDF generation does not crash and reflects skip.

### TC-C05 — Realtime AI assessment stored per step
- Priority: P0 | Type: Integration
- Steps:
  1. Trigger realtime AI comment in Step 0.
  2. Trigger realtime AI assessment in at least one later step.
- Expected:
  - `session.ai_assessments` contains entries keyed by correct step numbers.

---

## D. PDF Report Generation (P0/P1)

### TC-D01 — PDF generation succeeds without realtime AI
- Priority: P0 | Type: Integration
- Steps:
  1. Complete workflow with no AI success (or disable keys).
  2. Generate PDF.
- Expected:
  - PDF is generated successfully.
  - No live AI call is required at generation time.

### TC-D02 — PDF includes captured AI notes
- Priority: P0 | Type: Integration
- Preconditions: At least one step produced a successful realtime AI assessment.
- Steps:
  1. Generate PDF.
  2. Open the assessment page.
- Expected:
  - Section “实时AI点评摘录 (Realtime AI Notes)” appears.
  - Notes include step name, provider, and summary lines.

### TC-D03 — Deterministic PDF smoke test (automated)
- Priority: P0 | Type: Regression
- Steps:
  1. Run `PDF_DEBUG_NO_COMPRESS=1 ./.venv/bin/python smoke_test_ai_to_pdf.py`.
- Expected:
  - Exit code 0.
  - Prints `[OK] Confirmed rendered section: Realtime AI Notes`.

### TC-D04 — PDF generator handles long text gracefully
- Priority: P1 | Type: Robustness
- Steps:
  1. Create a session with very long AI notes.
  2. Generate PDF.
- Expected:
  - No `FPDFException`.
  - Notes are truncated/limited as intended.

---

## E. Machine Performance Module (P1/P2)

### TC-E01 — Machine-check page loads
- Priority: P1 | Type: UI
- Steps:
  1. Open `/machine-check`.
- Expected:
  - No crash; tabs render.

### TC-E02 — Run each machine performance test
- Priority: P1 | Type: Integration
- Steps:
  1. Run weight repeatability.
  2. Run speed linearity.
  3. Run pressure consistency.
- Expected:
  - Charts render.
  - History table updates.

---

## F. Data & Persistence (DB) (P1/P2)

### TC-F01 — Dashboard stats do not crash if DB empty
- Priority: P1 | Type: Integration
- Steps:
  1. Start fresh DB.
  2. Open `/`.
- Expected:
  - Counts render (0 or N/A), no crash.

### TC-F02 — Experiment session records appear
- Priority: P2 | Type: Integration
- Steps:
  1. Complete a workflow that writes records (if supported).
  2. Open dashboard recent experiments.
- Expected:
  - Records show expected fields.

---

## G. Non-Functional Tests (P1/P2)

### TC-G01 — Performance: PDF generation time
- Priority: P2 | Type: Performance
- Steps:
  1. Generate PDF for a full seeded dataset.
- Expected:
  - Completes under a target (e.g., <3s locally) with no crash.

### TC-G02 — Reliability: repeated PDF generations
- Priority: P2 | Type: Reliability
- Steps:
  1. Generate PDF 20 times.
- Expected:
  - No memory blow-up; no intermittent exceptions.

---

## H. Security/Hardening (P1/P2)

### TC-H01 — Secrets not printed
- Priority: P1 | Type: Security
- Steps:
  1. Configure API key.
  2. Perform tests.
- Expected:
  - Logs do not print full API keys.

### TC-H02 — .env not exposed in static
- Priority: P1 | Type: Security
- Steps:
  1. Verify static serving does not include `.env`.
- Expected:
  - Not accessible.

