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


def _build_prompt_from_session(session, focus_step: Optional[int] = None) -> str:
    """Create a Chinese prompt summarizing the session for Gemini.

    Includes raw step data and unreasonable notes so the model can point to specific
    data points when marking them as unreasonable.
    """
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

    step_status = {}
    step_remarks = {}
    try:
        for i in range(0, 8):
            step_status[str(i)] = {
                'skipped': bool(getattr(session, 'step_skipped', {}).get(i, False)),
                'quality': 'OK' if getattr(session, 'step_data_quality', {}).get(i, True) else 'NG',
            }
        step_remarks = getattr(session, 'step_remarks', {}) or {}
    except Exception:
        pass

    step_data = {
        'step1_viscosity_data_points': getattr(session, 'viscosity_data_points', None),
        'step1_inflection': getattr(session, 'viscosity_inflection_point', None),
        'step2_cavity_weights_short': getattr(session, 'cavity_weights', None),
        'step2_cavity_weights_full': getattr(session, 'cavity_weights_full', None),
        'step3_pressure_drop_data': getattr(session, 'pressure_drop_data', None),
        'step3_pressure_margin': getattr(session, 'pressure_margin', None),
        'step3_pressure_limited': getattr(session, 'pressure_limited', None),
        'step4_process_window_bounds': getattr(session, 'process_window_bounds', None),
        'step4_process_window_data': getattr(session, 'process_window_data', None),
        'step5_gate_seal_curve': getattr(session, 'gate_seal_curve', None),
        'step5_gate_freeze_time': getattr(session, 'gate_freeze_time', None),
        'step6_cooling_curve': getattr(session, 'cooling_curve', None),
        'step6_recommended_cooling_time': getattr(session, 'recommended_cooling_time', None),
        'step7_clamping_force_curve': getattr(session, 'clamping_force_curve', None),
        'step7_recommended_clamping_force': getattr(session, 'recommended_clamping_force', None),
    }

    focus = None
    try:
        if focus_step is not None:
            focus = int(focus_step)
        else:
            focus = int(getattr(session, 'current_step', 0) or 0)
    except Exception:
        focus = None

    step_rubrics = {
        0: (
            "【准备阶段/机台与材料信息】核查机台能力与上限参数是否足以支撑后续7步："
            "max_injection_pressure/max_holding_pressure、machine_tonnage、screw_diameter、vp_transfer_position、cycle_time。"
            "缺失项必须列入 missing_key_data 并解释导致哪些判断无法做。"
        ),
        1: (
            "【步骤1 粘度曲线】检查数据点数量（至少3点）与趋势一致性；结合 step1_inflection 给出推荐注射速度与对后续步骤影响。"
            "合理时不要逐条点评每点，但必须引用1~2个代表性数值/拐点作证据。"
        ),
        2: (
            "【步骤2 型腔平衡】基于短射/满射每穴重量判断平衡性，给出是否需要修模的明确结论。"
            "不合理时逐条点名偏差最大的穴位与重量值。"
        ),
        3: (
            "【步骤3 压力降】基于 pressure_drop_data/pressure_margin 判断压力受限与裕度，并指出最大压损段（若数据提供）。"
            "缺 pressure_drop_data 或机台最大注射压力必须列入 missing_key_data。"
        ),
        4: (
            "【步骤4 工艺窗口】基于 process_window_data/process_window_bounds 判断窗口宽度与中心点合理性，并给出量产控制上下限建议。"
            "点数/数据缺失必须列入 missing_key_data。"
        ),
        5: (
            "【步骤5 浇口冻结】基于 gate_seal_curve/gate_freeze_time 给出最小保压时间与安全裕量；缺失则列入 missing_key_data。"
        ),
        6: (
            "【步骤6 冷却时间】基于 cooling_curve/recommended_cooling_time 判断稳定点，给出周期与翘曲风险建议；缺失则列入 missing_key_data。"
        ),
        7: (
            "【步骤7 锁模力】基于 clamping_force_curve/recommended_clamping_force 与 machine_tonnage（若有）校核飞边风险与锁模裕度；缺失则列入 missing_key_data。"
        ),
    }

    rubric_text = step_rubrics.get(focus, "【综合点评】请基于所有步骤数据给出工程判断，并避免空泛结论。")

    framework = (
        "【点评框架】请严格输出 JSON（不要 Markdown），必须包含键："
        "overall, conclusions, actions, risks, missing_key_data, unreasonable_data_points。\n"
        "- overall: 一句话总结（含关键数值）\n"
        "- conclusions: 3-5条结论，逐条引用字段名+数值\n"
        "- actions: 3-5条可执行动作，尽量量化\n"
        "- risks: 2-4条风险点，说明触发条件\n"
        "- missing_key_data: 缺失项数组（无则空数组）\n"
        "- unreasonable_data_points: 不合理点数组（无则空数组）\n"
    )

    prompt = (
        "请你基于以下注塑试验信息，生成中文工程点评（严格 JSON）。\n"
        "要求：对合理与不合理数据都要点评。\n"
        "严禁使用空泛套话，必须基于证据（引用提供的字段名与数值，或明确指出缺失）。\n"
        "规则：合理数据只给总体评价/结论/建议动作/风险提示，不要逐条点评每个数据点，且 unreasonable_data_points 必须为空数组。\n"
        "但如果存在‘关键数据缺失/关键字段为空/数据不完整’，必须在 missing_key_data 中逐条列出到底缺哪些数据（字段/名称要具体），并说明每项用途与建议如何补测/补录，不要泛泛而谈。\n"
        "若不合理必须逐条点名不合理的数据点，包含原始值与字段/位置。不要编造不存在的数据点。\n"
        "只允许输出 JSON，不要 Markdown。\n"
        "顶层键必须包含：overall, conclusions, actions, risks, missing_key_data, unreasonable_data_points。\n"
        "missing_key_data 为对象数组：[{step, field, label, why, how_to_get}]；无缺失则返回空数组。\n"
        "unreasonable_data_points 为对象数组：[{step, field, value, why, suggestion}]；整体合理时必须返回空数组。\n\n"
        "额外要求：conclusions/actions/risks 至少各给出2条（除非因为数据缺失无法判断，此时应在 missing_key_data 写清楚）。\n\n"
        f"{rubric_text}\n\n"
        f"当前聚焦步骤 focus_step={focus}\n"
        f"基础信息 header={json.dumps(header, ensure_ascii=False)}\n"
        f"步骤状态 step_status={json.dumps(step_status, ensure_ascii=False)}\n"
        f"不合理备注 step_remarks={json.dumps(step_remarks, ensure_ascii=False)}\n"
        f"原始数据 step_data={json.dumps(step_data, ensure_ascii=False)}\n"
    )
    return prompt + "\n\n" + framework + "\n\n" + rubric_text


def request_assessment(
    session,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    timeout: int = 30,
    focus_step: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Request an assessment from Gemini. Returns a dict on success, or None on any failure.

    This function intentionally tolerates many failure modes since the UI
    wants to fall back to a local/mock AI behavior when Gemini is unreachable.
    """
    key = api_key or os.getenv('GEMINI_API_KEY')
    if not key:
        print("[Gemini Client] No API key provided")
        return None

    url = api_url or DEFAULT_API_URL

    prompt = _build_prompt_from_session(session, focus_step=focus_step)

    # If the official SDK is available, use it (prefer SDK for auth/compatibility).
    if _HAS_GENAI_SDK:
        try:
            client = genai.Client(api_key=api_key) if api_key else genai.Client()
            # Use a valid Gemini model name
            model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
            print(f"[Gemini Client] Using SDK with model: {model_name}")
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
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
                        print(f"[Gemini Client] SDK request succeeded")
                        return parsed
                except Exception as parse_err:
                    print(f"[Gemini Client] SDK response parse failed: {parse_err}")
                    return None
        except Exception as sdk_err:
            # fall through to HTTP path
            print(f"[Gemini Client] SDK request failed: {sdk_err}")
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
