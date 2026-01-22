"""Minimal test for gemini_client without importing the rest of the app."""
import warnings


# Quiet common environment warning on macOS LibreSSL builds
warnings.filterwarnings('ignore', message=r"urllib3 v2 only supports OpenSSL.*")

from types import SimpleNamespace
from gemini_client import request_assessment
import json
import os


class MockSession:
    def __init__(self):
        self.machine_snapshot = SimpleNamespace(part_name='TestPart', mold_number='M-001', machine_brand='YIZUMI', machine_tonnage=200)
        self.step_skipped = {i: False for i in range(1, 8)}
        self.step_data_quality = {i: True for i in range(1, 8)}


def main():
    s = MockSession()
    key = os.getenv('GEMINI_API_KEY')
    if not key:
        print('No GEMINI_API_KEY found in environment. Set GEMINI_API_KEY or use the UI modal.')
        return

    print('Calling Gemini client with environment API key...')
    res = request_assessment(s, api_key=key)
    if res is None:
        print('Gemini request returned None (failure or non-JSON response).')
    else:
        print('Gemini returned JSON:')
        print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
