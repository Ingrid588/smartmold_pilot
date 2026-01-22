"""Utility to test API keys for multiple providers.

Provides a simple `test_provider_key(provider, key)` function that attempts
to validate the provided key for known providers: 'gemini', 'openai', 'claude', 'deepseek'.
Returns (True, message) on success or (False, error_message) on failure.

Note: network calls may fail for many reasons; this helper is intentionally
simple and conservative — a non-exceptional HTTP 2xx response that yields
JSON is treated as success for most providers.
"""
from typing import Tuple
import requests
import os
import json

from gemini_client import request_assessment
from types import SimpleNamespace


def _make_mock_session():
    s = SimpleNamespace()
    s.machine_snapshot = SimpleNamespace(part_name='TestPart', mold_number='M-TEST', machine_brand='YIZU', machine_tonnage=200)
    s.step_skipped = {i: False for i in range(1, 8)}
    s.step_data_quality = {i: True for i in range(1, 8)}
    return s


def test_provider_key(provider: str, key: str, timeout: int = 8) -> Tuple[bool, str]:
    """Test the API key for the named provider.

    provider: one of 'gemini', 'openai', 'claude', 'deepseek'
    key: the API key string
    Returns: (success: bool, message: str)
    """
    if not key or not key.strip():
        return False, 'API key is empty'

    provider = provider.lower()

    try:
        if provider == 'gemini':
            # Use gemini_client.test_key to get a diagnostic message
            from gemini_client import test_key
            ok, msg = test_key(api_key=key)
            if ok:
                return True, f'Gemini key validated: {msg}'
            return False, msg

        if provider == 'openai':
            # Query models endpoint as a lightweight validation
            url = 'https://api.openai.com/v1/models'
            headers = {'Authorization': f'Bearer {key}'}
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 200:
                try:
                    _ = r.json()
                    return True, 'OpenAI key validated (models endpoint)' 
                except Exception:
                    return False, 'OpenAI responded but returned non-JSON'
            return False, f'OpenAI returned HTTP {r.status_code}: {r.text[:200]}'

        if provider == 'claude':
            # Anthropic uses x-api-key header for some endpoints; attempt a lightweight call
            url = 'https://api.anthropic.com/v1/models'
            headers = {'x-api-key': key}
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 200:
                try:
                    _ = r.json()
                    return True, 'Claude key validated (models endpoint)'
                except Exception:
                    return False, 'Claude responded but returned non-JSON'
            return False, f'Claude returned HTTP {r.status_code}: {r.text[:200]}'

        if provider == 'deepseek':
            # Deepseek API uses chat completions endpoint for testing
            url = 'https://api.deepseek.com/v1/chat/completions'
            headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
            body = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 5,
            }
            r = requests.post(url, headers=headers, json=body, timeout=timeout)
            if r.status_code == 200:
                try:
                    _ = r.json()
                    return True, 'Deepseek key validated (chat completions)'
                except Exception:
                    return False, 'Deepseek responded but returned non-JSON'
            return False, f'Deepseek returned HTTP {r.status_code}: {r.text[:200]}'

        return False, f'Unknown provider: {provider}'

    except requests.RequestException as e:
        return False, f'Network error: {str(e)}'
    except Exception as e:
        return False, f'Error: {str(e)}'
