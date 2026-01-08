"""
SmartMold Pilot V3 - Main Application Entry Point
NiceGUI-based PWA with dark mode, routing, and database integration.
"""

import asyncio
from datetime import datetime
from nicegui import ui, app
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

# Load Frosted Glass Theme CSS (shared across all pages)
ui.add_head_html('<link rel="stylesheet" href="/static/frosted_glass_theme.css">', shared=True)


# ============================================================
# Application State
# ============================================================

app_state = {
    "db_initialized": False,
    "current_drawer": None,
}


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
    
    with glass_container():
        # Title
        with ui.row().classes("items-center gap-4 mb-4"):
            ui.label("Dashboard").classes(f"{GLASS_THEME['text_primary']} text-3xl font-bold")
            glass_button("Toggle Menu", lambda: drawer.toggle(), variant="secondary").classes("ml-auto")
        
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
# Page: Settings (Placeholder)
# ============================================================

@ui.page("/settings")
async def settings():
    """Settings page - Placeholder."""
    setup_glass_theme()
    
    # Create mesh gradient background (bottom layer)
    glass_background_layer()
    
    app_header()
    drawer = AppDrawer()
    
    with glass_container():
        with ui.row().classes("items-center gap-4 mb-4"):
            ui.label("Settings").classes(f"{GLASS_THEME['text_primary']} text-3xl font-bold")
            glass_button("Toggle Menu", lambda: drawer.toggle(), variant="secondary").classes("ml-auto")
        
        glass_alert("⚙️ Settings Page - Coming Soon", "info")


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
    print("[APP] Starting SmartMold Pilot V3...")
    print("[APP] Open browser at: http://localhost:9091")
    ui.run(
        title="SmartMold Pilot V3",
        dark=False,
        port=9091,
    )
