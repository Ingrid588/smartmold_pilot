"""Test script to call gemini_client.request_assessment and generate a report."""
import warnings

# Quiet common environment warning on macOS LibreSSL builds
warnings.filterwarnings('ignore', message=r"urllib3 v2 only supports OpenSSL.*")

import os
import json
from session_state import SevenStepSessionState, MachineSnapshot
from gemini_client import request_assessment
from pdf_generator_v2 import generate_report_from_session


def make_test_session():
    s = SevenStepSessionState()
    snap = MachineSnapshot()
    snap.part_name = 'Handle Housing Support'
    snap.mold_number = 'TG34724342-07'
    snap.machine_brand = 'YIZUMI'
    snap.machine_tonnage = 260
    s.machine_snapshot = snap

    # simulate step quality and skipped
    for i in range(1, 8):
        s.step_data_quality[i] = True
        s.step_skipped[i] = False

    return s


def main():
    sess = make_test_session()
    print('Requesting assessment from selected provider (reads environment SELECTED_API_PROVIDER / SELECTED_API_KEY or GEMINI_API_KEY)...')
    # Prefer SELECTED_API_PROVIDER/SELECTED_API_KEY (set by UI modal); fall back to GEMINI_API_KEY
    provider = os.getenv('SELECTED_API_PROVIDER', 'gemini')
    key = os.getenv('SELECTED_API_KEY') or os.getenv('GEMINI_API_KEY')
    if not key:
        print('No API key found in environment (SELECTED_API_KEY / GEMINI_API_KEY). Falling back to mock assessment.')
        assessment = None
    else:
        if provider.lower() == 'gemini':
            assessment = request_assessment(sess, api_key=key)
        else:
            # for other providers we currently treat as not implemented and fall back
            print(f'Provider {provider} testing not implemented in this script; falling back.')
            assessment = None
    if assessment is None:
        print('Gemini call failed or returned non-JSON. Falling back to mock assessment.')
    else:
        print('Gemini returned assessment:')
        print(json.dumps(assessment, indent=2, ensure_ascii=False))

    print('Generating PDF using the assessment (or fallback).')
    pdf_path = generate_report_from_session(sess, external_assessment=assessment)
    print('PDF generated at:', pdf_path)


if __name__ == '__main__':
    main()
