"""
SmartMold Pilot V3 - Main Application Entry Point
NiceGUI-based PWA with dark mode, routing, and database integration.
"""

import asyncio
import os
import warnings
import socket
from datetime import datetime
from nicegui import ui, app

from global_state import app_state, get_available_api_sync, get_available_api, switch_to_next_api
from ui_components import (
    setup_glass_theme,
    glass_background_layer,
    app_header,
    AppDrawer,
    glass_container,
    glass_card,
    glass_stat_card,
    glass_info_panel,
    glass_alert,
    glass_table,
    glass_button,
    glass_input,
    GLASS_THEME,
)
from db import init_db, close_db
from models import Machine, ExperimentSession, Mold


# Quiet common environment warning on macOS LibreSSL builds:
# urllib3 v2 emits NotOpenSSLWarning when the ssl module is compiled with LibreSSL.
warnings.filterwarnings('ignore', message=r"urllib3 v2 only supports OpenSSL.*")

# Load Frosted Glass Theme CSS (shared across all pages)
ui.add_head_html('<link rel="stylesheet" href="/static/frosted_glass_theme.css">', shared=True)


# ============================================================
# Database Initialization
# ============================================================

async def initialize_database():
    """Initialize database on app startup."""
    try:
        await init_db()
        app_state["db_initialized"] = True
        print("[APP] Database initialized successfully")
    except Exception as e:
        print(f"[APP] Database initialization error: {e}")
        app_state["db_initialized"] = False


# ============================================================
# Page: Dashboard
# ============================================================

@ui.page("/")
async def dashboard():
    """Dashboard - Home page with recent experiment records."""
    
    # Setup theme
    setup_glass_theme()
    
    # Create mesh gradient background (bottom layer)
    glass_background_layer()
    
    # Header
    app_header()
    
    # Drawer
    drawer = AppDrawer()
    app_state["current_drawer"] = drawer
    
    # Check if API is configured - if not, redirect to settings
    from global_state import get_available_api_sync
    current_api, api_key = get_available_api_sync()
    if not current_api or not api_key:
        print("[APP] No API configured, redirecting to settings...")
        ui.navigate.to("/settings")
        return
    
    with glass_container():
        # Title
        with ui.row().classes("items-center gap-4 mb-4"):
            ui.label("Dashboard").classes(f"{GLASS_THEME['text_primary']} text-3xl font-bold")
            glass_button("Toggle Menu", lambda: drawer.toggle(), variant="secondary").classes("ml-auto")
        
        # Check API configuration status
        from global_state import get_available_api_sync
        current_api, api_key = get_available_api_sync()
        if not current_api or not api_key:
            glass_alert(
                "⚠️ AI API 未配置\n\n"
                "请先配置有效的 API Key 以启用实时 AI 点评功能。",
                "warning"
            )
            with ui.row().classes("gap-2 mt-2"):
                glass_button("前往设置", lambda: ui.navigate.to("/settings"), variant="primary")
        
        # Database status alert
        if app_state["db_initialized"]:
            glass_alert("✓ Database connected successfully", "success")
        else:
            glass_alert("⚠ Database not initialized", "warning")
        
        # Statistics row
        with ui.row().classes("gap-4"):
            try:
                # Fetch from database
                machine_count = await Machine.all().count()
                mold_count = await Mold.all().count()
                session_count = await ExperimentSession.all().count()
                
                glass_stat_card("Machines", str(machine_count), "units", "build")
                glass_stat_card("Molds", str(mold_count), "units", "settings")
                glass_stat_card("Experiments", str(session_count), "sessions", "assessment")
            except Exception as e:
                print(f"[APP] Error fetching stats: {e}")
                glass_stat_card("Machines", "N/A", "", "error")
                glass_stat_card("Molds", "N/A", "", "error")
                glass_stat_card("Experiments", "N/A", "", "error")
        
        # Recent experiments section
        ui.label("Recent Experiments").classes(f"{GLASS_THEME['text_primary']} text-xl font-semibold mt-8 mb-4")
        
        try:
            # Fetch latest experiments
            experiments = await ExperimentSession.all().order_by("-created_at").limit(5)
            
            if experiments:
                # Prepare table data
                table_rows = []
                for exp in experiments:
                    machine = await exp.machine
                    mold = await exp.mold
                    table_rows.append([
                        exp.session_code,
                        machine.code,
                        mold.code,
                        exp.experiment_type.replace("_", " ").title(),
                        exp.status.upper(),
                        exp.created_at.strftime("%Y-%m-%d %H:%M"),
                    ])
                
                glass_table(
                    columns=["Session Code", "Machine", "Mold", "Type", "Status", "Created"],
                    rows=table_rows
                )
            else:
                glass_alert("No experiments found", "info")
        
        except Exception as e:
            print(f"[APP] Error fetching experiments: {e}")
            glass_alert(f"Error loading experiments: {str(e)}", "error")
        
        # Machine info section
        ui.label("Active Machine").classes("text-xl font-semibold text-cyan-400 mt-8 mb-4")
        
        try:
            machine = await Machine.get_or_none(code="TEST-MACHINE-001")
            if machine:
                glass_info_panel(
                    "TEST-MACHINE-001",
                    items=[
                        ("Brand", machine.brand),
                        ("Tonnage", f"{machine.tonnage}T"),
                        ("Screw Diameter", f"{machine.screw_diameter}mm"),
                        ("Max Pressure", f"{machine.max_pressure}MPa"),
                        ("Max Speed", f"{machine.max_speed}mm/s"),
                        ("Theoretical Weight", f"{machine.theoretical_injection_weight}g"),
                    ]
                )
            else:
                glass_alert("No machine data found", "warning")
        
        except Exception as e:
            print(f"[APP] Error fetching machine data: {e}")
            glass_alert(f"Error loading machine data: {str(e)}", "error")


