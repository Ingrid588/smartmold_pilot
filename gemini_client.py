"""Simple Gemini (Generative AI) client with graceful failure handling.

This module attempts a HTTP call to a Gemini-like endpoint. It purposely
keeps the request schema generic and fails gracefully: on any failure it
returns None so callers can fall back to a mock/local assessment.

Usage:
    from gemini_client import request_assessment
    assessment = request_assessment(session, api_key=os.getenv('GEMINI_API_KEY'))
"""
from typing import Optional, Dict, Any
import os
import json
import requests

# Optional import of the official Google GenAI SDK (if installed). If available,
# prefer the SDK because it handles auth and streaming more robustly. We keep the
# requests-based fallback for environments without the SDK.
try:
    from google import genai  # type: ignore
    _HAS_GENAI_SDK = True
except Exception:
    genai = None  # type: ignore
    _HAS_GENAI_SDK = False

DEFAULT_API_URL = os.getenv('GEMINI_API_URL',
                            'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generate')


def _build_prompt_from_session(session) -> str:
    """Create a compact prompt summarizing the session for Gemini."""
    try:
        snap = session.machine_snapshot
        header = {
            'part_name': getattr(snap, 'part_name', 'N/A') if snap else 'N/A',
            'mold_number': getattr(snap, 'mold_number', 'N/A') if snap else 'N/A',
            'machine_brand': getattr(snap, 'machine_brand', 'N/A') if snap else 'N/A',
            'machine_tonnage': getattr(snap, 'machine_tonnage', 'N/A') if snap else 'N/A',
        }
    except Exception:
        header = {}

    # Include a short list of step statuses if present
    step_info = []
    try:
        for i in range(1, 8):
            skipped = session.step_skipped.get(i, False)
            quality = session.step_data_quality.get(i, True)
            step_info.append(f"Step{i}: skipped={skipped}, quality={'OK' if quality else 'NG'}")
    except Exception:
        step_info = []

    prompt = (
        f"Please provide a concise machine & mold assessment in JSON with keys: metrics, conclusions, actions, risks, overall. "
        f"Use engineering tone.\nHeader: {json.dumps(header)}\nSteps: {', '.join(step_info)}\n" 
        f"Return only valid JSON."
    )
    return prompt


def request_assessment(session, api_key: Optional[str] = None, api_url: Optional[str] = None, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Request an assessment from Gemini. Returns a dict on success, or None on any failure.

    This function intentionally tolerates many failure modes since the UI
    wants to fall back to a local/mock AI behavior when Gemini is unreachable.
    """
    key = api_key or os.getenv('GEMINI_API_KEY')
    if not key:
        return None

    url = api_url or DEFAULT_API_URL

    prompt = _build_prompt_from_session(session)

    # If the official SDK is available, use it (prefer SDK for auth/compatibility).
    if _HAS_GENAI_SDK:
        try:
            client = genai.Client(api_key=api_key) if api_key else genai.Client()
            resp = client.models.generate_content(
                model=os.getenv('GEMINI_MODEL', 'gemini-3-small-preview'),
                contents=prompt,
                temperature=0.2,
                max_output_tokens=512,
            )
            # SDK may present the output in different attributes; try common ones
            text = None
            if hasattr(resp, 'text'):
                text = resp.text
            elif hasattr(resp, 'output'):
                text = getattr(resp, 'output')
            else:
                # Fallback: try stringify
                try:
                    text = json.dumps(resp)
                except Exception:
                    text = str(resp)

            if text:
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    return None
        except Exception:
            # fall through to HTTP path
            pass

    # Construct a generic POST body; many Gemini-like endpoints accept `prompt` or `input`.
    body = {
        'prompt': prompt,
        'max_output_tokens': 512,
        'temperature': 0.2,
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}'
    }

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=timeout)
        resp.raise_for_status()
        # Try parse JSON response body
        data = None
        try:
            data = resp.json()
        except Exception:
            # not JSON
            data = resp.text

        # The exact schema varies; attempt to find a JSON string payload
        def _find_text(obj):
            # recursive search for the first string that looks like JSON or contains braces
            if isinstance(obj, str):
                return obj
            if isinstance(obj, dict):
                # common nested keys
                for k in ('candidates', 'output', 'response', 'result', 'content'):
                    if k in obj:
                        return _find_text(obj[k])
                for v in obj.values():
                    res = _find_text(v)
                    if res:
                        return res
            if isinstance(obj, list):
                for item in obj:
                    res = _find_text(item)
                    if res:
                        return res
            return None

        text = _find_text(data)

        if not text:
            return None

        # If response is JSON string, parse it
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            # Not JSON — give up and return None to trigger fallback
            return None

    except Exception:
        return None

    return None


def test_key(api_key: Optional[str] = None, api_url: Optional[str] = None, timeout: int = 8) -> (bool, str):
    """Test whether the provided API key can reach the Gemini endpoint.

    Returns (success: bool, message: str).
    This helper performs a single minimal call and returns diagnostic messages
    so the UI can display why a key validation failed.
    """
    key = api_key or os.getenv('GEMINI_API_KEY')
    if not key:
        return False, 'No GEMINI_API_KEY provided'

    url = api_url or DEFAULT_API_URL
    # minimal body
    body = {'prompt': 'Test connectivity. Reply with {"ok":true}', 'max_output_tokens': 16}
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'}

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=timeout)
    except requests.RequestException as e:
        return False, f'Network error: {str(e)}'

    status = resp.status_code
    # try to parse JSON
    try:
        j = resp.json()
        # give a short summary
        return True, f'HTTP {status}, JSON response received (summary: {str(j)[:200]})'
    except Exception:
        text = resp.text
        # show a short snippet of the response to help diagnosis
        snippet = text[:500].replace('\n', ' ') if text else '<empty body>'
        # If we got 401/403/404, attempt a retry using the API key as a query parameter
        if status in (401, 403, 404):
            try:
                retry_url = f"{url}?key={key}"
                r2 = requests.post(retry_url, json=body, headers={'Content-Type': 'application/json'}, timeout=timeout)
                try:
                    j2 = r2.json()
                    return True, f'HTTP {r2.status_code} (retry with ?key=): JSON received (summary: {str(j2)[:200]})'
                except Exception:
                    txt2 = r2.text
                    sn2 = txt2[:500].replace('\n', ' ') if txt2 else '<empty body>'
                    return False, f'HTTP {r2.status_code} on retry with ?key= - non-JSON: {sn2}'
            except Exception as e:
                return False, f'HTTP {status}: {snippet} (retry with ?key= failed: {str(e)})'

        if 200 <= status < 300:
            return False, f'HTTP {status} but non-JSON response: {snippet}'
        return False, f'HTTP {status}: {snippet}'
