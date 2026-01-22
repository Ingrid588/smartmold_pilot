"""End-to-end smoke test: stored realtime AI notes -> PDF embed (no live AI call).

This test intentionally does NOT invoke any provider.
It builds a minimal SevenStepSessionState with stored AI assessments and generates
PDF via `generate_report_from_session`.

Run:
  PDF_DEBUG_NO_COMPRESS=1 ./.venv/bin/python smoke_test_ai_to_pdf.py
"""

from __future__ import annotations

import os
from pathlib import Path

from session_state import SevenStepSessionState, MachineSnapshot
import pdf_generator_v2


def main() -> int:
    # Make PDF bytes grep-friendly for assertions
    os.environ.setdefault("PDF_DEBUG_NO_COMPRESS", "1")

    session = SevenStepSessionState()
    session.machine_snapshot = MachineSnapshot(
        model_no="SMOKE-TEST",
        part_no="P-001",
        part_name="Demo Part",
        supplier="Supplier",
        owner="Owner",
        machine_tonnage=260,
    )

    # Simulate workflow-captured realtime AI notes (no API calls here)
    session.set_ai_assessment(
        0,
        {
            "overall": "机台参数输入完整，建议核对VP切换与保压上限。",
            "conclusions": ["当前参数在合理范围"],
            "actions": ["确认材料干燥与料温窗口"],
            "risks": ["若VP切换过早可能导致短射"],
        },
        provider="openai",
    )
    session.set_ai_assessment(
        1,
        {
            "overall": "粘度曲线拐点清晰，建议以拐点附近作为基准速度。",
            "conclusions": ["拐点附近稳定性更好"],
            "actions": ["记录该速度下的充填时间与峰值压力"],
            "risks": [],
        },
        provider="openai",
    )

    # White-box assertion: ensure the assessment page actually renders the AI notes section.
    seen = {
        "ai_section_title": False,
        "ai_comments_nonempty": False,
    }

    orig_subsection_title = getattr(pdf_generator_v2.Brand1ReportV2, "_subsection_title")
    orig_add_assessment_page = getattr(pdf_generator_v2.Brand1ReportV2, "add_assessment_page")

    def _wrapped_subsection_title(self, title: str):
        if isinstance(title, str) and "Realtime AI Notes" in title:
            seen["ai_section_title"] = True
        return orig_subsection_title(self, title)

    def _wrapped_add_assessment_page(self, assessment):
        try:
            if isinstance(assessment, dict) and assessment.get("ai_comments"):
                seen["ai_comments_nonempty"] = True
        except Exception:
            pass
        return orig_add_assessment_page(self, assessment)

    pdf_generator_v2.Brand1ReportV2._subsection_title = _wrapped_subsection_title
    pdf_generator_v2.Brand1ReportV2.add_assessment_page = _wrapped_add_assessment_page

    try:
        pdf_path = Path(pdf_generator_v2.generate_report_from_session(session, external_assessment=None))
    finally:
        # Always restore to avoid affecting other runs.
        pdf_generator_v2.Brand1ReportV2._subsection_title = orig_subsection_title
        pdf_generator_v2.Brand1ReportV2.add_assessment_page = orig_add_assessment_page

    assert pdf_path.exists(), f"PDF not found: {pdf_path}"
    size = pdf_path.stat().st_size
    assert size > 10_000, f"PDF too small ({size} bytes): {pdf_path}"

    assert seen["ai_comments_nonempty"], "Assessment did not include ai_comments (expected non-empty)"
    assert seen["ai_section_title"], "PDF did not render the 'Realtime AI Notes' section title"

    print("[OK] Generated PDF:", str(pdf_path))
    print("[OK] Size:", size, "bytes")
    print("[OK] Confirmed rendered section: Realtime AI Notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
