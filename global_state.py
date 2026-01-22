"""Shared application state.

This module exists to avoid importing `main.py` from other modules.
When `main.py` is executed as a script, its module name is `__main__`,
so importing `main` elsewhere can create a second copy of state.

All pages and workflow modules should read/write shared API selection
through this module.
"""

from __future__ import annotations

import os
from typing import Optional, Tuple


def _load_dotenv_file(dotenv_path: str) -> None:
    """Minimal .env loader (no external deps).

    Loads KEY=VALUE pairs into os.environ if the key is not already set.
    Supports quoted values and ignores blank lines/comments.
    """
    try:
        if not os.path.exists(dotenv_path):
            return
        with open(dotenv_path, 'r', encoding='utf-8') as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        print(f"[ENV] Failed to load .env: {e}")


# Load .env early so app_state can pick it up
_load_dotenv_file(os.path.join(os.path.dirname(__file__), '.env'))


def _is_demo_key(api_key: Optional[str]) -> bool:
    if not api_key:
        return False
    key_lower = api_key.lower()
    demo_markers = (
        "sk-demo-",
        "demo-",
        "testing-only",
        "for-testing-purposes-only",
    )
    return any(marker in key_lower for marker in demo_markers)


app_state = {
    "db_initialized": False,
    "current_drawer": None,
    "api_keys": {
        "gemini": None,
        "openai": None,
        "claude": None,
        "deepseek": None,
    },
    "api_priority_order": ["deepseek", "openai", "gemini", "claude"],  # DeepSeek first (accessible in China)
    "current_api": None,
    "api_error_message": None,
    "last_tested_ok_api": None,  # Track which API was last tested successfully
}


# Hydrate API keys from environment variables (supports .env loaded above)
for _provider in ("gemini", "openai", "claude", "deepseek"):
    env_key_name = f"{_provider.upper()}_API_KEY"
    env_val = os.getenv(env_key_name)
    if env_val:
        app_state["api_keys"][_provider] = env_val

# Set demo API keys if none configured (for immediate usability)
if not any(app_state["api_keys"].values()):
    print("[APP] No API keys configured, setting demo keys for immediate use...")
    # These are demo keys - replace with real ones for production
    app_state["api_keys"]["deepseek"] = "sk-demo-deepseek-key-for-testing-purposes-only"
    app_state["api_keys"]["openai"] = "sk-demo-openai-key-for-testing-purposes-only"
    app_state["api_keys"]["gemini"] = "demo-gemini-api-key-for-testing-only"


# If user specified a selected provider, prefer it
_selected_provider = (os.getenv("SELECTED_API_PROVIDER") or "").strip().lower()
if _selected_provider and _selected_provider in app_state["api_keys"]:
    if app_state["api_keys"].get(_selected_provider):
        app_state["current_api"] = _selected_provider
else:
    for _p in app_state.get("api_priority_order", []):
        if app_state["api_keys"].get(_p):
            app_state["current_api"] = _p
            break


def get_available_api_sync() -> Tuple[Optional[str], Optional[str]]:
    """Get the currently available API (sync), with failover.

    Returns: (api_name, api_key) or (None, None) when none configured.

    Priority order:
    1. openai - prefer OpenAI for stability (DeepSeek often times out)
    2. last_tested_ok_api - the API that was most recently tested successfully
    3. current_api - the currently selected API
    4. api_priority_order - fallback to configured priority
    """
    # Prefer OpenAI for stability (DeepSeek often times out in China)
    openai_key = app_state.get("api_keys", {}).get("openai")
    if openai_key and not _is_demo_key(openai_key):
        return "openai", openai_key

    # First priority: use the last successfully tested API
    last_tested = app_state.get("last_tested_ok_api")
    if last_tested and last_tested != "mock":
        api_key = app_state["api_keys"].get(last_tested)
        if api_key and not _is_demo_key(api_key):
            return last_tested, api_key

    # Second priority: use current_api
    if app_state.get("current_api") and app_state["current_api"] != "mock":
        api_key = app_state["api_keys"].get(app_state["current_api"])
        if api_key and not _is_demo_key(api_key):
            return app_state["current_api"], api_key

    # Fallback: try APIs in priority order
    for api_name in app_state.get("api_priority_order", []):
        api_key = app_state["api_keys"].get(api_name)
        if api_key and not _is_demo_key(api_key):
            return api_name, api_key

    return None, None


async def get_available_api():
    return get_available_api_sync()


def switch_to_next_api(failed_api_name: str) -> Optional[str]:
    """Switch to the next available API when current provider fails."""
    available_apis = [
        name
        for name in app_state.get("api_priority_order", [])
        if app_state["api_keys"].get(name)
    ]

    try:
        current_idx = available_apis.index(failed_api_name)
        next_api = available_apis[(current_idx + 1) % len(available_apis)]
        app_state["current_api"] = next_api
        return next_api
    except (ValueError, IndexError):
        if available_apis:
            app_state["current_api"] = available_apis[0]
            return available_apis[0]
        app_state["current_api"] = None
        return None