# ============================================================
# Page: Scientific Molding - Seven-Step Workflow
# ============================================================

@ui.page("/scientific-molding")
async def scientific_molding():
    """Scientific Molding module - Seven-step sequential workflow with data inheritance."""
    from scientific_molding_6steps import SevenStepWizard
    from ui_components import setup_glass_theme, glass_background_layer, app_header, AppDrawer
    
    setup_glass_theme()
    glass_background_layer()
    app_header()
    drawer = AppDrawer()
    
    # Render the seven-step wizard
    wizard = SevenStepWizard()
    wizard.render()


# ============================================================
# Page: Machine Check (Performance Testing)
# ============================================================

@ui.page("/machine-check")
async def machine_check():
    """Machine Performance module - Weight repeatability & speed linearity testing."""
    from machine_performance import (
        MachineTestHistory,
        run_weight_repeatability_test,
        run_speed_linearity_test,
        run_pressure_consistency_test,
        generate_weight_trend_chart,
        generate_speed_linearity_chart,
        generate_pressure_distribution_chart,
        generate_test_summary_chart,
        generate_test_report,
    )
    
    setup_glass_theme()
    glass_background_layer()
    app_header()
    drawer = AppDrawer()
    
    # Initialize test history
    test_history = MachineTestHistory()
    
    # State for current tab
    test_state = {"current_test": "weight"}
    
    with glass_container():
        # Title
        with ui.row().classes("items-center gap-4 mb-6"):
            ui.label("机台性能测试").classes(f"{GLASS_THEME['text_primary']} text-3xl font-bold")
            glass_button("菜单", lambda: drawer.toggle(), variant="secondary").classes("ml-auto")
        
        # Test selection buttons
        test_buttons = {}
        
        with ui.row().classes("gap-2 mb-6 flex-wrap"):
            for test_name, test_label in [
                ("weight", "体重重复性"),
                ("speed", "速度线性性"),
                ("pressure", "压力一致性"),
                ("summary", "测试汇总"),
            ]:
                def on_test_click(test=test_name):
                    test_state["current_test"] = test
                    for btn_name, btn in test_buttons.items():
                        if btn_name == test:
                            btn.classes(add="bg-blue-600 text-white", remove="bg-white/30 text-slate-700")
                        else:
                            btn.classes(add="bg-white/30 text-slate-700", remove="bg-blue-600 text-white")
                
                btn = glass_button(test_label, on_test_click, variant="secondary")
                if test_name == "weight":
                    btn.classes(add="bg-blue-600 text-white")
                else:
                    btn.classes(add="bg-white/30 text-slate-700")
                test_buttons[test_name] = btn
        
        # ============ TEST 1: WEIGHT REPEATABILITY ============
        if test_state["current_test"] == "weight":
            with glass_card("体重重复性测试"):
                with ui.column().classes("gap-6"):
                    ui.label("测试配置").classes(f"{GLASS_THEME['text_primary']} font-semibold text-lg")
                    
                    with ui.row().classes("gap-4 flex-wrap"):
                        sample_count = glass_input("样品数量", "30")
                        target_weight = glass_input("目标体重 (g)", "10.0")
                    
                    result_label = ui.label("等待测试...").classes(f"{GLASS_THEME['text_secondary']}")
                    chart_container = ui.html("", sanitize=False).classes("w-full")
                    report_container = ui.html("", sanitize=False).classes("w-full")
                    
                    async def run_weight_test():
                        try:
                            count = int(sample_count.value)
                            target = float(target_weight.value)
                            
                            if count < 5 or count > 100:
                                result_label.set_text("✗ 样品数必须在 5-100 之间")
                                return
                            
                            # Run test
                            test_result = run_weight_repeatability_test(count, target)
                            
                            # Display result
                            status_emoji = "✓" if test_result["status"] == "PASS" else "✗"
                            result_label.set_text(
                                f"{status_emoji} {test_result['status']}\n"
                                f"重复性: {test_result['repeatability_percentage']:.2f}%\n"
                                f"平均体重: {test_result['mean_weight']:.2f}g | 标准差: {test_result['std_dev']:.4f}\n"
                                f"范围: {test_result['min_weight']:.2f}g - {test_result['max_weight']:.2f}g"
                            )
                            result_label.classes(add="text-emerald-600" if test_result["status"] == "PASS" else "text-red-600")
                            
                            # Generate charts
                            chart_html = generate_weight_trend_chart(test_result['weights'], target)
                            chart_container.content = chart_html
                            
                            # Generate report
                            report_html = generate_test_report(test_result)
                            report_container.content = report_html
                            
                            # Save to history
                            test_history.add_test_result(
                                test_type="Weight Repeatability",
                                status=test_result["status"],
                                results=test_result
                            )
                        except ValueError as e:
                            result_label.set_text(f"✗ 输入错误: {str(e)}")
                            result_label.classes(add="text-red-600")
                    
                    glass_button("运行测试", run_weight_test)
        
        # ============ TEST 2: SPEED LINEARITY ============
        elif test_state["current_test"] == "speed":
            with glass_card("速度线性性测试"):
                with ui.column().classes("gap-6"):
                    ui.label("测试配置").classes(f"{GLASS_THEME['text_primary']} font-semibold text-lg")
                    
                    with ui.row().classes("gap-4 flex-wrap"):
                        test_levels = glass_input("测试速度等级 (逗号分隔 %)", "20,30,40,50,60,70,80,90,100")
                    
                    result_label = ui.label("等待测试...").classes(f"{GLASS_THEME['text_secondary']}")
                    chart_container = ui.html("", sanitize=False).classes("w-full")
                    report_container = ui.html("", sanitize=False).classes("w-full")
                    
                    async def run_speed_test():
                        try:
                            levels = [float(x.strip()) for x in test_levels.value.split(",")]
                            
                            if not all(0 < l <= 100 for l in levels):
                                result_label.set_text("✗ 速度等级必须在 0-100% 之间")
                                return
                            
                            # Run test
                            test_result = run_speed_linearity_test(levels)
                            
                            # Display result
                            status_emoji = "✓" if test_result["status"] == "PASS" else "✗"
                            result_label.set_text(
                                f"{status_emoji} {test_result['status']}\n"
                                f"线性性指数 (R²): {test_result['r_squared']:.4f}\n"
                                f"线性性评分: {test_result['linearity_index']:.2f}%\n"
                                f"斜率: {test_result['slope']:.4f} | 截距: {test_result['intercept']:.4f}"
                            )
                            result_label.classes(add="text-emerald-600" if test_result["status"] == "PASS" else "text-red-600")
                            
                            # Generate chart
                            chart_html = generate_speed_linearity_chart(
                                test_result['speed_levels'],
                                test_result['actual_speeds'],
                                test_result['theoretical_speeds']
                            )
                            chart_container.content = chart_html
                            
                            # Generate report
                            report_html = generate_test_report(test_result)
                            report_container.content = report_html
                            
                            # Save to history
                            test_history.add_test_result(
                                test_type="Speed Linearity",
                                status=test_result["status"],
                                results=test_result
                            )
                        except ValueError as e:
                            result_label.set_text(f"✗ 输入错误: {str(e)}")
                            result_label.classes(add="text-red-600")
                    
                    glass_button("运行测试", run_speed_test)
        
        # ============ TEST 3: PRESSURE CONSISTENCY ============
        elif test_state["current_test"] == "pressure":
            with glass_card("压力一致性测试"):
                with ui.column().classes("gap-6"):
                    ui.label("测试配置").classes(f"{GLASS_THEME['text_primary']} font-semibold text-lg")
                    
                    with ui.row().classes("gap-4 flex-wrap"):
                        cycle_count = glass_input("测试周期数", "20")
                        target_pressure = glass_input("目标压力 (MPa)", "50.0")
                    
                    result_label = ui.label("等待测试...").classes(f"{GLASS_THEME['text_secondary']}")
                    chart_container = ui.html("", sanitize=False).classes("w-full")
                    report_container = ui.html("", sanitize=False).classes("w-full")
                    
                    async def run_pressure_test():
                        try:
                            cycles = int(cycle_count.value)
                            target = float(target_pressure.value)
                            
                            if cycles < 5 or cycles > 100:
                                result_label.set_text("✗ 周期数必须在 5-100 之间")
                                return
                            
                            # Run test
                            test_result = run_pressure_consistency_test(None, target)
                            test_result['cycle_count'] = cycles  # Override with user input
                            
                            # Display result
                            status_emoji = "✓" if test_result["status"] == "PASS" else "✗"
                            result_label.set_text(
                                f"{status_emoji} {test_result['status']}\n"
                                f"一致性: {test_result['consistency_percentage']:.2f}%\n"
                                f"平均压力: {test_result['mean_pressure']:.2f} MPa | 标准差: {test_result['std_dev']:.4f}\n"
                                f"范围: {test_result['min_pressure']:.2f} - {test_result['max_pressure']:.2f} MPa"
                            )
                            result_label.classes(add="text-emerald-600" if test_result["status"] == "PASS" else "text-red-600")
                            
                            # Generate chart
                            chart_html = generate_pressure_distribution_chart(test_result['measurements'], target)
                            chart_container.content = chart_html
                            
                            # Generate report
                            report_html = generate_test_report(test_result)
                            report_container.content = report_html
                            
                            # Save to history
                            test_history.add_test_result(
                                test_type="Pressure Consistency",
                                status=test_result["status"],
                                results=test_result
                            )
                        except ValueError as e:
                            result_label.set_text(f"✗ 输入错误: {str(e)}")
                            result_label.classes(add="text-red-600")
                    
                    glass_button("运行测试", run_pressure_test)
        
        # ============ TEST 4: SUMMARY ============
        else:  # summary
            with glass_card("测试汇总"):
                with ui.column().classes("gap-6"):
                    ui.label("测试历史与统计").classes(f"{GLASS_THEME['text_primary']} font-semibold text-lg")
                    
                    # Summary chart
                    summary_chart = ui.html("", sanitize=False).classes("w-full")
                    
                    # Statistics
                    weight_pass_rate = test_history.get_pass_rate("Weight Repeatability")
                    speed_pass_rate = test_history.get_pass_rate("Speed Linearity")
                    pressure_pass_rate = test_history.get_pass_rate("Pressure Consistency")
                    
                    with ui.row().classes("gap-4 flex-wrap"):
                        glass_stat_card("体重通过率", f"{weight_pass_rate:.1f}%", "%", "check_circle" if weight_pass_rate >= 90 else "warning")
                        glass_stat_card("速度通过率", f"{speed_pass_rate:.1f}%", "%", "check_circle" if speed_pass_rate >= 90 else "warning")
                        glass_stat_card("压力通过率", f"{pressure_pass_rate:.1f}%", "%", "check_circle" if pressure_pass_rate >= 90 else "warning")
                    
                    # Recent tests table
                    recent_tests = test_history.get_recent_tests(5)
                    if recent_tests:
                        glass_table("machine_tests", [
                            ("时间", lambda r: r.get('timestamp', '')[:19]),
                            ("测试类型", lambda r: r.get('test_type', '')),
                            ("结果", lambda r: r.get('status', ''))
                        ], recent_tests)


        with glass_card("Test Categories"):
            with ui.column().classes("gap-3"):
                tests = [
                    "• 注射油压压力测试 (Oil Pressure Check)",
                    "• 注射速度测试 (Injection Speed Check)",
                    "• 射出重量测试 (Injection Weight Check)",
                    "• 动态止逆环测试 (Dynamic Check Ring Test)",
                    "• 静态止逆环测试 (Static Check Ring Test)",
                ]
                for test in tests:
                    ui.label(test).classes(f"{GLASS_THEME['text_primary']}")


