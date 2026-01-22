"""OpenAI API client for AI assessments and reviews.

This module provides functions to interact with OpenAI's API for generating
assessments and reviews of injection molding experiments.
"""

import os
import json
import requests
from typing import Optional, Dict, Any


def request_assessment(
    session,
    api_key: Optional[str] = None,
    timeout: int = 30,
    api_url: Optional[str] = None,
    model: Optional[str] = None,
    focus_step: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Request an assessment from OpenAI GPT-3.5/GPT-4.
    
    Returns a dict on success, or None on any failure.
    This function intentionally tolerates many failure modes since the UI
    wants to fall back to a local/mock AI behavior when OpenAI is unreachable.
    
    Args:
        session: The session object containing machine snapshot and test data.
        api_key: OpenAI API key. If not provided, will try environment variable.
        timeout: Request timeout in seconds (default 30).
    
    Returns:
        Dict with assessment keys like 'overall', 'conclusions', 'actions', 'risks'
        or None if the request fails.
    """
    key = api_key or os.getenv('OPENAI_API_KEY')
    if not key:
        # No API key configured - return mock response for immediate usability
        return _get_mock_assessment_response(session, focus_step)

    # Build prompt from session
    prompt = _build_prompt_from_session(session, focus_step=focus_step)

    # OpenAI-compatible endpoint (supports OpenAI / Deepseek, etc.)
    base_url = (
        (api_url or "").strip()
        or os.getenv('OPENAI_BASE_URL', '').strip()
        or os.getenv('OPENAI_API_BASE', '').strip()
        or "https://api.openai.com"
    ).rstrip('/')
    url = f"{base_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    # Request body
    # Choose a default model based on provider base URL when not explicitly set
    if model:
        chosen_model = model
    else:
        if 'deepseek' in base_url.lower():
            chosen_model = os.getenv('DEEPSEEK_MODEL') or os.getenv('OPENAI_MODEL', 'deepseek-chat')
        else:
            # gpt-3.5-turbo is frequently unavailable on newer OpenAI accounts;
            # use a safer modern default when OPENAI_MODEL isn't configured.
            chosen_model = os.getenv('OPENAI_MODEL') or 'gpt-4o-mini'

    body = {
        "model": chosen_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一名资深注塑工艺工程师。\n"
                    "请用中文输出严格 JSON，不要 Markdown。\n"
                    "点评必须基于证据，引用具体字段名与数值。\n"
                    "请遵循点评框架：\n"
                    "1) overall: 用一句话总结结果与结论（含关键数值）\n"
                    "2) conclusions: 3-5条结论，逐条引用字段名+数值\n"
                    "3) actions: 3-5条可执行动作，尽量量化\n"
                    "4) risks: 2-4条风险点，说明触发条件\n"
                    "5) missing_key_data: 缺失项列表（若无则空数组）\n"
                    "6) unreasonable_data_points: 不合理点列表（若无则空数组）\n"
                    "输出 JSON 必须包含键：overall, conclusions, actions, risks, missing_key_data, unreasonable_data_points。"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1500,
    }

    # Ask for strict JSON when the model is likely to support it.
    # (Some older models/providers may reject response_format.)
    try:
        if any(token in chosen_model.lower() for token in ("gpt-4", "gpt-4o", "gpt-4.1")):
            body["response_format"] = {"type": "json_object"}
    except Exception:
        pass

    try:
        # Configure proxy if available
        proxies = None
        if os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY') or os.getenv('ALL_PROXY'):
            proxies = {
                'http': os.getenv('HTTP_PROXY') or os.getenv('ALL_PROXY'),
                'https': os.getenv('HTTPS_PROXY') or os.getenv('ALL_PROXY'),
            }
            print(f"[OpenAI Client] Using proxy: {proxies}")

        req_timeout = timeout
        if 'deepseek' in base_url.lower() and not isinstance(timeout, tuple):
            # Use longer timeout for DeepSeek to handle slow responses
            req_timeout = (15, 45)
        
        resp = requests.post(url, json=body, headers=headers, timeout=req_timeout, proxies=proxies)
        print(f"[OpenAI Client] Response status: {resp.status_code} from {url}")
        if resp.status_code >= 400:
            print(f"[OpenAI Client] HTTP {resp.status_code} from {base_url}: {resp.text[:300]}")
            return None
        
        data = resp.json()
        print(f"[OpenAI Client] Response data keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        
        # Extract message content from response
        if "choices" in data and len(data["choices"]) > 0:
            message_content = data["choices"][0].get("message", {}).get("content", "")
            print(f"[OpenAI Client] Message content length: {len(message_content)}")
            print(f"[OpenAI Client] Message content preview: {message_content[:200]}")
            if message_content:
                try:
                    # Try to parse JSON response
                    parsed = json.loads(message_content)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    # If not JSON, try to extract JSON from text
                    import re
                    # Remove markdown code block markers
                    clean_content = re.sub(r'```\w*\n?', '', message_content)
                    print(f"[OpenAI Client] Cleaned content length: {len(clean_content)}")
                    print(f"[OpenAI Client] Cleaned content preview: {clean_content[:200]}")
                    try:
                        parsed = json.loads(clean_content)
                        if isinstance(parsed, dict):
                            return parsed
                    except json.JSONDecodeError as e:
                        print(f"[OpenAI Client] Direct JSON parse failed: {e}")
                        pass
                    
                    # Fallback: try to extract JSON with regex and handle truncated JSON
                    json_match = re.search(r'\{.*', clean_content, re.DOTALL)
                    print(f"[OpenAI Client] JSON match found: {json_match is not None}")
                    if json_match:
                        json_text = json_match.group()
                        print(f"[OpenAI Client] Extracted JSON length: {len(json_text)}")
                        try:
                            parsed = json.loads(json_text)
                            if isinstance(parsed, dict):
                                return parsed
                        except json.JSONDecodeError as e:
                            print(f"[OpenAI Client] JSON parse error: {e}")
                            # Try to fix truncated JSON by completing it
                            try:
                                # Find the last complete key-value pair and close the JSON
                                last_comma = json_text.rfind(',')
                                if last_comma > 0:
                                    # Find the opening brace of the last incomplete object/array
                                    incomplete_part = json_text[last_comma+1:].strip()
                                    if incomplete_part.startswith('"') and not incomplete_part.endswith('"'):
                                        # Incomplete string value
                                        fixed_json = json_text[:last_comma] + '}'
                                    elif incomplete_part.startswith('[') and not incomplete_part.endswith(']'):
                                        # Incomplete array
                                        fixed_json = json_text[:last_comma] + '}'
                                    elif incomplete_part.startswith('{') and not incomplete_part.endswith('}'):
                                        # Incomplete object
                                        fixed_json = json_text[:last_comma] + '}'
                                    else:
                                        # Try to close with missing keys
                                        fixed_json = json_text + '}'
                                    
                                    print(f"[OpenAI Client] Attempting to fix truncated JSON")
                                    parsed = json.loads(fixed_json)
                                    if isinstance(parsed, dict):
                                        print(f"[OpenAI Client] Successfully parsed fixed JSON")
                                        return parsed
                            except Exception as fix_e:
                                print(f"[OpenAI Client] Failed to fix truncated JSON: {fix_e}")
                                # Create a fallback response based on extracted text
                                try:
                                    fallback_response = {
                                        "overall": "AI响应解析失败，但API调用成功。以下是基于响应内容的分析。",
                                        "conclusions": ["API响应被截断，无法完整解析JSON"],
                                        "actions": ["检查网络连接和API配置"],
                                        "risks": ["可能存在数据传输问题"],
                                        "missing_key_data": [],
                                        "unreasonable_data_points": []
                                    }
                                    
                                    # Try to extract some useful information from the text
                                    if "machine_tonnage" in clean_content and "-100" in clean_content:
                                        fallback_response["unreasonable_data_points"].append({
                                            "step": "header",
                                            "field": "machine_tonnage", 
                                            "value": "-100",
                                            "why": "机器吨位不能为负值",
                                            "suggestion": "检查并修正机器吨位数据"
                                        })
                                    
                                    if "max_injection_pressure" in clean_content and "-50" in clean_content:
                                        fallback_response["unreasonable_data_points"].append({
                                            "step": "header",
                                            "field": "max_injection_pressure",
                                            "value": "-50", 
                                            "why": "最大注射压力不能为负值",
                                            "suggestion": "检查并修正注射压力数据"
                                        })
                                    
                                    if "数据缺失" in clean_content or "missing" in clean_content.lower():
                                        fallback_response["missing_key_data"].append({
                                            "step": str(focus_step or "multiple"),
                                            "field": "step_data",
                                            "label": "关键步骤数据",
                                            "why": "缺少必要的数据进行工艺分析",
                                            "how_to_get": "重新执行相应步骤并记录数据"
                                        })
                                    
                                    print(f"[OpenAI Client] Returning fallback response with extracted info")
                                    return fallback_response
                                except Exception as fallback_e:
                                    print(f"[OpenAI Client] Fallback response creation failed: {fallback_e}")
                                pass
        
        return None
    
    except Exception as e:
        print(f"[OpenAI Client] Request failed ({base_url}): {e}")
        # For DeepSeek, print more details
        if 'deepseek' in base_url.lower():
            print(f"[OpenAI Client] DeepSeek request failed with error: {e}")
        # For DeepSeek, don't return mock - let it fail so user knows
        if 'deepseek' in base_url.lower():
            return None
        # Return a meaningful mock response when API fails, so the app remains usable
        return _get_mock_assessment_response(session, focus_step)


def _get_mock_assessment_response(session, focus_step: Optional[int] = None) -> Dict[str, Any]:
    """Return a mock assessment response when API is unavailable.
    
    This provides immediate usability while showing that real AI is not available.
    """
    try:
        current_step = getattr(session, 'current_step', 0) or 0
        focus = focus_step if focus_step is not None else current_step
        
        step_names = {
            0: "准备阶段",
            1: "粘度曲线", 
            2: "型腔平衡",
            3: "压力降分析",
            4: "工艺窗口",
            5: "浇口冻结",
            6: "冷却时间",
            7: "锁模力验证"
        }
        
        step_name = step_names.get(focus, f"步骤{focus}")
        
        return {
            "overall": f"⚠️ AI分析不可用 - 显示演示数据 (聚焦: {step_name})",
            "conclusions": [
                f"当前聚焦{step_name}，数据分析功能暂时不可用",
                "建议检查网络连接或API配置",
                "应用正在使用演示模式以保证可用性"
            ],
            "actions": [
                "检查API密钥配置是否正确",
                "确认网络连接正常",
                "如需真实AI分析，请配置有效的API密钥"
            ],
            "risks": [
                "当前显示的是演示数据，不是真实的工程分析",
                "生产决策请谨慎，仅供参考"
            ],
            "missing_key_data": [
                {
                    "step": focus,
                    "field": "ai_analysis",
                    "label": "AI工程分析",
                    "why": "API服务暂时不可用，无法获取实时分析",
                    "how_to_get": "配置有效的OpenAI或Gemini API密钥"
                }
            ],
            "unreasonable_data_points": []
        }
    except Exception:
        # Fallback mock response
        return {
            "overall": "⚠️ AI分析服务不可用 - 演示模式",
            "conclusions": ["API服务暂时无法访问"],
            "actions": ["请检查网络和API配置"],
            "risks": ["当前为演示数据"],
            "missing_key_data": [],
            "unreasonable_data_points": []
        }
def _build_prompt_from_session(session, focus_step: Optional[int] = None) -> str:
    """Build a prompt summarizing the session for OpenAI.

    Only includes data relevant to the current focus_step to avoid AI confusion.
    """
    # Determine focus step
    focus = None
    try:
        if focus_step is not None:
            focus = int(focus_step)
        else:
            focus = int(getattr(session, 'current_step', 0) or 0)
    except Exception:
        focus = 0

    # Get machine snapshot (header info)
    try:
        snap = session.machine_snapshot
        header = {
            'part_name': getattr(snap, 'part_name', 'N/A') if snap else 'N/A',
            'mold_number': getattr(snap, 'mold_number', 'N/A') if snap else 'N/A',
            'machine_brand': getattr(snap, 'machine_brand', 'N/A') if snap else 'N/A',
            'machine_tonnage': getattr(snap, 'machine_tonnage', 'N/A') if snap else 'N/A',
            'material_type': getattr(snap, 'material_type', 'N/A') if snap else 'N/A',
            'screw_diameter': getattr(snap, 'screw_diameter', 'N/A') if snap else 'N/A',
            'max_injection_pressure': getattr(snap, 'max_injection_pressure', 'N/A') if snap else 'N/A',
            'max_holding_pressure': getattr(snap, 'max_holding_pressure', 'N/A') if snap else 'N/A',
            'part_no': getattr(snap, 'part_no', 'N/A') if snap else 'N/A',
            'supplier': getattr(snap, 'supplier', 'N/A') if snap else 'N/A',
            'owner': getattr(snap, 'owner', 'N/A') if snap else 'N/A',
            'vp_transfer_position': getattr(snap, 'vp_transfer_position', 'N/A') if snap else 'N/A',
            'cycle_time': getattr(snap, 'cycle_time', 'N/A') if snap else 'N/A',
        }
    except Exception:
        header = {}

    # Only get data for the CURRENT step - do not send all steps' data
    step_data = {}
    if focus == 0:
        step_data = {'step': 0, 'description': '机台与模具基础信息设置'}
    elif focus == 1:
        step_data = {
            'step': 1,
            'description': '粘度曲线分析',
            'viscosity_data_points': getattr(session, 'viscosity_data_points', None),
            'viscosity_inflection_point': getattr(session, 'viscosity_inflection_point', None),
            'optimal_injection_speed': getattr(session, 'optimal_injection_speed', None),
        }
    elif focus == 2:
        step_data = {
            'step': 2,
            'description': '型腔平衡测试',
            'cavity_weights_short': getattr(session, 'cavity_weights', None),
            'cavity_weights_full': getattr(session, 'cavity_weights_full', None),
            'balance_ratio': getattr(session, 'balance_ratio', None),
        }
    elif focus == 3:
        step_data = {
            'step': 3,
            'description': '压力降分析',
            'pressure_drop_data': getattr(session, 'pressure_drop_data', None),
            'pressure_margin': getattr(session, 'pressure_margin', None),
            'pressure_limited': getattr(session, 'pressure_limited', None),
        }
    elif focus == 4:
        step_data = {
            'step': 4,
            'description': '工艺窗口',
            'process_window_bounds': getattr(session, 'process_window_bounds', None),
            'process_window_data': getattr(session, 'process_window_data', None),
        }
    elif focus == 5:
        step_data = {
            'step': 5,
            'description': '浇口冻结',
            'gate_seal_curve': getattr(session, 'gate_seal_curve', None),
            'gate_freeze_time': getattr(session, 'gate_freeze_time', None),
        }
    elif focus == 6:
        step_data = {
            'step': 6,
            'description': '冷却时间',
            'cooling_curve': getattr(session, 'cooling_curve', None),
            'recommended_cooling_time': getattr(session, 'recommended_cooling_time', None),
        }
    elif focus == 7:
        step_data = {
            'step': 7,
            'description': '锁模力验证',
            'clamping_force_curve': getattr(session, 'clamping_force_curve', None),
            'recommended_clamping_force': getattr(session, 'recommended_clamping_force', None),
        }

    step_rubrics = {
        0: (
            "【步骤0 准备阶段/机台与材料信息】\n"
            "请仅基于 header 中的机台基础信息进行点评：\n"
            "- 核查机台能力参数是否完整（吨位、螺杆直径、最大注射压力、最大保压等）\n"
            "- 检查材料信息是否填写（材料类型）\n"
            "- 检查模具/产品信息是否填写（产品名、模号等）\n"
            "- 给出数据完整性评价和补录建议\n"
            "注意：此阶段只有基础设置信息，不要评价其他步骤的数据。"
        ),
        1: (
            "【步骤1 粘度曲线】\n"
            "请仅基于 step_data 中的粘度数据进行点评：\n"
            "- 数据点数量是否足够（至少3-5点）\n"
            "- 曲线趋势是否合理（粘度随速度变化）\n"
            "- 推荐的注射速度是否在合理区间\n"
            "注意：只评价粘度相关数据，不要评价其他步骤。"
        ),
        2: (
            "【步骤2 型腔平衡】\n"
            "请仅基于 step_data 中的型腔重量数据进行点评：\n"
            "- 各腔重量偏差是否在可接受范围（<5%）\n"
            "- 平衡度是否达标\n"
            "- 给出改善建议（如需要）\n"
            "注意：只评价型腔平衡数据，不要评价其他步骤。"
        ),
        3: (
            "【步骤3 压力降分析】\n"
            "请仅基于 step_data 中的压力数据进行点评：\n"
            "- 压力裕度是否充足\n"
            "- 是否存在压力受限风险\n"
            "注意：只评价压力相关数据，不要评价其他步骤。"
        ),
        4: (
            "【步骤4 工艺窗口】\n"
            "请仅基于 step_data 中的工艺窗口数据进行点评：\n"
            "- 窗口范围是否足够宽\n"
            "- 中心点设置是否合理\n"
            "注意：只评价工艺窗口数据，不要评价其他步骤。"
        ),
        5: (
            "【步骤5 浇口冻结】\n"
            "请仅基于 step_data 中的浇口冻结数据进行点评：\n"
            "- 冻结时间是否合理\n"
            "- 保压时间设置建议\n"
            "注意：只评价浇口冻结数据，不要评价其他步骤。"
        ),
        6: (
            "【步骤6 冷却时间】\n"
            "请仅基于 step_data 中的冷却数据进行点评：\n"
            "- 冷却时间是否充足\n"
            "- 周期优化建议\n"
            "注意：只评价冷却时间数据，不要评价其他步骤。"
        ),
        7: (
            "【步骤7 锁模力验证】\n"
            "请仅基于 step_data 中的锁模力数据进行点评：\n"
            "- 锁模力设置是否合理\n"
            "- 是否存在飞边风险\n"
            "注意：只评价锁模力数据，不要评价其他步骤。"
        ),
    }

    rubric_text = step_rubrics.get(focus, "请基于当前步骤数据给出工程判断。")

    step_names = {0: "准备阶段", 1: "粘度曲线", 2: "型腔平衡", 3: "压力降", 4: "工艺窗口", 5: "浇口冻结", 6: "冷却时间", 7: "锁模力"}
    step_name = step_names.get(focus, f"步骤{focus}")

    prompt = (
        f"请你基于以下【{step_name}】的注塑试验数据，生成中文工程点评（严格JSON格式）。\n\n"
        f"重要提示：你现在只需要评价【{step_name}】这一个步骤的数据，不要评价其他步骤！\n\n"
        f"{rubric_text}\n\n"
        "输出要求：\n"
        "1) JSON格式，顶层键：overall, conclusions, actions, risks, missing_key_data, unreasonable_data_points\n"
        "2) conclusions/actions/risks 用字符串数组\n"
        "3) missing_key_data: [{step, field, label, why, how_to_get}]，若无缺失返回空数组\n"
        "4) unreasonable_data_points: [{step, field, value, why, suggestion}]，若合理返回空数组\n"
        "5) 必须引用实际数据值作为依据\n\n"
        f"当前步骤: {focus} ({step_name})\n"
        f"机台基础信息: {json.dumps(header, ensure_ascii=False)}\n"
        f"当前步骤数据: {json.dumps(step_data, ensure_ascii=False)}\n"
    )
    return prompt



def test_key(api_key: Optional[str] = None, timeout: int = 8) -> tuple:
    """Test whether the provided API key can reach the OpenAI endpoint.

    Returns (success: bool, message: str).
    """
    key = api_key or os.getenv('OPENAI_API_KEY')
    if not key:
        return (False, "No API key provided")

    url = "https://api.openai.com/v1/models"
    headers = {
        "Authorization": f"Bearer {key}",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            return (True, "OpenAI API key is valid")
        elif resp.status_code == 401:
            return (False, "Invalid API key (401 Unauthorized)")
        else:
            return (False, f"HTTP {resp.status_code}: {resp.reason}")
    except requests.exceptions.Timeout:
        return (False, "Request timeout - check your network connection")
    except Exception as e:
        return (False, f"Error: {str(e)[:100]}")