# ============================================================
# Page: Settings (API Configuration)
# ============================================================

@ui.page("/settings")
async def settings():
    """Settings page - API Key Management with failover."""
    setup_glass_theme()
    
    # Create mesh gradient background (bottom layer)
    glass_background_layer()
    
    app_header()
    drawer = AppDrawer()
    
    with glass_container():
        with ui.row().classes("items-center gap-4 mb-4"):
            ui.label("⚙️ 配置 API Key").classes(f"{GLASS_THEME['text_primary']} text-3xl font-bold")
            glass_button("Toggle Menu", lambda: drawer.toggle(), variant="secondary").classes("ml-auto")
        
        # Show current API error if any
        if app_state["api_error_message"]:
            glass_alert(f"✗ {app_state['api_error_message']}", "error")
        
        # Current API status
        current_api_display = ui.label(
            f"当前 API: {app_state['current_api'].upper() if app_state['current_api'] else '未选择'}"
        ).classes(f"{GLASS_THEME['text_primary']} text-lg font-semibold mb-4")
        
        # API Key Configuration
        with glass_card("🔑 配置 API Key"):
            ui.label("为不同模型提供商贴上 API key，输入时为密码样式。点击对应的'测试'按钮验证可用性。").classes(f"{GLASS_THEME['text_secondary']} text-sm mb-4")

            # OpenAI model selection (used by Scientific Molding realtime comments)
            openai_model_input = glass_input(
                "OpenAI Model（用于实时点评）",
                placeholder="例如: gpt-4o-mini / gpt-4.1-mini",
                value=os.getenv('OPENAI_MODEL') or 'gpt-4o-mini',
            ).classes('mb-2')
            ui.label("提示：如果 API 测试通过但实时点评失败，通常是模型名不可用；请在此调整模型再测试。")\
                .classes(f"{GLASS_THEME['text_secondary']} text-xs mb-4")
            
            # API Test Results Storage
            api_test_results = {}
            last_ok_provider = {"name": None}
            
            # Function to test API
            def test_api(api_name, api_key):
                if not api_key.strip():
                    return "❌ Please enter an API Key"
                
                try:
                    import requests
                    
                    # Configure proxy if available
                    proxies = None
                    if os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY'):
                        proxies = {
                            'http': os.getenv('HTTP_PROXY'),
                            'https': os.getenv('HTTPS_PROXY'),
                        }
                    
                    if api_name == "openai":
                        headers = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        }
                        # Test the same endpoint used by realtime comments to avoid “models ok but chat fails”.
                        model_name = (openai_model_input.value or '').strip() or (os.getenv('OPENAI_MODEL') or 'gpt-4o-mini')
                        body = {
                            "model": model_name,
                            "messages": [{"role": "user", "content": "ping"}],
                            "max_tokens": 5,
                            "temperature": 0,
                        }
                        resp = requests.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers=headers,
                            json=body,
                            timeout=12,
                            proxies=proxies,
                        )
                        if resp.status_code == 200:
                            # Apply immediately for current process
                            os.environ['OPENAI_MODEL'] = model_name
                            return f"✓ OpenAI API 有效（模型: {model_name}）"
                        if resp.status_code == 401:
                            return "✗ OpenAI returned HTTP 401: Invalid API key"
                        return f"✗ OpenAI chat test failed (HTTP {resp.status_code}): {resp.text[:120]}"
                    
                    elif api_name == "gemini":
                        # Test using the same SDK that will be used for actual requests
                        try:
                            from google import genai
                            client = genai.Client(api_key=api_key) if api_key else genai.Client()
                            # Try a simple generation request similar to what we'll do
                            resp = client.models.generate_content(
                                model="gemini-2.0-flash",
                                contents="Test ping",
                                max_output_tokens=10,
                            )
                            # Check if we got a response
                            if hasattr(resp, 'text') and resp.text:
                                return "✓ Gemini API 有效"
                            elif hasattr(resp, 'output') and resp.output:
                                return "✓ Gemini API 有效"
                            else:
                                return "✓ Gemini API 有效"
                        except Exception as e:
                            error_msg = str(e)
                            if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
                                return "✗ Gemini API key 无效"
                            elif "PERMISSION_DENIED" in error_msg:
                                return "✗ Gemini API 权限不足"
                            else:
                                return f"✗ Gemini 测试失败: {error_msg[:100]}"
                    
                    elif api_name == "claude":
                        headers = {
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        }
                        resp = requests.get(
                            "https://api.anthropic.com/v1/models",
                            headers=headers,
                            timeout=8,
                            proxies=proxies,
                        )
                        if resp.status_code == 200:
                            return "✓ Claude API 有效"
                        elif resp.status_code == 401:
                            return "✗ Claude API key invalid"
                        else:
                            return f"✗ Claude test failed (HTTP {resp.status_code})"
                    
                    elif api_name == "deepseek":
                        headers = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        }
                        # Test with chat completions endpoint like OpenAI
                        body = {
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": "ping"}],
                            "max_tokens": 5,
                        }
                        resp = requests.post(
                            "https://api.deepseek.com/v1/chat/completions",
                            headers=headers,
                            json=body,
                            timeout=8,
                            proxies=proxies,
                        )
                        if resp.status_code == 200:
                            return "✓ Deepseek API 有效"
                        elif resp.status_code == 401:
                            return "✗ Deepseek API key invalid"
                        else:
                            return f"✗ Deepseek test failed (HTTP {resp.status_code})"
                    
                except Exception as e:
                    return f"✗ Connection error: {str(e)[:60]}"
            
            # Create API input sections
            api_configs = {
                "gemini": "Gemini API Key",
                "openai": "OpenAI API Key",
                "claude": "Claude API Key",
                "deepseek": "Deepseek API Key",
            }
            
            api_inputs = {}
            api_status_labels = {}
            
            for api_name, api_label in api_configs.items():
                with ui.row().classes("gap-3 items-end mb-4"):
                    # API Key input
                    api_input = glass_input(
                        api_label,
                        placeholder=f"{api_label}...",
                        value=app_state["api_keys"].get(api_name, "")
                    )
                    api_input.props("type=password")
                    api_inputs[api_name] = api_input

                    async def paste_from_clipboard(inp=api_input):
                        try:
                            text = await ui.run_javascript("navigator.clipboard.readText()", timeout=5.0)
                            if text:
                                inp.set_value(text)
                                ui.notify("✓ 已从剪贴板粘贴", type="positive")
                            else:
                                ui.notify("剪贴板为空或无法读取", type="warning")
                        except Exception as e:
                            ui.notify("无法读取剪贴板，请允许权限或用 Cmd+V 粘贴", type="negative")
                    api_input.on("contextmenu", paste_from_clipboard)
                    
                    # Test button
                    status_label = ui.label("").classes(f"{GLASS_THEME['text_secondary']} text-sm")
                    api_status_labels[api_name] = status_label
                    
                    def create_test_handler(name, inp, label):
                        async def test_handler():
                            label.set_text("⏳ Testing...")
                            label.classes(remove="text-red-600 text-emerald-600", add=f"{GLASS_THEME['text_secondary']}")
                            key_val = inp.value.strip() if inp.value else ""
                            result = await asyncio.to_thread(test_api, name, key_val)
                            label.set_text(result)
                            if "✓" in result:
                                label.classes(remove=f"{GLASS_THEME['text_secondary']} text-red-600", add="text-emerald-600")
                                api_test_results[name] = True
                                last_ok_provider["name"] = name

                                # Apply immediately - always use the API that was just tested successfully
                                if key_val:
                                    app_state["api_keys"][name] = key_val
                                    app_state["current_api"] = name  # Always switch to tested API
                                    app_state["last_tested_ok_api"] = name  # Track last successful test
                                    current_api_display.set_text(f"当前 API: {name.upper()}")
                                    print(f"[API Config] Switched to {name.upper()} after successful test")
                            else:
                                label.classes(remove=f"{GLASS_THEME['text_secondary']} text-emerald-600", add="text-red-600")
                                api_test_results[name] = False
                        return test_handler
                    
                    glass_button("测试", create_test_handler(api_name, api_input, status_label))
            
            # Save to .env option (persist on save)
            with ui.row().classes("gap-2 mt-4 items-center"):
                save_to_env_checkbox = ui.checkbox("保存到 .env 文件（仅开发机，谨慎）")

            # Save configuration
            def save_api_config():
                # Save all API keys
                for api_name, inp in api_inputs.items():
                    app_state["api_keys"][api_name] = inp.value.strip() if inp.value else None
                
                # Determine priority order based on valid APIs (preserve configured priority)
                valid_apis = [name for name in app_state.get("api_priority_order", []) if app_state["api_keys"].get(name)]

                # If the user just tested a provider successfully, prefer it as current.
                preferred = last_ok_provider.get("name")
                if preferred and preferred in valid_apis:
                    app_state["current_api"] = preferred
                    # Keep failover order but move the preferred provider to the front.
                    valid_apis = [preferred] + [x for x in valid_apis if x != preferred]
                elif valid_apis:
                    app_state["current_api"] = valid_apis[0]
                else:
                    app_state["current_api"] = None

                app_state["api_priority_order"] = valid_apis

                if valid_apis:
                    current_api_display.set_text(f"当前 API: {app_state['current_api'].upper()}")
                    ui.notify("✓ API 配置已保存！当前使用: " + app_state["current_api"].upper(), type="positive")

                    # Apply OpenAI model selection immediately
                    try:
                        model_name = (openai_model_input.value or '').strip()
                        if model_name:
                            os.environ['OPENAI_MODEL'] = model_name
                    except Exception:
                        pass

                    # Auto-navigate back to dashboard after successful configuration
                    ui.timer(2.0, lambda: ui.navigate.to("/"), once=True)

                    # Persist to .env if requested
                    if save_to_env_checkbox.value:
                        try:
                            env_lines = []
                            for api_name in api_configs.keys():
                                key_val = app_state["api_keys"].get(api_name)
                                if key_val:
                                    env_lines.append(f"{api_name.upper()}_API_KEY={key_val}")

                            # Persist OpenAI model (optional)
                            model_name = (openai_model_input.value or '').strip()
                            if model_name:
                                env_lines.append(f"OPENAI_MODEL={model_name}")

                            env_lines.append(f"SELECTED_API_PROVIDER={app_state['current_api']}")
                            env_lines.append(f"SELECTED_API_KEY={app_state['api_keys'].get(app_state['current_api'], '')}")
                            with open(os.path.join(os.path.dirname(__file__), '.env'), 'w', encoding='utf-8') as f:
                                f.write("\n".join(env_lines) + "\n")
                            ui.notify("✓ 配置已保存至 .env", type="positive")
                        except Exception as e:
                            ui.notify(f"✗ 保存至 .env 失败: {str(e)}", type="negative")
                else:
                    app_state["current_api"] = None
                    ui.notify("⚠️ 请至少配置一个有效的 API", type="warning")
            
            with ui.row().classes("gap-3 mt-6"):
                glass_button("确认并使用所选", save_api_config)
                glass_button(
                    "使用 MOCK AI",
                    lambda: (
                        app_state.update({"current_api": "mock"}),
                        current_api_display.set_text("当前 API: MOCK"),
                        ui.notify("✓ 已切换至 MOCK AI", type="positive")
                    ),
                    variant="secondary"
                )
            
            # Tip: testing only validates connectivity; click "确认并使用所选" to apply.
        
        # API Failover Information
        with glass_card("ℹ️ API 自动故障转移"):
            ui.label("当前配置的 API 将按以下优先级使用：").classes(f"{GLASS_THEME['text_primary']} font-semibold mb-3")
            
            with ui.column().classes("ml-4 gap-1"):
                priority_num = 1
                for api in app_state["api_priority_order"]:
                    if app_state["api_keys"].get(api):
                        ui.label(f"{priority_num}. {api.upper()} (已配置)").classes(f"{GLASS_THEME['text_primary']}")
                        priority_num += 1
                if priority_num == 1:
                    ui.label("暂无配置的 API").classes(f"{GLASS_THEME['text_secondary']}")
            
            ui.label("如果当前 API 发生错误，系统会自动切换到下一个可用的 API，并在界面顶部显示错误提示。").classes(f"{GLASS_THEME['text_secondary']} text-sm mt-3")


# ============================================================
# Page: About (Placeholder)
# ============================================================

@ui.page("/about")
async def about():
    """About page - Placeholder."""
    setup_glass_theme()
    
    # Create mesh gradient background (bottom layer)
    glass_background_layer()
    
    app_header()
    drawer = AppDrawer()
    
    with glass_container():
        with ui.row().classes("items-center gap-4 mb-4"):
            ui.label("About").classes(f"{GLASS_THEME['text_primary']} text-3xl font-bold")
            glass_button("Toggle Menu", lambda: drawer.toggle(), variant="secondary").classes("ml-auto")
        
        glass_info_panel(
            "SmartMold Pilot V3",
            items=[
                ("Version", "3.0.0"),
                ("Build Date", datetime.now().strftime("%Y-%m-%d")),
                ("Tech Stack", "NiceGUI + Tortoise-ORM + Plotly"),
                ("License", "Proprietary"),
                ("Author", "SmartMold Team"),
            ]
        )


# ============================================================
# Application Startup & Shutdown
# ============================================================

# Configure static files for CSS theme
import os
static_dir = os.path.join(os.path.dirname(__file__), 'static')
os.makedirs(static_dir, exist_ok=True)

# Copy CSS to static folder if needed
import shutil
css_source = os.path.join(os.path.dirname(__file__), 'frosted_glass_theme.css')
css_dest = os.path.join(static_dir, 'frosted_glass_theme.css')
if os.path.exists(css_source) and not os.path.exists(css_dest):
    shutil.copy(css_source, css_dest)

app.add_static_files('/static', static_dir)

app.on_startup(lambda: asyncio.create_task(initialize_database()))
app.on_shutdown(lambda: asyncio.create_task(close_db()))


# ============================================================
# Run Application
# ============================================================

if __name__ in {"__main__", "__mp_main__"}:
    def find_available_port(preferred: int = 9091, span: int = 10) -> int:
        """Find an available port starting from preferred, cycling within range.

        Args:
            preferred: Starting port to try.
            span: Number of ports to try consecutively.
        """
        for offset in range(span):
            candidate = preferred + offset
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("0.0.0.0", candidate))
                    return candidate
                except OSError:
                    continue
        # If none free, fall back to preferred
        return preferred

    chosen_port = find_available_port(9091, span=10)
    if chosen_port != 9091:
        print(f"[APP] Port 9091 busy, switched to {chosen_port}")
    print("[APP] Starting SmartMold Pilot V3...")
    print(f"[APP] Open browser at: http://localhost:{chosen_port}")
    ui.run(
        title="SmartMold Pilot V3",
        dark=False,
        port=chosen_port,
        show=True,
    )
    
