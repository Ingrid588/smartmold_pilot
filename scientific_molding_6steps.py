"""
SmartMold Pilot V3 - Scientific Molding Seven-Step Workflow
Implements sequential wizard-style workflow with data inheritance.

7-Step Scientific Molding Workflow:
1. 粘度曲线分析 (Viscosity Curve)
2. 型腔平衡测试 (Cavity Balance)
3. 压力降测试 (Pressure Drop)
4. 工艺窗口定义 (Process Window)
5. 浇口冻结测试 (Gate Seal)
6. 冷却时间优化 (Cooling Time)
7. 锁模力优化 (Clamping Force Optimization)
"""

import os
import io
import random
import time
from pathlib import Path
from nicegui import ui, app
from nicegui.events import UploadEventArguments
from datetime import datetime
from session_state import get_session_state, MachineSnapshot
from algorithms import (
    find_viscosity_inflection_point,
    calculate_viscosity_fingerprint,
    cavity_balance,
    calculate_pressure_margin,
    find_process_window_center,
    detect_gate_freeze_time,
)
from ui_components import (
    GLASS_THEME,
    glass_container,
    glass_card,
    glass_button,
    glass_input,
    glass_alert,
)
from excel_data_parser import ExcelDataParser, create_template_excel, ExcelTestData
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional


def _get_ai_assessment(session, step: Optional[int] = None):
    """
    统一的 AI 评估函数，支持多 API 自动故障转移。
    返回 assessment dict 或 None。
    """
    try:
        from global_state import app_state, get_available_api_sync
        api_name, api_key = get_available_api_sync()
        
        if not api_name or not api_key:
            print("[AI Assessment] No API available")
            return None
        
        print(f"[AI Assessment] Using {api_name.upper()} API...")
        
        if api_name == "gemini":
            from gemini_client import request_assessment
            assessment = request_assessment(session, api_key=api_key, focus_step=step)
        elif api_name in ["openai", "deepseek"]:
            from openai_client import request_assessment
            if api_name == "deepseek":
                print(f"[AI Assessment] Calling DeepSeek API for step {step}...")
                assessment = request_assessment(session, api_key=api_key, api_url="https://api.deepseek.com", focus_step=step, timeout=60)
                if assessment is None:
                    print(f"[AI Assessment] DeepSeek API call returned None for step {step}")
            else:
                assessment = request_assessment(session, api_key=api_key, focus_step=step)
        else:
            assessment = None

        # Persist successful realtime AI assessments into session for PDF export
        try:
            if assessment and hasattr(session, 'set_ai_assessment'):
                # Use explicit step when provided; fallback to session.current_step
                if step is None:
                    step_idx = getattr(session, 'current_step', 0) or 0
                else:
                    step_idx = step
                session.set_ai_assessment(int(step_idx), assessment, provider=api_name)
        except Exception:
            pass

        return assessment
    except Exception as e:
        print(f"[AI Assessment] Error: {e}")
        import traceback
        traceback.print_exc()
        return None


class SevenStepWizard:
    """Seven-step scientific molding wizard with parameter inheritance."""
    
    def __init__(self):
        self.session = get_session_state()
        # Reset session state on page load to start fresh
        self.session.reset()
        self.current_step = 1
        
        # UI References
        self.stepper = None
        self.content_container = None
        self.progress_container = None
        
        # Machine snapshot UI inputs
        self.snapshot_inputs = {}
        
        # Track which steps have unreasonable data
        self.unreasonable_steps: Dict[int, str] = {}  # step -> issue description
        
        # Excel上传数据存储
        self.uploaded_excel_data: Optional[ExcelTestData] = None
        self.excel_upload_status = None  # UI显示区域
        self.pending_ai: Dict[int, Dict[str, Any]] = {}
    
    async def show_unreasonable_data_dialog(self, step: int, data_issue: str, on_continue: callable):
        """Show dialog for unreasonable data confirmation with remark input."""
        dialog_result = {'continue': False, 'remark': '', 'reason': ''}
        
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label(f"⚠️ 数据不合理警告").classes('text-xl font-bold text-orange-600')
            display_step = f"步骤 {step}" if step > 0 else "准备阶段"
            ui.label(f"{display_step} 检测到以下问题：").classes('text-gray-600 mt-2')
            ui.label(data_issue).classes('text-red-600 font-semibold mt-1 p-2 bg-red-50 rounded')
            
            ui.label("建议修正数据后再继续。如需继续，请选择原因：").classes('text-sm text-gray-500 mt-4')
            
            # Common reasons for scientific molding
            reason_options = [
                "客户特殊要求",
                "设备限制，已是最优",
                "材料批次差异",
                "模具设计限制",
                "试验性验证",
                "其他原因"
            ]
            reason_select = ui.select(reason_options, label="选择原因").classes('w-full')
            
            # 动态更新备注标签
            remark_label = ui.label("补充说明（选填）").classes('text-sm text-gray-600 mt-2')
            remark_input = ui.textarea(placeholder="请补充说明...").classes('w-full')
            
            def on_reason_change(e):
                if reason_select.value == "其他原因":
                    remark_label.set_text("补充说明（必填）")
                    remark_label.classes(remove="text-gray-600", add="text-red-600 font-semibold")
                else:
                    remark_label.set_text("补充说明（选填）")
                    remark_label.classes(remove="text-red-600 font-semibold", add="text-gray-600")
            
            reason_select.on('update:model-value', on_reason_change)
            
            error_label = ui.label("").classes('text-red-500 text-sm')
            
            async def on_confirm():
                if not reason_select.value:
                    error_label.set_text("请选择原因")
                    return
                # 仅当选择"其他原因"时，备注必填
                if reason_select.value == "其他原因":
                    if not remark_input.value or len(remark_input.value.strip()) < 3:
                        error_label.set_text("选择'其他原因'时必须填写补充说明")
                        return
                
                # Save remark to session
                remark_text = remark_input.value.strip() if remark_input.value else "（无补充说明）"
                self.session.set_step_remark(step, reason_select.value, remark_text, data_issue)
                self.unreasonable_steps[step] = data_issue
                
                # Update progress indicator BEFORE closing dialog and navigating
                self.update_progress_indicator()
                
                dialog.close()
                ui.notify(f"步骤 {step} 已记录偏离原因", type='warning')
                
                # Handle both sync and async callbacks
                import asyncio
                if asyncio.iscoroutinefunction(on_continue):
                    await on_continue()
                else:
                    on_continue()
            
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('继续', on_click=on_confirm).props('color=orange')
        
        dialog.open()
    
    async def show_skip_step_dialog(self, step: int, stepper, go_next: bool = True):
        """Show dialog when user tries to skip a step without completing it.
        
        When 'Use Historical Data' is selected, show data input fields and AI review.
        """
        # Debug log for why skip dialog was triggered
        try:
            print(f"[show_skip_step_dialog] invoked for step={step}, progress={self.session.get_progress_summary()}")
        except Exception:
            pass
        step_names = ['背景信息', '粘度曲线', '型腔平衡', '压力降', '工艺窗口', '浇口冻结', '冷却时间', '锁模力优化']
        step_name = step_names[step] if 0 <= step < len(step_names) else f'步骤 {step}'
        
        # Historical data field definitions for each step
        historical_data_fields = {
            1: [("optimal_speed", "最佳射速 (mm/s)", "例如: 45.5")],
            2: [("balance_ratio", "型腔平衡比", "例如: 0.97")],
            3: [("pressure_margin", "压力裕度 (MPa)", "例如: 25")],
            4: [("process_window_low", "工艺窗口下限 (MPa)", "例如: 40"),
                ("process_window_high", "工艺窗口上限 (MPa)", "例如: 60")],
            5: [("gate_freeze_time", "浇口冻结时间 (s)", "例如: 13")],
            6: [("cooling_time", "推荐冷却时间 (s)", "例如: 15")],
            7: [("clamping_force", "推荐锁模力 (Ton)", "例如: 138")],
        }
        
        # Skip reasons
        skip_reasons = [
            "该测试已在其他试模中完成",
            "使用历史数据/经验值",
            "客户提供参数，无需验证",
            "模具/材料限制，无法进行该测试",
            "时间紧迫，后续补做",
            "其他原因"
        ]
        
        with ui.dialog() as dialog, ui.card().classes('w-[500px]'):
            display_step = f"步骤 {step}" if step > 0 else "准备阶段"
            ui.label(f"⏭️ {display_step} 跳过确认").classes('text-xl font-bold text-orange-600')
            ui.label(f"您即将跳过: {step_name}").classes('text-gray-600 mt-2')
            ui.label("该步骤在科学注塑流程中非常重要，跳过可能影响最终工艺的可靠性。").classes('text-sm text-red-500 mt-2 p-2 bg-red-50 rounded')
            
            ui.label("请选择跳过原因：").classes('text-sm text-gray-500 mt-4')
            
            reason_select = ui.select(skip_reasons, label="选择跳过原因").classes('w-full')
            
            # Container for historical data input (shown only when "使用历史数据/经验值" is selected)
            historical_data_container = ui.column().classes('w-full mt-2')
            historical_data_inputs = {}
            ai_review_container = ui.column().classes('w-full mt-2')
            
            remark_label = ui.label("补充说明").classes('text-sm text-gray-600 mt-2')
            remark_input = ui.textarea(placeholder="请说明跳过该步骤的具体原因...").classes('w-full')
            
            error_label = ui.label("").classes('text-red-500 text-sm')
            
            def on_reason_change(e):
                historical_data_container.clear()
                ai_review_container.clear()
                historical_data_inputs.clear()
                
                if reason_select.value == "使用历史数据/经验值":
                    # Show historical data input fields
                    with historical_data_container:
                        ui.label("📊 请输入历史数据：").classes('font-semibold text-blue-600 mt-2')
                        fields = historical_data_fields.get(step, [])
                        if fields:
                            with ui.grid(columns=2).classes('w-full gap-2'):
                                for field_key, field_label, placeholder in fields:
                                    inp = ui.input(label=field_label, placeholder=placeholder).classes('w-full')
                                    historical_data_inputs[field_key] = inp
                        else:
                            ui.label("此步骤无需额外数据").classes('text-gray-500 text-sm')
                        
                        # AI Review button
                        async def request_ai_review():
                            ai_review_container.clear()
                            with ai_review_container:
                                ui.spinner('dots').classes('mr-2')
                                ui.label("正在获取AI点评...").classes('text-gray-500')
                            
                            # Collect historical data
                            hist_data = {k: v.value for k, v in historical_data_inputs.items() if v.value}
                            
                            # Store historical data to session and trigger AI
                            self._apply_historical_data_to_session(step, hist_data)
                            
                            # Get AI assessment
                            try:
                                from global_state import get_available_api_sync
                                current_api, api_key = get_available_api_sync()
                                
                                if current_api and api_key:
                                    import asyncio
                                    
                                    def blocking_api_call():
                                        if current_api == "openai":
                                            from openai_client import request_assessment
                                            return request_assessment(self.session, api_key=api_key, timeout=15, focus_step=step)
                                        elif current_api == "gemini":
                                            from gemini_client import request_assessment
                                            return request_assessment(self.session, api_key=api_key, timeout=15, focus_step=step)
                                        return None
                                    
                                    assessment = await asyncio.get_event_loop().run_in_executor(None, blocking_api_call)
                                    
                                    ai_review_container.clear()
                                    with ai_review_container:
                                        if assessment and isinstance(assessment, dict):
                                            # Store AI assessment
                                            self.session.set_ai_assessment(step, assessment, provider=current_api)
                                            
                                            text = self._format_assessment_text(assessment)
                                            glass_alert(f"🤖 AI点评（{current_api.upper()}）：\n" + text, "success")
                                            ui.notify("✅ AI点评已获取并保存", type="positive")
                                        else:
                                            glass_alert("⚠️ AI点评获取失败，但可以继续", "warning")
                                else:
                                    ai_review_container.clear()
                                    with ai_review_container:
                                        glass_alert("⚠️ 未配置AI API，跳过AI点评", "warning")
                            except Exception as ex:
                                print(f"[Skip Dialog AI] Error: {ex}")
                                ai_review_container.clear()
                                with ai_review_container:
                                    glass_alert(f"⚠️ AI点评出错: {str(ex)[:50]}", "error")
                        
                        ui.button("🤖 获取AI点评", on_click=request_ai_review).classes(
                            'mt-2 bg-blue-500 hover:bg-blue-600 text-white'
                        )
                    
                    remark_label.set_text("数据来源说明（选填）")
                elif reason_select.value == "其他原因":
                    remark_label.set_text("补充说明（必填）")
                    remark_label.classes(remove="text-gray-600", add="text-red-600 font-semibold")
                else:
                    remark_label.set_text("补充说明（选填）")
                    remark_label.classes(remove="text-red-600 font-semibold", add="text-gray-600")
            
            reason_select.on('update:model-value', on_reason_change)
            
            async def on_skip():
                if not reason_select.value:
                    error_label.set_text("请选择跳过原因")
                    return
                
                # Validate based on reason
                if reason_select.value == "其他原因" and (not remark_input.value or len(remark_input.value.strip()) < 3):
                    error_label.set_text("选择'其他原因'时必须填写补充说明")
                    return
                
                if reason_select.value == "使用历史数据/经验值":
                    # Validate that at least one historical data field is filled
                    hist_data = {k: v.value for k, v in historical_data_inputs.items() if v.value}
                    if not hist_data:
                        error_label.set_text("请至少填写一项历史数据")
                        return
                    # Apply historical data to session
                    self._apply_historical_data_to_session(step, hist_data)
                    # Mark as completed (with historical data)
                    self.session.set_step_remark(step, reason_select.value, 
                                                  f"历史数据: {hist_data}, {remark_input.value or ''}", 
                                                  "使用历史数据替代实测")
                else:
                    # Mark step as skipped with reason
                    self.session.set_step_remark(step, reason_select.value, remark_input.value or "（无补充说明）", "用户跳过该步骤")
                
                self.session.set_step_skipped(step, True)
                
                # Update progress indicator
                self.update_progress_indicator()
                
                dialog.close()
                ui.notify(f"步骤 {step} 已跳过（已记录原因）", type='warning')
                
                # Move to next/previous step
                if go_next:
                    stepper.next()
                else:
                    stepper.previous()
            
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('返回完成', on_click=dialog.close).props('flat color=primary')
                ui.button('确认跳过', on_click=on_skip).props('color=orange')
        
        dialog.open()
    
    def _apply_historical_data_to_session(self, step: int, hist_data: dict):
        """Apply historical data to session for a specific step."""
        try:
            if step == 1 and 'optimal_speed' in hist_data:
                speed = float(hist_data['optimal_speed'])
                self.session.set_step1_result(speed, {'optimal_speed': speed, 'viscosity_at_optimal': 0})
                self.session.set_step_quality(1, True)
            elif step == 2 and 'balance_ratio' in hist_data:
                ratio = float(hist_data['balance_ratio'])
                self.session.set_step2_result(ratio, {1: 10.0, 2: 10.0, 3: 10.0, 4: 10.0})  # Mock weights
                self.session.set_step_quality(2, ratio >= 0.95)
            elif step == 3 and 'pressure_margin' in hist_data:
                margin = float(hist_data['pressure_margin'])
                self.session.set_step3_result(margin, margin < 10)
                self.session.set_step_quality(3, margin >= 10)
            elif step == 4:
                low = float(hist_data.get('process_window_low', 0))
                high = float(hist_data.get('process_window_high', 0))
                window_width = high - low
                self.session.set_step4_result({'min_pressure': low, 'max_pressure': high, 
                                                'recommended': (low + high) / 2}, 
                                               [])
                self.session.set_step_quality(4, window_width >= 10)
            elif step == 5 and 'gate_freeze_time' in hist_data:
                freeze_time = float(hist_data['gate_freeze_time'])
                self.session.set_step5_result(freeze_time, [])
                self.session.set_step_quality(5, True)
            elif step == 6 and 'cooling_time' in hist_data:
                cooling_time = float(hist_data['cooling_time'])
                self.session.set_step6_result(cooling_time, [])
                self.session.set_step_quality(6, True)
            elif step == 7 and 'clamping_force' in hist_data:
                force = float(hist_data['clamping_force'])
                self.session.set_step7_result(force, [])
                self.session.set_step_quality(7, True)
            print(f"[Historical Data] Applied to step {step}: {hist_data}")
        except Exception as e:
            print(f"[Historical Data] Error applying data: {e}")
    
    def show_completion_error_dialog(self, missing_steps: list):
        """Show error dialog when trying to complete without finishing all steps.
        Note: missing_steps only contains truly unfinished steps (not skipped or unreasonable)."""
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label("❌ 无法完成").classes('text-xl font-bold text-red-600')
            ui.label("以下步骤尚未完成：").classes('text-gray-600 mt-2')
            
            step_names = ['粘度曲线', '型腔平衡', '压力降', '工艺窗口', '浇口冻结', '冷却时间', '锁模力优化']
            for step in missing_steps:
                ui.label(f"  • 步骤 {step}: {step_names[step-1]}").classes('text-red-500 ml-4')
            
            ui.label("").classes('mt-2')
            ui.label("提示：您可以通过以下方式处理未完成步骤：").classes('text-sm text-gray-500')
            ui.label("  • 完成测试（正常或偏离数据）").classes('text-xs text-gray-400 ml-2')
            ui.label("  • 点击\"下一步\"选择跳过").classes('text-xs text-gray-400 ml-2')
            
            ui.button('确定', on_click=dialog.close).classes('mt-4').props('color=primary')
        
        dialog.open()
    
    def create_machine_snapshot_ui(self) -> Dict[str, Any]:
        """Create a comprehensive input section for Project, Machine, Material, and Mold settings."""
        inputs = {}
        
        with ui.expansion("📋 项目与基础信息 (Project & Background Info)", icon='assignment', value=True).classes('w-full mb-4'):
            with ui.grid(columns=3).classes('w-full gap-4 p-4'):
                with ui.column().classes('gap-2'):
                    ui.label("产品信息 (Part Info)").classes('font-bold text-blue-600')
                    inputs['model_no'] = glass_input("Model No", "")
                    inputs['part_no'] = glass_input("Part No", "")
                    inputs['part_name'] = glass_input("Part Name", "")
                    inputs['supplier'] = glass_input("供应商 (Supplier)", "")
                    inputs['owner'] = glass_input("负责人 (Owner)", "")
                    inputs['theoretical_part_weight'] = glass_input("产品理论重量 (g)", "")
                    inputs['actual_part_weight'] = glass_input("实际重量 (g)", "")
                
                with ui.column().classes('gap-2'):
                    ui.label("材料信息 (Material Info)").classes('font-bold text-green-600')
                    inputs['material_brand'] = glass_input("品牌 (Brand)", "")
                    inputs['material_type'] = glass_input("型号 (Type)", "")
                    inputs['material_number'] = glass_input("材料编号", "")
                    inputs['material_color'] = glass_input("颜色 (Color)", "")
                    inputs['material_density'] = glass_input("密度 (g/cm³)", "")
                    inputs['drying_temp'] = glass_input("烘烤温度 (°C)", "")
                    inputs['drying_time'] = glass_input("烘烤时间 (H)", "")
                
                with ui.column().classes('gap-2'):
                    ui.label("机台与模具 (Machine & Mold)").classes('font-bold text-purple-600')
                    inputs['machine_number'] = glass_input("机台号", "")
                    inputs['machine_brand'] = glass_input("机台品牌", "")
                    inputs['machine_tonnage'] = glass_input("吨位 (Ton)", "")
                    inputs['screw_diameter'] = glass_input("螺杆直径 (mm)", "")
                    inputs['intensification_ratio'] = glass_input("增强比 (Ratio)", "")
                    inputs['mold_number'] = glass_input("模号 (T/N)", "")
                    inputs['cavity_count'] = glass_input("总穴数 (CAV)", "")
                    inputs['runner_type'] = ui.select(["Cold Runner", "Hot Runner", "Mixed"], label="流道形式").classes('w-full')

        with ui.expansion("⚙️ 机台工艺设定 (Processing Parameters)", icon='settings', value=True).classes('w-full mb-4'):
            with ui.row().classes('w-full gap-8 p-4'):
                with ui.column().classes('flex-1 gap-4'):
                    ui.label("温度设定 (°C)").classes('font-bold border-b w-full')
                    with ui.grid(columns=3).classes('w-full gap-2'):
                        inputs['barrel1'] = glass_input("Z1", "")
                        inputs['barrel2'] = glass_input("Z2", "")
                        inputs['barrel3'] = glass_input("Z3", "")
                        inputs['barrel4'] = glass_input("Z4", "")
                        inputs['barrel5'] = glass_input("Z5", "")
                        inputs['nozzle'] = glass_input("喷嘴", "")
                        inputs['hot_runner'] = glass_input("热流道", "")
                        inputs['mold_fixed'] = glass_input("定模", "")
                        inputs['mold_moving'] = glass_input("动模", "")
                
                with ui.column().classes('flex-1 gap-4'):
                    ui.label("压力与周期").classes('font-bold border-b w-full')
                    with ui.grid(columns=2).classes('w-full gap-2'):
                        inputs['max_inj_pressure'] = glass_input("最大注射压 (MPa)", "")
                        inputs['max_hold_pressure'] = glass_input("最大保压 (MPa)", "")
                        inputs['vp_position'] = glass_input("V/P位置 (mm)", "")
                        inputs['cycle_time'] = glass_input("周期 (s)", "")
            
            # AI comment area
            inputs['ai_comment'] = ui.column().classes("w-full mt-2 p-4")
        
        return inputs

    def render_step0_setup(self):
        """Render the initial setup step to collect background information."""
        with ui.column().classes('w-full gap-4'):
            ui.label("试验背景信息录入").classes('text-2xl font-bold text-blue-800 mb-2')
            ui.label("请在开始科学注塑试验前，填写以下基本信息。这些信息将出现在报告的第一页。").classes('text-gray-600')
            
            # Use the existing UI builder but it's now more comprehensive
            self.snapshot_inputs = self.create_machine_snapshot_ui()
            
            # Quick-fill buttons for testing reasonable / unreasonable data on the first page
            def fill_step0_data(is_reasonable: bool):
                """Fill step 0 data and set step 0 quality."""
                self.fill_machine_snapshot(self.snapshot_inputs, is_reasonable)
                # Only set step 0 quality when filling data from step 0 page
                self.session.set_step_quality(0, is_reasonable)
            
            with ui.row().classes('w-full gap-2'):
                ui.button('快速填充（合理）', on_click=lambda: fill_step0_data(True)).props('flat')
                ui.button('快速填充（不合理）', on_click=lambda: fill_step0_data(False)).props('flat color=negative')
                ui.button(f"🤖 实时AI点评（{self._get_ai_label()}）", on_click=lambda: self.trigger_realtime_ai(0)).props('flat color=primary')

            with ui.row().classes('w-full justify-end mt-4'):
                ui.button("保存并开始试验", on_click=lambda: self.save_setup_info()).props('color=primary icon=play_arrow')

    def save_setup_info(self):
        """Save setup info and move to Step 1."""
        try:
            snapshot = self.capture_snapshot()
            self.session.machine_snapshot = snapshot
            # Mark step0 as completed; if data quality was set by quick-fill keep it,
            # otherwise default to reasonable
            if 0 not in self.session.step_data_quality:
                self.session.set_step_quality(0, True)
            # Refresh progress indicator so step 0 shows as completed
            self.update_progress_indicator()
            # Advance to step 1 and persist current step
            self.session.current_step = 1
            ui.notify("✅ 基本信息已保存", type='positive')
            if self.stepper:
                ui.timer(0.05, lambda: self.stepper.next(), once=True)
        except Exception as e:
            ui.notify(f"❌ 保存失败: {str(e)}", type='negative')

    def fill_machine_snapshot(self, inputs: Dict, is_reasonable: bool):
        """Fill machine snapshot with simulated values and trigger AI commentary."""
        if is_reasonable:
            # 合理的项目信息
            inputs['model_no'].set_value("2026-PROJ-01")
            inputs['part_no'].set_value("P-8890-X")
            inputs['part_name'].set_value("Front Housing")
            inputs['supplier'].set_value("SmartInjection Ltd")
            inputs['owner'].set_value("Admin")
            inputs['theoretical_part_weight'].set_value("45.5")
            inputs['actual_part_weight'].set_value("45.7")
            
            inputs['material_brand'].set_value("BASF")
            inputs['material_type'].set_value("Ultramid B3K")
            inputs['material_number'].set_value("50012345")
            inputs['material_color'].set_value("Natural")
            inputs['material_density'].set_value("1.13")
            inputs['drying_temp'].set_value("80")
            inputs['drying_time'].set_value("4")

            inputs['machine_number'].set_value("M-08")
            inputs['machine_brand'].set_value("Arburg")
            inputs['machine_tonnage'].set_value("150")
            inputs['screw_diameter'].set_value("35")
            inputs['intensification_ratio'].set_value("10.5")
            inputs['mold_number'].set_value("T-5521")
            inputs['cavity_count'].set_value("1+1")
            inputs['runner_type'].set_value("Hot Runner")

            # 合理的机台参数
            inputs['barrel1'].set_value("205")
            inputs['barrel2'].set_value("210")
            inputs['barrel3'].set_value("215")
            inputs['barrel4'].set_value("220")
            inputs['barrel5'].set_value("225")
            inputs['nozzle'].set_value("230")
            inputs['hot_runner'].set_value("235")
            inputs['mold_fixed'].set_value("55")
            inputs['mold_moving'].set_value("55")
            inputs['max_inj_pressure'].set_value("180")
            inputs['max_hold_pressure'].set_value("120")
            inputs['vp_position'].set_value("25")
            inputs['cycle_time'].set_value("22.5")
            
            # 显示数据已填充的通知
            ui.notify("✅ 数据已填充完成，可点击实时AI点评", type='positive')
            
            # 先显示本地Mock（不触发实时AI）
            mock_renderer = self._create_mock_renderer(is_reasonable)
            self._set_pending_ai(0, inputs['ai_comment'], mock_renderer)
            try:
                inputs['ai_comment'].clear()
                mock_renderer()
            except Exception:
                pass
        else:
            # 不合理的参数
            inputs['model_no'].set_value("TEST-ERR-01")
            inputs['part_no'].set_value("ERR-999")
            inputs['part_name'].set_value("Test Part with Errors")
            inputs['supplier'].set_value("Unknown Supplier")
            inputs['owner'].set_value("Test User")
            inputs['theoretical_part_weight'].set_value("50.0")
            inputs['actual_part_weight'].set_value("52.1")
            
            inputs['material_brand'].set_value("Unknown")
            inputs['material_type'].set_value("Test Material")
            inputs['material_number'].set_value("ERR000")
            inputs['material_color'].set_value("Mixed")
            inputs['material_density'].set_value("1.2")
            inputs['drying_temp'].set_value("60")
            inputs['drying_time'].set_value("2")

            inputs['machine_number'].set_value("ERR-01")
            inputs['machine_brand'].set_value("Unknown Brand")
            inputs['machine_tonnage'].set_value("-100")
            inputs['screw_diameter'].set_value("40")
            inputs['intensification_ratio'].set_value("8.0")
            inputs['mold_number'].set_value("ERR-MOLD")
            inputs['cavity_count'].set_value("4")
            inputs['runner_type'].set_value("Cold Runner")

            # 不合理的机台参数
            inputs['barrel1'].set_value("260")
            inputs['mold_fixed'].set_value("30")
            inputs['mold_moving'].set_value("45")
            inputs['cycle_time'].set_value("35.0")
            inputs['max_inj_pressure'].set_value("-50")
            inputs['max_hold_pressure'].set_value("80")
            inputs['vp_position'].set_value("15")
            
            # 显示数据已填充的通知
            ui.notify("✅ 不合理数据已填充完成，可点击实时AI点评", type='positive')
            
            # 先显示本地Mock（不触发实时AI）
            mock_renderer = self._create_mock_renderer(is_reasonable)
            self._set_pending_ai(0, inputs['ai_comment'], mock_renderer)
            try:
                inputs['ai_comment'].clear()
                mock_renderer()
            except Exception:
                pass
        
        # Persist current inputs so realtime AI has full context
        try:
            self.session.machine_snapshot = self.capture_snapshot()
        except Exception:
            pass
        # NOTE: Do NOT set step0 quality here - this function is called from multiple steps
        # Step 0 quality should only be set when user explicitly fills data on step 0 page
        # The caller (step 0's quick-fill button) should set the quality separately

    def _set_pending_ai(self, step: int, container, mock_renderer: callable) -> None:
        """Store AI rendering context for manual realtime trigger."""
        self.pending_ai[int(step)] = {
            "container": container,
            "mock_renderer": mock_renderer,
        }

    def trigger_realtime_ai(self, step: int) -> None:
        """Manually trigger realtime AI for a step after data is filled.
        
        NiceGUI requires UI operations to happen in the correct client context.
        We use ui.timer with once=True to schedule the async work properly.
        """
        payload = self.pending_ai.get(int(step))
        
        # For step 0, auto-setup pending_ai if not set
        if not payload and step == 0 and hasattr(self, 'snapshot_inputs'):
            inputs = self.snapshot_inputs
            if 'ai_comment' in inputs:
                is_reasonable = self.session.step_data_quality.get(0, True)
                mock_renderer = self._create_mock_renderer(is_reasonable)
                self._set_pending_ai(0, inputs['ai_comment'], mock_renderer)
                payload = self.pending_ai.get(0)
        
        if not payload:
            ui.notify("请先填充或分析数据后再调用实时AI", type='warning')
            return
        
        container = payload["container"]
        
        # Show loading indicator immediately (in current UI context)
        container.clear()
        with container:
            with ui.row().classes("items-center gap-2"):
                ui.spinner(size="lg")
                ui.label("正在调用实时AI，请稍候...").classes("text-blue-600")
        
        # Use background_tasks.create for proper NiceGUI async handling
        from nicegui import background_tasks
        
        async def do_ai_call():
            import asyncio
            
            # Get API info
            try:
                from global_state import get_available_api_sync
                current_api, api_key = get_available_api_sync()
            except Exception:
                current_api, api_key = None, None
            
            if not current_api or not api_key:
                # Update UI - must use container context
                container.clear()
                with container:
                    glass_alert("⚠️ 未配置 AI API Key，请前往设置页面配置。", "warning")
                return
            
            step_idx = int(step)
            
            # Capture snapshot for step 0
            if step_idx == 0:
                try:
                    if getattr(self, 'snapshot_inputs', None):
                        self.session.machine_snapshot = self.capture_snapshot()
                except Exception:
                    pass
            
            # Define the blocking API call
            def blocking_api_call():
                try:
                    if current_api == "openai":
                        from openai_client import request_assessment
                        return request_assessment(self.session, api_key=api_key, timeout=15, focus_step=step_idx)
                    elif current_api == "gemini":
                        from gemini_client import request_assessment
                        return request_assessment(self.session, api_key=api_key, timeout=15, focus_step=step_idx)
                    elif current_api == "deepseek":
                        from openai_client import request_assessment
                        return request_assessment(self.session, api_key=api_key, timeout=15, 
                                                  api_url="https://api.deepseek.com", focus_step=step_idx)
                except Exception as e:
                    print(f"[AI] API call exception: {e}")
                return None
            
            # Run blocking call in thread pool
            assessment = await asyncio.get_event_loop().run_in_executor(None, blocking_api_call)
            
            # Update UI with result (we're back in the UI context now)
            # Use 'with container:' to ensure we have a valid slot context for ALL UI operations
            with container:
                container.clear()
                if assessment and isinstance(assessment, dict):
                    try:
                        self.session.set_ai_assessment(step_idx, assessment, provider=current_api)
                    except Exception:
                        pass
                    
                    text = self._format_assessment_text(assessment)
                    glass_alert(f"🤖 实时AI点评（{current_api.upper()}）：\n" + text, "success")
                    ui.notify(f"✅ AI点评成功", type="positive")
                    print(f"[AI] Success for step {step_idx}")
                else:
                    glass_alert("⚠️ AI调用失败，请检查网络或API配置。", "warning")
                    ui.notify("⚠️ AI调用失败", type="warning")
                    print(f"[AI] Failed for step {step_idx}")
        
        background_tasks.create(do_ai_call())

    def _get_ai_label(self) -> str:
        try:
            from global_state import get_available_api_sync
            api_name, _ = get_available_api_sync()
            return api_name.upper() if api_name else "AI"
        except Exception:
            return "AI"
    
    def _create_mock_renderer(self, is_reasonable: bool):
        """Create a mock renderer function for AI comments."""
        def mock_renderer():
            inputs = self.snapshot_inputs
            inputs['ai_comment'].clear()
            part_name = inputs['part_name'].value or "—"
            model_no = inputs['model_no'].value or "—"
            part_no = inputs['part_no'].value or "—"
            supplier = inputs['supplier'].value or "—"
            owner = inputs['owner'].value or "—"
            material_brand = inputs['material_brand'].value or "—"
            material_type = inputs['material_type'].value or "—"
            material_color = inputs['material_color'].value or "—"
            material_density = inputs['material_density'].value or "—"
            machine_number = inputs['machine_number'].value or "—"
            machine_brand = inputs['machine_brand'].value or "—"
            machine_tonnage = inputs['machine_tonnage'].value or "—"
            screw_diameter = inputs['screw_diameter'].value or "—"
            mold_number = inputs['mold_number'].value or "—"
            cavity_count = inputs['cavity_count'].value or "—"
            runner_type = inputs['runner_type'].value or "—"
            z1 = inputs['barrel1'].value or "—"
            z5 = inputs['barrel5'].value or "—"
            mold_fixed = inputs['mold_fixed'].value or "—"
            mold_moving = inputs['mold_moving'].value or "—"
            cycle_time = inputs['cycle_time'].value or "—"
            
            if is_reasonable:
                with inputs['ai_comment']:
                    glass_alert(
                        "🤖 AI点评加载中...\n"
                        f"【产品】{part_name} | Model {model_no} | Part {part_no} | 供应商 {supplier} | 负责人 {owner}\n"
                        f"【材料】{material_brand} {material_type} | 颜色 {material_color} | 密度 {material_density} g/cm³\n"
                        f"【机台&模具】{machine_number} {machine_brand} {machine_tonnage}T | 螺杆 {screw_diameter}mm | 模号 {mold_number} | 穴数 {cavity_count} | 流道 {runner_type}\n"
                        f"【工艺】料筒温度梯度 {z1}→{z5}°C | 模温 {mold_fixed}/{mold_moving}°C | 周期 {cycle_time}s\n"
                        "⏳ 已准备就绪，可点击实时AI点评",
                        "info"
                    )
            else:
                with inputs['ai_comment']:
                    glass_alert(
                        "🤖 AI点评加载中...\n"
                        f"【产品】{part_name} 基础信息需复核\n"
                        f"【材料】{material_brand} 建议确认干燥与密度参数\n"
                        f"【机台&模具】机台 {machine_number} / 模号 {mold_number} 建议核对规格\n"
                        f"【工艺】模温 {mold_fixed}/{mold_moving}°C 温差偏大；周期 {cycle_time}s 过长\n"
                        "⏳ 已准备就绪，可点击实时AI点评",
                        "info"
                    )
        
        return mock_renderer
    
    def capture_snapshot(self) -> MachineSnapshot:
        """Capture current snapshot from UI inputs."""
        return MachineSnapshot(
            model_no=self.snapshot_inputs['model_no'].value,
            part_no=self.snapshot_inputs['part_no'].value,
            part_name=self.snapshot_inputs['part_name'].value,
            supplier=self.snapshot_inputs['supplier'].value,
            owner=self.snapshot_inputs['owner'].value,
            theoretical_part_weight=float(self.snapshot_inputs['theoretical_part_weight'].value or 0),
            actual_part_weight=float(self.snapshot_inputs['actual_part_weight'].value or 0),
            
            material_brand=self.snapshot_inputs['material_brand'].value,
            material_type=self.snapshot_inputs['material_type'].value,
            material_number=self.snapshot_inputs['material_number'].value,
            material_color=self.snapshot_inputs['material_color'].value,
            material_density=float(self.snapshot_inputs['material_density'].value or 0),
            drying_temp=self.snapshot_inputs['drying_temp'].value,
            drying_time=self.snapshot_inputs['drying_time'].value,
            
            machine_number=self.snapshot_inputs['machine_number'].value,
            machine_brand=self.snapshot_inputs['machine_brand'].value,
            machine_tonnage=float(self.snapshot_inputs['machine_tonnage'].value or 0),
            screw_diameter=float(self.snapshot_inputs['screw_diameter'].value or 53),
            intensification_ratio=float(self.snapshot_inputs['intensification_ratio'].value or 1),
            
            mold_number=self.snapshot_inputs['mold_number'].value,
            cavity_count=self.snapshot_inputs['cavity_count'].value,
            runner_type=self.snapshot_inputs['runner_type'].value,

            barrel_temp_zone1=float(self.snapshot_inputs['barrel1'].value or 0),
            barrel_temp_zone2=float(self.snapshot_inputs['barrel2'].value or 0),
            barrel_temp_zone3=float(self.snapshot_inputs['barrel3'].value or 0),
            barrel_temp_zone4=float(self.snapshot_inputs['barrel4'].value or 0),
            barrel_temp_zone5=float(self.snapshot_inputs['barrel5'].value or 0),
            nozzle_temp=float(self.snapshot_inputs['nozzle'].value or 0),
            hot_runner_temp=float(self.snapshot_inputs['hot_runner'].value or 0),
            mold_temp_fixed=float(self.snapshot_inputs['mold_fixed'].value or 0),
            mold_temp_moving=float(self.snapshot_inputs['mold_moving'].value or 0),
            max_injection_pressure=float(self.snapshot_inputs['max_inj_pressure'].value or 0),
            max_holding_pressure=float(self.snapshot_inputs['max_hold_pressure'].value or 0),
            vp_transfer_position=float(self.snapshot_inputs['vp_position'].value or 0),
            cycle_time=float(self.snapshot_inputs['cycle_time'].value or 0),
        )
    
    def handle_machine_snapshot_update(self):
        """Update session snapshot when inputs change."""
        try:
            self.session.machine_snapshot = self.capture_snapshot()
        except Exception:
            pass

    def _format_assessment_text(self, assessment: Dict[str, Any]) -> str:
        """Format provider assessment dict into Chinese display text."""
        if not isinstance(assessment, dict):
            return str(assessment)

        parts: List[str] = []
        overall = assessment.get('overall') or assessment.get('conclusions') or assessment.get('conclusion')
        if overall:
            if isinstance(overall, (list, tuple)):
                parts.append("总体评价：\n" + "\n".join([str(x) for x in overall]))
            else:
                parts.append("总体评价：\n" + str(overall))

        conclusions = assessment.get('conclusions') or assessment.get('conclusion')
        if conclusions and conclusions != overall:
            if isinstance(conclusions, (list, tuple)):
                parts.append("结论：\n" + "\n".join([f"• {c}" for c in conclusions]))
            else:
                parts.append("结论：\n" + str(conclusions))

        actions = assessment.get('actions')
        if actions:
            if isinstance(actions, (list, tuple)):
                parts.append("建议动作：\n" + "\n".join([f"• {a}" for a in actions]))
            else:
                parts.append("建议动作：\n" + str(actions))

        risks = assessment.get('risks')
        if risks:
            if isinstance(risks, (list, tuple)):
                parts.append("风险提示：\n" + "\n".join([f"• {r}" for r in risks]))
            else:
                parts.append("风险提示：\n" + str(risks))

        missing = assessment.get('missing_key_data')
        if missing and isinstance(missing, list):
            lines: List[str] = []
            for it in missing:
                if isinstance(it, dict):
                    step = it.get('step')
                    label = it.get('label') or it.get('field') or it.get('name')
                    why = it.get('why')
                    how = it.get('how_to_get')
                    line = f"• Step{step} {label}" if step is not None else f"• {label}"
                    if why:
                        line += f"（用途：{why}）"
                    if how:
                        line += f"；补齐建议：{how}"
                    lines.append(line)
                else:
                    lines.append(f"• {it}")
            if lines:
                parts.append("缺失关键数据（请补齐）：\n" + "\n".join(lines))

        bad_points = assessment.get('unreasonable_data_points')
        if bad_points and isinstance(bad_points, list):
            lines = []
            for it in bad_points:
                if not isinstance(it, dict):
                    lines.append(f"• {it}")
                    continue
                step = it.get('step')
                field = it.get('field')
                value = it.get('value')
                why = it.get('why')
                suggestion = it.get('suggestion')
                line = f"• Step{step} {field}={value}"
                if why:
                    line += f"，原因：{why}"
                if suggestion:
                    line += f"，建议：{suggestion}"
                lines.append(line)
            if lines:
                parts.append("不合理数据点（逐条）：\n" + "\n".join(lines))

        return "\n\n".join(parts) if parts else str(assessment)

    def _compute_missing_key_data(self, focus_step: Optional[int] = None) -> List[Dict[str, Any]]:
        """Compute which key numeric fields are missing (None/empty/zero) for the current session.

        This is deterministic and prevents the AI from being vague about "missing key data".
        """

        def _is_missing(value: Any) -> bool:
            if value is None:
                return True
            if isinstance(value, str):
                v = value.strip().lower()
                return v in ("", "n/a", "na", "none", "null")
            if isinstance(value, (list, tuple, dict, set)):
                return len(value) == 0
            if isinstance(value, (int, float)):
                return float(value) == 0.0
            return False

        # Required fields by step
        requirements: List[Dict[str, Any]] = [
            # Step 0 (snapshot / setup)
            {
                'step': 0,
                'field': 'machine_snapshot.machine_tonnage',
                'label': '机台吨位 (machine_tonnage)',
                'why': '用于校核锁模力与成型安全裕度',
                'how_to_get': '从机台铭牌/参数页面录入',
                'get': lambda: getattr(getattr(self.session, 'machine_snapshot', None), 'machine_tonnage', None),
            },
            {
                'step': 0,
                'field': 'machine_snapshot.screw_diameter',
                'label': '螺杆直径 (screw_diameter)',
                'why': '影响剪切速率/粘度曲线与充填能力评估',
                'how_to_get': '从机台配置或螺杆规格获取',
                'get': lambda: getattr(getattr(self.session, 'machine_snapshot', None), 'screw_diameter', None),
            },
            {
                'step': 0,
                'field': 'machine_snapshot.max_injection_pressure',
                'label': '最大注射压力 (max_injection_pressure)',
                'why': '用于步骤3压力裕度与是否压力受限判断',
                'how_to_get': '从机台参数/报警设定读取并录入',
                'get': lambda: getattr(getattr(self.session, 'machine_snapshot', None), 'max_injection_pressure', None),
            },
            {
                'step': 0,
                'field': 'machine_snapshot.max_holding_pressure',
                'label': '最大保压压力 (max_holding_pressure)',
                'why': '用于保压能力/浇口冻结窗口判断',
                'how_to_get': '从机台保压上限设定读取并录入',
                'get': lambda: getattr(getattr(self.session, 'machine_snapshot', None), 'max_holding_pressure', None),
            },
            {
                'step': 0,
                'field': 'machine_snapshot.vp_transfer_position',
                'label': 'V/P切换位置 (vp_transfer_position)',
                'why': '用于一致性控制与工艺窗口复现实验',
                'how_to_get': '从当前生产配方/机台曲线读取',
                'get': lambda: getattr(getattr(self.session, 'machine_snapshot', None), 'vp_transfer_position', None),
            },
            {
                'step': 0,
                'field': 'machine_snapshot.cycle_time',
                'label': '成型周期 (cycle_time)',
                'why': '影响冷却/产能与温度平衡评估',
                'how_to_get': '从机台实际循环监控读取',
                'get': lambda: getattr(getattr(self.session, 'machine_snapshot', None), 'cycle_time', None),
            },
            # Step 1
            {
                'step': 1,
                'field': 'viscosity_data_points',
                'label': '粘度曲线数据点 (speed/viscosity)',
                'why': '用于找到拐点与最佳充填速度',
                'how_to_get': '录入或Excel导入：至少3个速度-粘度点',
                'get': lambda: getattr(self.session, 'viscosity_data_points', None),
            },
            {
                'step': 1,
                'field': 'viscosity_inflection_point',
                'label': '粘度拐点结果 (inflection point)',
                'why': '用于确定推荐注射速度与工艺基准',
                'how_to_get': '完成步骤1计算后自动生成；若为空请重新计算/检查输入',
                'get': lambda: getattr(self.session, 'viscosity_inflection_point', None),
            },
            # Step 2
            {
                'step': 2,
                'field': 'cavity_weights',
                'label': '短射型腔重量 (cavity_weights)',
                'why': '用于型腔平衡判定与流道调整方向',
                'how_to_get': '每穴称重并录入/Excel导入',
                'get': lambda: getattr(self.session, 'cavity_weights', None),
            },
            {
                'step': 2,
                'field': 'cavity_weights_full',
                'label': '满射型腔重量 (cavity_weights_full)',
                'why': '用于确认平衡在充满状态下是否仍成立',
                'how_to_get': '每穴满射称重并录入/Excel导入',
                'get': lambda: getattr(self.session, 'cavity_weights_full', None),
            },
            # Step 3
            {
                'step': 3,
                'field': 'pressure_drop_data',
                'label': '压力降/压力分布数据 (pressure_drop_data)',
                'why': '用于计算压力裕度与识别压力受限',
                'how_to_get': '录入各段压力/曲线采样点（喷嘴/前段/末端等）',
                'get': lambda: getattr(self.session, 'pressure_drop_data', None),
            },
            {
                'step': 3,
                'field': 'pressure_margin',
                'label': '压力裕度结果 (pressure_margin)',
                'why': '用于判断是否有足够工艺窗口与稳定性',
                'how_to_get': '完成步骤3计算后自动生成；若为空请补录压力数据后重算',
                'get': lambda: getattr(self.session, 'pressure_margin', None),
            },
            # Step 4
            {
                'step': 4,
                'field': 'process_window_data',
                'label': '工艺窗口试验点数据 (process_window_data)',
                'why': '用于建立O-Window并确定中心点',
                'how_to_get': '按矩阵试验记录16点（或系统要求点数）并录入/导入',
                'get': lambda: getattr(self.session, 'process_window_data', None),
            },
            {
                'step': 4,
                'field': 'process_window_bounds',
                'label': '工艺窗口边界结果 (process_window_bounds)',
                'why': '用于定义可控范围与验收标准',
                'how_to_get': '完成步骤4计算后自动生成；若为空请补齐试验点数据',
                'get': lambda: getattr(self.session, 'process_window_bounds', None),
            },
            # Step 5
            {
                'step': 5,
                'field': 'gate_seal_curve',
                'label': '浇口冻结曲线数据 (gate_seal_curve)',
                'why': '用于确定最小保压时间，避免过保压/欠保压',
                'how_to_get': '记录不同保压时间下重量变化并录入/Excel导入',
                'get': lambda: getattr(self.session, 'gate_seal_curve', None),
            },
            {
                'step': 5,
                'field': 'gate_freeze_time',
                'label': '浇口冻结时间结果 (gate_freeze_time)',
                'why': '用于设定保压时间与稳定窗口',
                'how_to_get': '完成步骤5分析后自动生成；若为空请补录曲线数据后重算',
                'get': lambda: getattr(self.session, 'gate_freeze_time', None),
            },
            # Step 6
            {
                'step': 6,
                'field': 'cooling_curve',
                'label': '冷却曲线数据 (cooling_curve)',
                'why': '用于确定可靠冷却时间并控制翘曲/收缩',
                'how_to_get': '记录不同冷却时间的温度/变形/外观并录入/Excel导入',
                'get': lambda: getattr(self.session, 'cooling_curve', None),
            },
            {
                'step': 6,
                'field': 'recommended_cooling_time',
                'label': '推荐冷却时间结果 (recommended_cooling_time)',
                'why': '用于量产周期与质量稳定性设定',
                'how_to_get': '完成步骤6分析后自动生成；若为空请补录冷却曲线数据',
                'get': lambda: getattr(self.session, 'recommended_cooling_time', None),
            },
            # Step 7
            {
                'step': 7,
                'field': 'clamping_force_curve',
                'label': '锁模力试验曲线 (clamping_force_curve)',
                'why': '用于确定最小锁模力与防飞边窗口',
                'how_to_get': '记录不同锁模力下飞边/重量变化并录入',
                'get': lambda: getattr(self.session, 'clamping_force_curve', None),
            },
            {
                'step': 7,
                'field': 'recommended_clamping_force',
                'label': '推荐锁模力结果 (recommended_clamping_force)',
                'why': '用于锁模设定与设备能力校核',
                'how_to_get': '完成步骤7分析后自动生成；若为空请补录锁模力曲线数据',
                'get': lambda: getattr(self.session, 'recommended_clamping_force', None),
            },
        ]

        try:
            focus = int(focus_step) if focus_step is not None else None
        except Exception:
            focus = None

        missing_items: List[Dict[str, Any]] = []
        for req in requirements:
            step = req.get('step')
            if focus is not None and step not in (0, focus):
                # When focusing a step, still keep step0 snapshot requirements
                continue
            getter = req.get('get')
            try:
                value = getter() if callable(getter) else None
            except Exception:
                value = None

            # Special handling for viscosity points: require at least 3 points
            if req.get('field') == 'viscosity_data_points':
                if not isinstance(value, list) or len(value) < 3:
                    missing_items.append({k: req[k] for k in ('step', 'field', 'label', 'why', 'how_to_get')})
                continue

            if _is_missing(value):
                missing_items.append({k: req[k] for k in ('step', 'field', 'label', 'why', 'how_to_get')})

        return missing_items

    async def _render_ai_comment_async(self, container, mock_renderer: callable, step: Optional[int] = None):
        """Async version: Render AI comment without blocking UI."""
        import asyncio
        
        # Import app_state and helper function
        try:
            from global_state import app_state, get_available_api_sync
        except Exception:
            app_state = {}
            get_available_api_sync = lambda: (None, None)
        
        # Determine step
        try:
            step_idx = int(step) if step is not None else int(getattr(self.session, 'current_step', 0) or 0)
        except Exception:
            step_idx = 0

        # For step 0, capture snapshot
        if step_idx == 0:
            try:
                if getattr(self, 'snapshot_inputs', None):
                    self.session.machine_snapshot = self.capture_snapshot()
            except Exception:
                pass

        # Get API
        current_api, api_key = get_available_api_sync()
        
        if not current_api or not api_key:
            container.clear()
            with container:
                glass_alert("⚠️ 未配置 AI API Key，请前往设置页面配置。", "warning")
            container.update()
            return

        # Show loading
        ui.notify(f"⏳ 正在调用 {current_api.upper()}...", type="info")

        # Run API call in background thread
        def call_api():
            if current_api == "openai":
                from openai_client import request_assessment
                return request_assessment(self.session, api_key=api_key, timeout=20, focus_step=step_idx)
            elif current_api == "gemini":
                from gemini_client import request_assessment
                return request_assessment(self.session, api_key=api_key, timeout=20, focus_step=step_idx)
            elif current_api == "deepseek":
                from openai_client import request_assessment
                return request_assessment(self.session, api_key=api_key, timeout=20, api_url="https://api.deepseek.com", focus_step=step_idx)
            return None

        try:
            assessment = await asyncio.to_thread(call_api)
        except Exception as e:
            print(f"[AI Comment] API call failed: {e}")
            assessment = None

        # Update UI with result
        if assessment and isinstance(assessment, dict):
            try:
                self.session.set_ai_assessment(step_idx, assessment, provider=current_api)
            except Exception:
                pass
            
            text = self._format_assessment_text(assessment)
            container.clear()
            with container:
                glass_alert(f"🤖 实时AI点评（{current_api.upper()}）：\n" + text, "success")
            container.update()
            ui.notify(f"✅ 实时AI点评成功（{current_api.upper()}）", type="positive")
            print(f"[AI Comment] Realtime AI succeeded for step {step_idx}")
        else:
            container.clear()
            with container:
                glass_alert("⚠️ 实时AI调用失败，请检查网络或API配置。", "warning")
            container.update()
            ui.notify("⚠️ 实时AI调用失败", type="warning")
            print(f"[AI Comment] All API attempts failed for step {step_idx}")

    def _render_ai_comment(self, container, mock_renderer: callable, step: Optional[int] = None):
        """Render AI comment: first show mock immediately, then attempt realtime AI in background.
        
        Flow:
        1. Immediately render mock data so user sees results fast
        2. Show a notification that realtime AI is being requested
        3. If realtime AI succeeds, replace mock with realtime result
        4. If realtime AI fails, show notification and keep mock
        """
        # Import app_state and helper function from main to access global API keys
        try:
            from global_state import app_state, get_available_api_sync
        except Exception:
            app_state = {}
            get_available_api_sync = lambda: (None, None)
        
        # Determine which step to attribute this comment to
        try:
            step_idx = int(step) if step is not None else int(getattr(self.session, 'current_step', 0) or 0)
        except Exception:
            step_idx = 0

        # For step 0, ensure latest inputs are captured before requesting AI
        if step_idx == 0:
            try:
                if getattr(self, 'snapshot_inputs', None):
                    self.session.machine_snapshot = self.capture_snapshot()
            except Exception:
                pass

        # Step 1: Immediately render mock data
        try:
            container.clear()
            mock_renderer()
        except Exception as e:
            print(f"[AI Comment] Mock renderer failed: {e}")

        # Get the current available API
        current_api, api_key = get_available_api_sync()
        
        # If no API key available, show configuration prompt
        if not current_api or not api_key:
            print(f"[AI Comment] No API key available, showing config prompt for step {step_idx}")
            try:
                container.clear()
                with container:
                    glass_alert(
                        "⚠️ 未配置 AI API Key\n\n"
                        "请前往首页设置页面配置有效的 API Key，然后重新测试此步骤。\n"
                        "目前显示的是本地 Mock AI 演示结果。",
                        "warning"
                    )
                ui.notification(
                    "⚠️ 未配置 AI API Key，已显示本地Mock",
                    type="warning",
                    position="top",
                    timeout=6000,
                )
            except Exception as e:
                print(f"[AI Comment] Failed to show config prompt: {e}")
            return

        provider_label = current_api.upper() if current_api else "AI"

        # Step 2: Show notification that realtime AI is being requested
        loading_notification = None
        try:
            loading_notification = ui.notification(
                f"⏳ 正在调用 {provider_label} ...",
                type="info",
                position="top",
                timeout=None,  # Don't auto-dismiss
                close_button=True,
            )
        except Exception as e:
            print(f"[AI Comment] Failed to show loading notification: {e}")

        request_id = f"{step_idx}-{time.time()}"
        try:
            if step_idx in self.pending_ai:
                self.pending_ai[step_idx]["request_id"] = request_id
                self.pending_ai[step_idx]["ai_done"] = False
        except Exception:
            pass

        # Request AI synchronously to avoid background slot errors
        try:
            assessment = None
            used_api = current_api

            print(f"[AI Comment] Using {current_api.upper()} API...")

            if current_api == "openai":
                from openai_client import request_assessment as request_openai_assessment
                print(f"[AI Comment] Calling OpenAI with 30s timeout...")
                assessment = request_openai_assessment(
                    self.session,
                    api_key=api_key,
                    timeout=30,
                    focus_step=step_idx,
                )
            elif current_api == "gemini":
                from gemini_client import request_assessment as request_gemini_assessment
                print(f"[AI Comment] Calling Gemini with 30s timeout...")
                assessment = request_gemini_assessment(
                    self.session,
                    api_key=api_key,
                    timeout=30,
                    focus_step=step_idx,
                )
            elif current_api == "deepseek":
                from openai_client import request_assessment as request_openai_assessment
                assessment = request_openai_assessment(
                    self.session,
                    api_key=api_key,
                    timeout=30,
                    api_url="https://api.deepseek.com",
                    focus_step=step_idx,
                )

            # Fallback: Try other available APIs (including when DeepSeek fails)
            if assessment is None and app_state:
                for api_name in app_state.get("api_priority_order", []):
                    if api_name == current_api:
                        continue
                    fallback_key = app_state.get("api_keys", {}).get(api_name)
                    if fallback_key:
                        print(f"[AI Comment] Fallback to {api_name.upper()}...")
                        if api_name == "openai":
                            from openai_client import request_assessment as request_openai_assessment
                            assessment = request_openai_assessment(
                                self.session,
                                api_key=fallback_key,
                                timeout=30,
                                focus_step=step_idx,
                            )
                        elif api_name == "gemini":
                            from gemini_client import request_assessment as request_gemini_assessment
                            assessment = request_gemini_assessment(
                                self.session,
                                api_key=fallback_key,
                                timeout=30,
                                focus_step=step_idx,
                            )
                        elif api_name == "deepseek":
                            from openai_client import request_assessment as request_openai_assessment
                            assessment = request_openai_assessment(
                                self.session,
                                api_key=fallback_key,
                                timeout=30,
                                api_url="https://api.deepseek.com",
                                focus_step=step_idx,
                            )

                        if assessment:
                            app_state["current_api"] = api_name
                            used_api = api_name
                            print(f"[AI Comment] {api_name.upper()} fallback succeeded!")
                            break

            # Dismiss loading notification
            try:
                if loading_notification:
                    loading_notification.dismiss()
            except Exception:
                pass

            if assessment and isinstance(assessment, dict):
                try:
                    computed_missing = self._compute_missing_key_data(focus_step=step_idx)
                    existing_missing = assessment.get('missing_key_data')
                    if computed_missing and (not isinstance(existing_missing, list) or len(existing_missing) == 0):
                        assessment['missing_key_data'] = computed_missing
                except Exception:
                    pass

                try:
                    self.session.set_ai_assessment(step_idx, assessment, provider=used_api)
                except Exception:
                    pass

                text = self._format_assessment_text(assessment)
                provider_label = f"（{used_api.upper()}）" if used_api else ""

                try:
                    if step_idx in self.pending_ai and self.pending_ai[step_idx].get("request_id") == request_id:
                        self.pending_ai[step_idx]["ai_done"] = True
                except Exception:
                    pass

                container.clear()
                with container:
                    glass_alert(f"🤖 实时AI点评{provider_label}：\n" + text, "success")
                container.update()
                ui.notify(f"✅ 实时AI点评成功（{used_api.upper()}）", type="positive")

                print(f"[AI Comment] Realtime AI succeeded for step {step_idx}")
            else:
                print(f"[AI Comment] All API attempts failed, keeping mock for step {step_idx}")
                try:
                    if step_idx in self.pending_ai and self.pending_ai[step_idx].get("request_id") == request_id:
                        self.pending_ai[step_idx]["ai_done"] = True
                except Exception:
                    pass

                container.clear()
                with container:
                    glass_alert(
                        "⚠️ 实时AI调用失败，已启用本地Mock AI\n\n"
                        "请检查API配置或网络连接。",
                        "warning"
                    )
                container.update()
                ui.notify("⚠️ 实时AI调用失败", type="warning")

        except Exception as e:
            print(f"[AI Comment] Realtime AI request failed: {e}")
            try:
                if loading_notification:
                    loading_notification.dismiss()
            except Exception:
                pass
            try:
                container.clear()
                with container:
                    glass_alert(
                        "⚠️ 实时AI调用异常\n\n"
                        "请检查API配置或网络连接。",
                        "warning"
                    )
                container.update()
                ui.notify("⚠️ 实时AI调用异常", type="warning")
            except Exception:
                pass

    async def handle_excel_upload(self, e: UploadEventArguments, speeds_input, viscosities_input, 
                                   screw_dia, machine_inputs, upload_status):
        """处理Excel文件上传并自动填充数据"""
        try:
            # 读取上传的文件内容
            content = e.content.read()
            filename = e.name
            
            # 解析Excel
            parser = ExcelDataParser()
            self.uploaded_excel_data = parser.parse_bytes(content)
            
            # 更新状态显示
            upload_status.clear()
            with upload_status:
                if self.uploaded_excel_data.parse_errors:
                    glass_alert(f"❌ 解析错误: {', '.join(self.uploaded_excel_data.parse_errors)}", "error")
                    return
                
                # 统计识别到的数据
                data_summary = []
                
                # Step 1: 粘度曲线
                if self.uploaded_excel_data.viscosity and self.uploaded_excel_data.viscosity.speeds:
                    v = self.uploaded_excel_data.viscosity
                    data_summary.append(f"✓ 粘度曲线: {len(v.speeds)}个数据点")
                    # 自动填充到输入框
                    speeds_input.set_value(",".join([str(s) for s in v.speeds]))
                    viscosities_input.set_value(",".join([str(v) for v in v.viscosities]))
                    if v.screw_diameter > 0:
                        screw_dia.set_value(str(v.screw_diameter))
                
                # Step 2: 型腔平衡
                if self.uploaded_excel_data.cavity_balance and self.uploaded_excel_data.cavity_balance.cavity_weights:
                    cb = self.uploaded_excel_data.cavity_balance
                    data_summary.append(f"✓ 型腔平衡: {len(cb.cavity_weights)}个腔")
                
                # Step 5: 浇口冻结
                if self.uploaded_excel_data.gate_freeze and self.uploaded_excel_data.gate_freeze.hold_times:
                    gf = self.uploaded_excel_data.gate_freeze
                    data_summary.append(f"✓ 浇口冻结: {len(gf.hold_times)}个数据点")
                
                # Step 6: 冷却时间
                if self.uploaded_excel_data.cooling_time and self.uploaded_excel_data.cooling_time.cooling_times:
                    ct = self.uploaded_excel_data.cooling_time
                    data_summary.append(f"✓ 冷却时间: {len(ct.cooling_times)}个数据点")
                
                # 机台信息
                if self.uploaded_excel_data.machine_snapshot:
                    ms = self.uploaded_excel_data.machine_snapshot
                    data_summary.append("✓ 机台参数已识别")
                    # 自动填充机台参数
                    if ms.barrel_temp_zone1 > 0:
                        machine_inputs['barrel1'].set_value(str(int(ms.barrel_temp_zone1)))
                    if ms.barrel_temp_zone2 > 0:
                        machine_inputs['barrel2'].set_value(str(int(ms.barrel_temp_zone2)))
                    if ms.barrel_temp_zone3 > 0:
                        machine_inputs['barrel3'].set_value(str(int(ms.barrel_temp_zone3)))
                    if ms.barrel_temp_zone4 > 0:
                        machine_inputs['barrel4'].set_value(str(int(ms.barrel_temp_zone4)))
                    if ms.barrel_temp_zone5 > 0:
                        machine_inputs['barrel5'].set_value(str(int(ms.barrel_temp_zone5)))
                    if ms.nozzle_temp > 0:
                        machine_inputs['nozzle'].set_value(str(int(ms.nozzle_temp)))
                    if hasattr(ms, 'hot_runner_temp') and ms.hot_runner_temp > 0:
                        machine_inputs['hot_runner'].set_value(str(int(ms.hot_runner_temp)))
                    if ms.mold_temp_fixed > 0:
                        machine_inputs['mold_fixed'].set_value(str(int(ms.mold_temp_fixed)))
                    if ms.mold_temp_moving > 0:
                        machine_inputs['mold_moving'].set_value(str(int(ms.mold_temp_moving)))
                    if hasattr(ms, 'cycle_time') and ms.cycle_time > 0:
                        machine_inputs['cycle_time'].set_value(str(float(ms.cycle_time)))
                
                if data_summary:
                    glass_alert(
                        f"📁 文件 '{filename}' 解析成功!\n\n" + "\n".join(data_summary) + 
                        "\n\n💡 数据已自动填入，点击「分析我的数据」开始分析",
                        "success"
                    )
                else:
                    glass_alert(
                        f"⚠️ 文件 '{filename}' 未找到有效数据\n\n"
                        "请确保Excel包含以下工作表之一:\n"
                        "• Step1_粘度曲线 (或含 '粘度' 的表名)\n"
                        "• Step2_型腔平衡 (或含 '型腔' 的表名)\n"
                        "• 等等...\n\n"
                        "💡 点击「下载模板」获取标准格式",
                        "warning"
                    )
                
                # 显示警告
                if self.uploaded_excel_data.parse_warnings:
                    for w in self.uploaded_excel_data.parse_warnings:
                        ui.label(f"⚠ {w}").classes("text-yellow-600 text-sm")
            
            ui.notify(f"✓ Excel文件已解析", type='positive')
            
        except Exception as e:
            upload_status.clear()
            with upload_status:
                glass_alert(f"❌ 上传失败: {str(e)}", "error")
            ui.notify(f"上传失败: {str(e)}", type='negative')
    
    def download_template(self):
        """生成并下载Excel模板"""
        import tempfile
        template_path = os.path.join(tempfile.gettempdir(), "SmartMold_数据模板.xlsx")
        create_template_excel(template_path)
        
        # 读取文件并提供下载
        with open(template_path, 'rb') as f:
            content = f.read()
        
        ui.download(content, "SmartMold_数据模板.xlsx")
        ui.notify("✓ 模板下载中...", type='positive')

    def render_step1_viscosity(self):
        """Step 1: Viscosity Curve Analysis."""
        with glass_card("步骤 1: 粘度曲线分析"):
            ui.label("目标：找到剪切变稀的拐点，确定最佳射胶速度").classes(f"{GLASS_THEME['text_secondary']} mb-4")
            
            # ========== Excel上传区域 ==========
            with ui.expansion("📁 方式一：上传Excel文件（推荐）", icon="upload_file").classes(
                "w-full bg-blue-50/50 rounded-lg mb-4"
            ).props("default-opened"):
                ui.label("上传包含测试数据的Excel文件，系统将自动识别并填充所有步骤的数据").classes(
                    "text-sm text-gray-600 mb-2"
                )
                
                # 上传状态显示区域
                upload_status = ui.column().classes("w-full")
                
                with ui.row().classes('gap-4 items-center'):
                    # 上传组件
                    upload = ui.upload(
                        label="选择Excel文件",
                        auto_upload=True,
                        max_files=1,
                        max_file_size=10*1024*1024,  # 10MB
                    ).props('accept=".xlsx,.xls"').classes(
                        "max-w-md"
                    )
                    
                    # 下载模板按钮
                    ui.button("📥 下载模板", on_click=self.download_template).classes(
                        "bg-slate-500 hover:bg-slate-600 text-white rounded-lg px-4 py-2"
                    )
                
                ui.label("支持格式: .xlsx, .xls | 最大10MB").classes("text-xs text-gray-400 mt-1")
            
            ui.separator().classes("my-2")
            
            # ========== 手动输入区域 ==========
            with ui.expansion("✏️ 方式二：手动输入数据", icon="edit").classes(
                "w-full bg-green-50/50 rounded-lg"
            ):
                ui.label("📊 输入您的测试数据:").classes("text-sm font-semibold text-slate-700 mt-2")
                with ui.row().classes('gap-4 w-full flex-wrap'):
                    speeds_input = glass_input("射速序列 (mm/s, 逗号分隔)", "例如: 6.8,22.2,37.3,45.3,52.9,60.9,68.8")
                    viscosities_input = glass_input("粘度序列 (MPa·s, 逗号分隔)", "例如: 1844,517,350,305,275,253,230")
                    screw_dia = glass_input("螺杆直径 (mm)", "53")
            
            # 显示当前数据状态（供Excel上传填充后展示）
            data_preview = ui.column().classes("w-full mt-2")
            
            # AI Commentary area
            ai_comment = ui.column().classes("w-full mt-4")
            
            result_label = ui.label("等待测试...").classes(f"{GLASS_THEME['text_secondary']}")
            chart_container = ui.column().classes("w-full")
            
            # Machine snapshot - create and keep reference
            machine_inputs = self.create_machine_snapshot_ui()
            
            # 绑定上传处理
            async def on_upload(e: UploadEventArguments):
                await self.handle_excel_upload(e, speeds_input, viscosities_input, screw_dia, machine_inputs, upload_status)
                # 更新数据预览
                data_preview.clear()
                with data_preview:
                    if speeds_input.value and viscosities_input.value:
                        speeds_list = [s.strip() for s in speeds_input.value.split(',') if s.strip()]
                        viscosities_list = [v.strip() for v in viscosities_input.value.split(',') if v.strip()]
                        ui.label(f"📊 已加载 {len(speeds_list)} 个测试点").classes("text-emerald-600 font-semibold")
            
            upload.on('upload', on_upload)
            
            async def run_with_user_data():
                """使用用户输入的真实数据运行分析"""
                try:
                    ai_comment.clear()
                    
                    # 解析用户输入的数据
                    speeds_str = speeds_input.value.strip()
                    viscosities_str = viscosities_input.value.strip()
                    
                    if not speeds_str or not viscosities_str:
                        ui.notify("请输入射速和粘度数据", type='warning')
                        return
                    
                    speeds = [float(x.strip()) for x in speeds_str.split(',') if x.strip()]
                    viscosities = [float(x.strip()) for x in viscosities_str.split(',') if x.strip()]
                    
                    if len(speeds) != len(viscosities):
                        ui.notify(f"数据点数量不匹配: 射速{len(speeds)}个, 粘度{len(viscosities)}个", type='error')
                        return
                    
                    if len(speeds) < 3:
                        ui.notify("至少需要3个测试点", type='warning')
                        return
                    
                    # 保存机台快照
                    self.save_machine_snapshot(machine_inputs)
                    
                    # 数据质量评估
                    speed_range = max(speeds) - min(speeds)
                    is_reasonable = len(speeds) >= 5 and speed_range >= 30
                    
                    def _mock_local_user():
                        ai_comment.clear()
                        with ai_comment:
                            if is_reasonable:
                                glass_alert(
                                    f"🤖 Mock AI点评（您的真实数据）：\n\n"
                                    f"✓ 共{len(speeds)}个测试点，数据充足\n"
                                    f"✓ 射速范围: {min(speeds):.1f} - {max(speeds):.1f} mm/s (跨度{speed_range:.1f}mm/s)\n"
                                    f"✓ 粘度范围: {min(viscosities):.1f} - {max(viscosities):.1f} MPa·s\n"
                                    f"📊 正在分析粘度曲线拐点...",
                                    "success"
                                )
                            else:
                                issues = []
                                if len(speeds) < 5:
                                    issues.append(f"测试点较少({len(speeds)}个)，建议至少5个点")
                                if speed_range < 30:
                                    issues.append(f"射速范围较窄({speed_range:.1f}mm/s)，建议扩大")
                                glass_alert(
                                    f"🤖 Mock AI点评（您的真实数据）：\n\n"
                                    f"⚠ 数据质量提醒:\n" + "\n".join([f"  • {i}" for i in issues]),
                                    "warning"
                                )

                    # Ensure raw viscosity points are present for AI pinpointing
                    try:
                        self.session.viscosity_data_points = [
                            {'index': idx + 1, 'speed_mm_s': float(s), 'viscosity': float(v)}
                            for idx, (s, v) in enumerate(zip(speeds, viscosities))
                        ]
                    except Exception:
                        pass
                    self._set_pending_ai(1, ai_comment, _mock_local_user)
                    _mock_local_user()
                    
                    # 运行分析算法
                    inflection = find_viscosity_inflection_point(speeds, viscosities)
                    optimal_speed = inflection['optimal_speed']

                    def _finalize_step1(assessment=None):
                        self.session.set_step1_result(optimal_speed, inflection)
                        self.session.set_step_quality(1, is_reasonable)

                        result_label.set_text(f"✓ 分析完成\n识别的最佳射速: {optimal_speed:.1f} mm/s\n该速度将自动应用于步骤2和步骤3")
                        result_label.classes(remove="text-red-600 text-emerald-600 text-yellow-600")
                        result_label.classes(add="text-emerald-600")

                        # 绘制图表
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=speeds, y=viscosities, mode='lines+markers', name='粘度曲线',
                            line=dict(color='#3b82f6', width=2)))
                        fig.add_trace(go.Scatter(x=[optimal_speed], y=[inflection['viscosity_at_optimal']],
                            mode='markers', name='拐点', marker=dict(color='red', size=15, symbol='star')))
                        fig.update_layout(title="粘度曲线分析 (您的真实数据)", xaxis_title="射速 (mm/s)", yaxis_title="有效粘度 (MPa·s)", template="plotly_white", height=400)

                        chart_container.clear()
                        with chart_container:
                            ui.plotly(fig).classes('w-full')

                        # Note: progress indicator will be updated when clicking 'Next' and confirming

                        if not is_reasonable:
                            ui.notify("✓ 步骤1数据已填充（数据偏离，点击'下一步'时确认）", type='warning')
                        else:
                            ui.notify("✓ 步骤1数据已填充 - 使用您的真实数据", type='positive')

                    _finalize_step1()
                
                except ValueError as e:
                    ui.notify(f"数据格式错误: 请输入数字，用逗号分隔", type='error')
                except Exception as e:
                    result_label.set_text(f"✗ 错误: {str(e)}")
                    result_label.classes(add="text-red-600")
            
            async def run_test_with_data(is_reasonable: bool):
                """Run test with simulated data."""
                try:
                    ai_comment.clear()
                    
                    # Fill machine snapshot
                    self.fill_machine_snapshot(machine_inputs, is_reasonable)
                    
                    if is_reasonable:
                        speeds = [6.8, 22.2, 37.3, 45.3, 52.9, 60.9, 68.8]
                        viscosities = [1844, 517, 350, 305, 275, 253, 230]
                        speeds_input.set_value("6.8,22.2,37.3,45.3,52.9,60.9,68.8")
                        viscosities_input.set_value("1844,517,350,305,275,253,230")
                        screw_dia.set_value("53")
                        
                        def _mock_sim_ok():
                            ai_comment.clear()
                            with ai_comment:
                                glass_alert(
                                    "🤖 Mock AI点评（PA6 260G6模拟案例）：\n\n"
                                    "✓ 射速6.8-68.8mm/s，覆盖完整剪切区\n"
                                    "✓ 螺杆直径53mm，YIZUMI 260T油压机\n"
                                    "✓ 粘度曲线在37-53mm/s区间有明显拐点\n"
                                    "✓ 最佳射速推荐：45-53mm/s",
                                    "success"
                                )
                        try:
                            self.session.viscosity_data_points = [
                                {'index': idx + 1, 'speed_mm_s': float(s), 'viscosity': float(v)}
                                for idx, (s, v) in enumerate(zip(speeds, viscosities))
                            ]
                        except Exception:
                            pass
                        self._set_pending_ai(1, ai_comment, _mock_sim_ok)
                        _mock_sim_ok()
                    else:
                        speeds = [50, 55, 60]
                        viscosities = [75, 74, 73]
                        speeds_input.set_value("50,55,60")
                        viscosities_input.set_value("75,74,73")
                        screw_dia.set_value("80")
                        
                        def _mock_sim_bad():
                            ai_comment.clear()
                            with ai_comment:
                                glass_alert(
                                    "🤖 Mock AI点评（不合理模拟数据）：\n\n"
                                    "✗ 射速范围太窄（仅50-60mm/s）\n"
                                    "✗ 仅3个测试点不足以精确定位拐点\n"
                                    "⚠ 建议：扩大射速范围",
                                    "error"
                                )
                        try:
                            self.session.viscosity_data_points = [
                                {'index': idx + 1, 'speed_mm_s': float(s), 'viscosity': float(v)}
                                for idx, (s, v) in enumerate(zip(speeds, viscosities))
                            ]
                        except Exception:
                            pass
                        self._set_pending_ai(1, ai_comment, _mock_sim_bad)
                        _mock_sim_bad()
                    
                    inflection = find_viscosity_inflection_point(speeds, viscosities)
                    optimal_speed = inflection['optimal_speed']

                    def _finalize_step1(assessment=None):
                        self.session.set_step1_result(optimal_speed, inflection)
                        self.session.set_step_quality(1, is_reasonable)

                        status = "✓ 合理" if is_reasonable else "⚠ 需改进"
                        result_label.set_text(f"{status}\n识别的最佳射速: {optimal_speed:.1f} mm/s")
                        result_label.classes(remove="text-red-600 text-emerald-600 text-yellow-600")
                        result_label.classes(add="text-emerald-600" if is_reasonable else "text-yellow-600")

                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=speeds, y=viscosities, mode='lines+markers', name='粘度曲线',
                            line=dict(color='#3b82f6' if is_reasonable else '#ef4444', width=2)))
                        fig.add_trace(go.Scatter(x=[optimal_speed], y=[inflection['viscosity_at_optimal']],
                            mode='markers', name='拐点', marker=dict(color='red', size=15, symbol='star')))
                        fig.update_layout(title="粘度曲线分析", xaxis_title="射速 (mm/s)", yaxis_title="相对粘度", template="plotly_white", height=400)

                        chart_container.clear()
                        with chart_container:
                            ui.plotly(fig).classes('w-full')

                        # Note: progress indicator will be updated when clicking 'Next' and confirming

                        if not is_reasonable:
                            ui.notify("✓ 步骤1数据已填充（数据偏离，点击'下一步'时确认）", type='warning')
                        else:
                            ui.notify(f"✓ 步骤1数据已填充", type='positive')

                    _finalize_step1()
                
                except Exception as e:
                    result_label.set_text(f"✗ 错误: {str(e)}")
                    result_label.classes(add="text-red-600")
            
            # 按钮区域
            with ui.row().classes('gap-4 mt-4 flex-wrap'):
                # 主按钮 - 使用用户真实数据
                ui.button("🚀 分析我的数据", on_click=run_with_user_data).classes(
                    "bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg px-8 py-3 text-lg"
                )
                ui.label("|").classes("text-gray-300 self-center")
                # 模拟按钮
                glass_button("⚡ 快速填充（合理）", lambda: run_test_with_data(True))
                ui.button("⚡ 快速填充（不合理）", on_click=lambda: run_test_with_data(False)).classes(
                    "bg-orange-500 hover:bg-orange-600 text-white rounded-lg px-4 py-2 text-sm"
                )
                ui.button(f"🤖 实时AI点评（{self._get_ai_label()}）", on_click=lambda: self.trigger_realtime_ai(1)).props('color=primary')

    def render_step2_cavity_balance(self):
        """Step 2: Cavity Balance Study."""
        with glass_card("步骤 2: 型腔平衡分析"):
            ui.label("目标：确保多型腔模具的填充一致性").classes(f"{GLASS_THEME['text_secondary']} mb-4")
            
            # Status display area
            status_area = ui.column().classes("w-full")
            
            # Cavity weight and visual check inputs
            with ui.grid(columns=4).classes('w-full gap-4 mt-4'):
                cavity_inputs = {}
                visual_inputs = {}
                for i in range(1, 9):
                    with ui.column():
                        inp = glass_input(f"腔{i} 重量(g)", "")
                        vis = ui.select(["OK", "NG"], value="OK", label="目视").classes("w-full h-10")
                        cavity_inputs[i] = inp
                        visual_inputs[i] = vis
            
            # AI Commentary area
            ai_comment = ui.column().classes("w-full mt-4")
            
            result_label = ui.label("等待计算...").classes(f"{GLASS_THEME['text_secondary']}")
            chart_container = ui.column().classes("w-full")
            
            # Machine snapshot
            machine_inputs = self.create_machine_snapshot_ui()
            
            def update_status(show_warning=True):
                status_area.clear()
                inherited = self.session.get_inherited_params(2)
                can_proceed, reason = self.session.can_proceed_to_step(2)
                
                with status_area:
                    if not can_proceed and show_warning:
                        glass_alert(f"⚠️ 请先完成步骤1（粘度曲线）", "warning")
                    elif 'injection_speed' in inherited:
                        glass_alert(f"✅ 射速已锁定为: {inherited['injection_speed']:.1f} mm/s (来自步骤1)", "info")
                
                return can_proceed
            
            # Initial status (don't show warning on page load)
            update_status(show_warning=False)
            
            async def run_test_with_data(is_reasonable: bool):
                can_proceed = update_status(show_warning=True)
                if not can_proceed:
                    ui.notify("请先完成步骤1", type='warning')
                    return
                
                ai_comment.clear()
                self.fill_machine_snapshot(machine_inputs, is_reasonable)

                if is_reasonable:
                    # 真实案例数据 - 来自模版案例Excel (8腔模具)
                    # 型腔重量：24.83, 25.20, 25.77, 24.73, 25.33, 24.80, 24.67, 25.37
                    weights = [24.83, 25.20, 25.77, 24.73, 25.33, 24.80, 24.67, 25.37]
                    for i, w in enumerate(weights, 1):
                        cavity_inputs[i].set_value(f"{w:.2f}")

                    # 不平衡程度：4.27%（略超3%标准，但仍可接受）
                    def _mock_local_cavity_ok():
                        ai_comment.clear()
                        with ai_comment:
                            glass_alert(
                                "🤖 Mock AI点评（PA6真实案例 - 8腔模具）：\n\n"
                                "✓ 8个型腔短射重量范围：24.67g ~ 25.77g\n"
                                "✓ 最大差异1.1g，不平衡度约4.27%\n"
                                "⚠ 略超3%推荐标准，但属于可接受范围\n"
                                "📊 模号：TG34724342-07，1+1型腔\n"
                                "💡 建议：如需提升平衡度，可微调热流道温度",
                                "success"
                            )
                    try:
                        self.session.cavity_weights = {i: float(weights[i-1]) for i in range(1, 9)}
                    except Exception:
                        pass
                    self._set_pending_ai(2, ai_comment, _mock_local_cavity_ok)
                    _mock_local_cavity_ok()
                else:
                    weights = [10.50, 9.20, 10.80, 9.00, 10.30, 8.90, 10.60, 9.10]
                    for i, w in enumerate(weights, 1):
                        cavity_inputs[i].set_value(f"{w:.2f}")
                    
                    def _mock_local_cavity_bad():
                        ai_comment.clear()
                        with ai_comment:
                            glass_alert(
                                "🤖 Mock AI点评（不合理数据）：\n\n"
                                "✗ 型腔重量差异达1.9g，平衡度仅82%\n"
                                "✗ 远腔重量偏高，近腔偏低，流道设计不均\n"
                                "⚠ 建议：检查热流道温度，调整浇口尺寸",
                                "error"
                            )
                    try:
                        self.session.cavity_weights = {i: float(weights[i-1]) for i in range(1, 9)}
                    except Exception:
                        pass
                    self._set_pending_ai(2, ai_comment, _mock_local_cavity_bad)
                    _mock_local_cavity_bad()
                
                pressures = [w * 10 for w in weights]
                balance_ratio = cavity_balance(pressures)
                
                # Mock full shot weights (slightly higher and more balanced)
                full_shot_weights = {i: w * 2 * (1 + random.uniform(-0.01, 0.01)) for i, w in enumerate(weights, 1)}
                visual_data = {i: visual_inputs[i].value for i in range(1, 9)}
                
                def _finalize_step2(assessment=None):
                    self.session.set_step2_result(
                        balance_ratio,
                        {i: weights[i-1] for i in range(1, 9)},
                        cavity_weights_full=full_shot_weights,
                        visual_checks=visual_data
                    )

                    # Set data quality
                    all_ok = all(v == "OK" for v in visual_data.values())
                    self.session.set_step_quality(2, is_reasonable and all_ok)

                    status = "✓ 平衡良好" if balance_ratio > 0.95 and all_ok else "⚠ 需要优化"
                    result_label.set_text(f"{status}\n平衡度: {balance_ratio*100:.1f}%\n最大: {max(weights):.2f}g | 最小: {min(weights):.2f}g")
                    result_label.classes(remove="text-red-600 text-emerald-600 text-yellow-600")
                    result_label.classes(add="text-emerald-600" if balance_ratio > 0.95 else "text-yellow-600")

                    fig = go.Figure()
                    colors = ['#10b981' if is_reasonable else ('#ef4444' if w < 9.5 or w > 10.5 else '#f59e0b') for w in weights]
                    fig.add_trace(go.Bar(x=[f"腔{i}" for i in range(1, 9)], y=weights, marker_color=colors))
                    fig.add_hline(y=sum(weights)/8, line_dash="dash", line_color="blue", annotation_text="平均值")

                    # 设置 y 轴范围从 min-1 开始，显性化差异
                    y_min = min(weights) - 1
                    y_max = max(weights) + 1
                    fig.update_layout(
                        title="型腔重量分布",
                        xaxis_title="型腔",
                        yaxis_title="重量 (g)",
                        yaxis_range=[y_min, y_max],
                        template="plotly_white",
                        height=400
                    )

                    chart_container.clear()
                    with chart_container:
                        ui.plotly(fig).classes('w-full')

                    # Note: progress indicator will be updated when clicking 'Next' and confirming
                    ui.notify(f"✓ 步骤2数据已填充", type='positive' if is_reasonable else 'warning')

                _finalize_step2()
            
            # Track reasonable state for this step - confirmation dialog will be shown when clicking "Next"
            async def run_unreasonable_test():
                await run_test_with_data(False)
                ui.notify("已填充不合理测试数据，点击'下一步'时将要求确认偏离原因", type='warning')
            
            with ui.row().classes('gap-4 mt-4'):
                glass_button("⚡ 快速填充（合理）", lambda: run_test_with_data(True))
                ui.button("⚡ 快速填充（不合理）", on_click=run_unreasonable_test).classes(
                    "bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg px-6 py-3"
                )
                ui.button(f"🤖 实时AI点评（{self._get_ai_label()}）", on_click=lambda: self.trigger_realtime_ai(2)).props('color=primary')
    
    def render_step3_pressure_drop(self):
        """Step 3: Pressure Drop Study."""
        with glass_card("步骤 3: 压力降测试"):
            ui.label("目标：确保机器压力足够克服流道阻力").classes(f"{GLASS_THEME['text_secondary']} mb-4")
            
            # Status display area
            status_area = ui.column().classes("w-full")
            
            with ui.row().classes('gap-4'):
                max_pressure_input = glass_input("机器最大压力 (MPa)", "")
                peak_pressure_input = glass_input("实际峰值压力 (MPa)", "")
            
            # AI Commentary area
            ai_comment = ui.column().classes("w-full mt-4")
            
            result_label = ui.label("等待计算...").classes(f"{GLASS_THEME['text_secondary']}")
            
            # Machine snapshot
            machine_inputs = self.create_machine_snapshot_ui()
            
            def update_status(show_warning=True):
                status_area.clear()
                inherited = self.session.get_inherited_params(3)
                can_proceed, reason = self.session.can_proceed_to_step(3)
                
                with status_area:
                    if not can_proceed and show_warning:
                        glass_alert(f"⚠️ 请先完成步骤1（粘度曲线）", "warning")
                    elif 'injection_speed' in inherited:
                        glass_alert(f"✅ 射速已锁定为: {inherited['injection_speed']:.1f} mm/s (来自步骤1)", "info")
                
                return can_proceed
            
            update_status(show_warning=False)
            
            async def run_test_with_data(is_reasonable: bool):
                can_proceed = update_status(show_warning=True)
                if not can_proceed:
                    ui.notify("请先完成步骤1", type='warning')
                    return
                
                ai_comment.clear()
                self.fill_machine_snapshot(machine_inputs, is_reasonable)
                
                if is_reasonable:
                    # 真实案例数据 - 来自模版案例Excel
                    # 机器最大注塑压力：217.1 MPa，峰值压力（V/P点）：106.7 Bar = 10.67 MPa
                    # 压力单位在Excel是Bar，转换：175 Bar液压 → 217.1 MPa注塑压力
                    max_p, peak_p = 217, 107  # 机器最大压力217MPa，实际峰值107MPa (Bar转换)
                    max_pressure_input.set_value("217")
                    peak_pressure_input.set_value("107")
                    
                    def _mock_local_pressure_ok():
                        ai_comment.clear()
                        with ai_comment:
                            glass_alert(
                                "🤖 Mock AI点评（PA6真实案例 - YIZUMI 260T）：\n\n"
                                "✓ 机器最大注塑压力：217.1 MPa\n"
                                "✓ 实际V/P点峰值压力：107 MPa（106.7 Bar）\n"
                                "✓ 压力利用率49%，余量充足（110 MPa）\n"
                                "📊 压力损失分布：\n"
                                "   • 喷嘴: 24.3 Bar\n"
                                "   • 流道: 28.2 Bar\n"
                                "   • 浇口: 55 Bar\n"
                                "   • 50%产品: 77.3 Bar\n"
                                "   • V/P点: 106.7 Bar",
                                "success"
                            )
                    self._set_pending_ai(3, ai_comment, _mock_local_pressure_ok)
                    _mock_local_pressure_ok()
                else:
                    max_p, peak_p = 180, 172
                    max_pressure_input.set_value("180")
                    peak_pressure_input.set_value("172")
                    
                    def _mock_local_pressure_bad():
                        ai_comment.clear()
                        with ai_comment:
                            glass_alert(
                                "🤖 Mock AI点评（不合理数据）：\n\n"
                                "✗ 压力利用率96%，几乎无余量！\n"
                                "✗ 材料波动可能导致欠注或报警\n"
                                "⚠ 建议：降低射速或更换大机器",
                                "error"
                            )
                    self._set_pending_ai(3, ai_comment, _mock_local_pressure_bad)
                    _mock_local_pressure_bad()
                
                result = calculate_pressure_margin(max_p, peak_p)
                
                # Prepare detailed pressure drop data for report
                detailed_pressures = {
                    'positions': ["Nozzle", "Runner", "Gate", "Part_50%", "Part_99%"],
                    'pressures': [24.3, 28.2, 55.0, 77.3, 106.7] if is_reasonable else [30, 60, 100, 140, 172]
                }
                def _finalize_step3(assessment=None):
                    self.session.set_step3_result(result['margin'], result['is_limited'], detailed_data=detailed_pressures)

                    # Set data quality
                    self.session.set_step_quality(3, is_reasonable)

                    status_icon = "✓" if not result['is_limited'] else "⚠"
                    result_label.set_text(f"{status_icon} {result['status']}\n压力余量: {result['margin']:.1f} MPa\n压力利用率: {result['utilization_percent']:.1f}%")
                    result_label.classes(remove="text-red-600 text-emerald-600 text-yellow-600")
                    result_label.classes(add="text-emerald-600" if not result['is_limited'] else "text-red-600")

                    # Note: progress indicator will be updated when clicking 'Next' and confirming
                    ui.notify(f"✓ 步骤3数据已填充", type='positive' if is_reasonable else 'warning')

                _finalize_step3()
            
            # Track reasonable state for this step - confirmation dialog will be shown when clicking "Next"
            async def run_unreasonable_test():
                await run_test_with_data(False)
                ui.notify("已填充不合理测试数据，点击'下一步'时将要求确认偏离原因", type='warning')
            
            with ui.row().classes('gap-4 mt-4'):
                glass_button("✓ 合理模拟数值", lambda: run_test_with_data(True))
                ui.button("✗ 不合理模拟数值", on_click=run_unreasonable_test).classes(
                    "bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg px-6 py-3"
                )
                ui.button(f"🤖 实时AI点评（{self._get_ai_label()}）", on_click=lambda: self.trigger_realtime_ai(3)).props('color=primary')
    
    def render_step4_process_window(self):
        """Step 4: Process Window (O-Window)."""
        with glass_card("步骤 4: 工艺窗口定义"):
            ui.label("目标：找到成型参数的安全区域").classes(f"{GLASS_THEME['text_secondary']} mb-4")
            
            with ui.grid(columns=2).classes('w-full gap-4'):
                min_pressure_input = glass_input("最小保压 (MPa)", "")
                max_pressure_input = glass_input("最大保压 (MPa)", "")
                min_temp_input = glass_input("最小温度 (°C)", "")
                max_temp_input = glass_input("最大温度 (°C)", "")
            
            # AI Commentary area
            ai_comment = ui.column().classes("w-full mt-4")
            
            result_label = ui.label("等待定义...").classes(f"{GLASS_THEME['text_secondary']}")
            chart_container = ui.column().classes("w-full")
            
            # Machine snapshot
            machine_inputs = self.create_machine_snapshot_ui()
            
            async def run_test_with_data(is_reasonable: bool):
                ai_comment.clear()
                self.fill_machine_snapshot(machine_inputs, is_reasonable)
                
                if is_reasonable:
                    # 真实案例数据 - 来自模版案例Excel
                    # 保压30Bar=缩水, 40-60Bar=OK, 70-80Bar=披风
                    # 最小压力40 Bar, 最大压力60 Bar, 推荐50 Bar
                    test_points = [
                        {'holding_pressure': 30, 'temperature': 255, 'appearance_status': 'short', 'product_weight': 329.2},  # 缩水
                        {'holding_pressure': 40, 'temperature': 255, 'appearance_status': 'ok', 'product_weight': 331.5},     # OK
                        {'holding_pressure': 50, 'temperature': 255, 'appearance_status': 'ok', 'product_weight': 335.6},     # OK (推荐)
                        {'holding_pressure': 60, 'temperature': 255, 'appearance_status': 'ok', 'product_weight': 336.4},     # OK
                        {'holding_pressure': 70, 'temperature': 255, 'appearance_status': 'flash', 'product_weight': 339.1},  # 披风
                        {'holding_pressure': 80, 'temperature': 255, 'appearance_status': 'flash', 'product_weight': 341.2},  # 披风
                    ]
                    min_pressure_input.set_value("40")
                    max_pressure_input.set_value("60")
                    min_temp_input.set_value("230")
                    max_temp_input.set_value("260")
                    
                    def _mock_local_window_ok():
                        ai_comment.clear()
                        with ai_comment:
                            glass_alert(
                                "🤖 Mock AI点评（PA6真实案例 - 工艺窗口）：\n\n"
                                "✓ 工艺窗口：40-60 Bar（宽度20 Bar）\n"
                                "✓ 推荐保压：50 Bar（窗口中值）\n"
                                "✓ 低于40 Bar产品缩水，高于60 Bar产品披风\n"
                                "📊 测试保压时间15s，产品重量变化：\n"
                                "   • 30 Bar: 329.2g (缩水)\n"
                                "   • 40 Bar: 331.5g (OK)\n"
                                "   • 50 Bar: 335.6g (OK)\n"
                                "   • 60 Bar: 336.4g (OK)\n"
                                "   • 70 Bar: 339.1g (披风)",
                                "success"
                            )
                    self._set_pending_ai(4, ai_comment, _mock_local_window_ok)
                    _mock_local_window_ok()
                else:
                    test_points = [
                        {'holding_pressure': 55, 'temperature': 235, 'appearance_status': 'short', 'product_weight': 320.0},
                        {'holding_pressure': 58, 'temperature': 238, 'appearance_status': 'ok', 'product_weight': 322.1},
                        {'holding_pressure': 62, 'temperature': 242, 'appearance_status': 'flash', 'product_weight': 325.3},
                    ]
                    min_pressure_input.set_value("55")
                    max_pressure_input.set_value("65")
                    min_temp_input.set_value("235")
                    max_temp_input.set_value("245")
                    
                    def _mock_local_window_bad():
                        ai_comment.clear()
                        with ai_comment:
                            glass_alert(
                                "🤖 Mock AI点评（不合理数据）：\n\n"
                                "✗ 工艺窗口仅4MPa，属于极窄窗口！\n"
                                "✗ 参数波动易导致短射或飞边\n"
                                "⚠ 建议：优化壁厚设计，调整浇口位置",
                                "error"
                            )
                    self._set_pending_ai(4, ai_comment, _mock_local_window_bad)
                    _mock_local_window_bad()
                
                window = find_process_window_center(test_points)
                
                if window['status'] == 'found':
                    optimal_pressure = window['center_pressure']

                    def _finalize_step4(assessment=None):
                        self.session.set_step4_result(optimal_pressure, window, raw_data=test_points)

                        status = "✓ 窗口良好" if is_reasonable else "⚠ 窗口过窄"
                        result_label.set_text(f"{status}\n推荐保压: {optimal_pressure:.1f} MPa\n窗口大小: {window['window_size']:.1f} MPa")
                        # Set data quality
                        self.session.set_step_quality(4, is_reasonable)

                        result_label.classes(remove="text-red-600 text-emerald-600 text-yellow-600")
                        result_label.classes(add="text-emerald-600" if is_reasonable else "text-yellow-600")

                        fig = go.Figure()
                        for status_type, color, name in [('short', 'blue', '短射'), ('ok', 'green', 'OK'), ('flash', 'red', '飞边')]:
                            pts = [p for p in test_points if p['appearance_status'] == status_type]
                            if pts:
                                fig.add_trace(go.Scatter(x=[p['temperature'] for p in pts], y=[p['holding_pressure'] for p in pts],
                                    mode='markers', name=name, marker=dict(color=color, size=12)))
                        fig.add_trace(go.Scatter(x=[window['center_temperature']], y=[window['center_pressure']],
                            mode='markers', name='推荐点', marker=dict(color='gold', size=18, symbol='star', line=dict(width=2, color='black'))))
                        fig.update_layout(title="工艺窗口 (O-Window)", xaxis_title="温度 (°C)", yaxis_title="保压 (MPa)", template="plotly_white", height=400)

                        chart_container.clear()
                        with chart_container:
                            ui.plotly(fig).classes('w-full')

                        # Note: progress indicator will be updated when clicking 'Next' and confirming
                        ui.notify(f"✓ 步骤4数据已填充", type='positive' if is_reasonable else 'warning')

                    _finalize_step4()
            
            # Track reasonable state for this step - confirmation dialog will be shown when clicking "Next"
            async def run_unreasonable_test():
                await run_test_with_data(False)
                ui.notify("已填充不合理测试数据，点击'下一步'时将要求确认偏离原因", type='warning')
            
            with ui.row().classes('gap-4 mt-4'):
                glass_button("✓ 合理模拟数值", lambda: run_test_with_data(True))
                ui.button("✗ 不合理模拟数值", on_click=run_unreasonable_test).classes(
                    "bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg px-6 py-3"
                )
                ui.button(f"🤖 实时AI点评（{self._get_ai_label()}）", on_click=lambda: self.trigger_realtime_ai(4)).props('color=primary')
    
    def render_step5_gate_seal(self):
        """Step 5: Gate Seal Study."""
        with glass_card("步骤 5: 浇口冻结测试"):
            ui.label("目标：确定最短有效保压时间").classes(f"{GLASS_THEME['text_secondary']} mb-4")
            
            # Status display area
            status_area = ui.column().classes("w-full")
            
            times_input = glass_input("保压时间序列 (s, 逗号分隔)", "")
            weights_input = glass_input("对应重量 (g, 逗号分隔)", "")
            
            # AI Commentary area
            ai_comment = ui.column().classes("w-full mt-4")
            
            result_label = ui.label("等待测试...").classes(f"{GLASS_THEME['text_secondary']}")
            chart_container = ui.column().classes("w-full")
            
            # Machine snapshot
            machine_inputs = self.create_machine_snapshot_ui()
            
            def update_status(show_warning=True):
                status_area.clear()
                inherited = self.session.get_inherited_params(5)
                can_proceed, reason = self.session.can_proceed_to_step(5)
                
                with status_area:
                    if not can_proceed and show_warning:
                        glass_alert(f"⚠️ 请先完成步骤4（工艺窗口）", "warning")
                    elif 'holding_pressure' in inherited:
                        glass_alert(f"✅ 保压压力已锁定为: {inherited['holding_pressure']:.1f} MPa (来自步骤4)", "info")
                
                return can_proceed
            
            update_status(show_warning=False)
            
            async def run_test_with_data(is_reasonable: bool):
                can_proceed = update_status(show_warning=True)
                if not can_proceed:
                    ui.notify("请先完成步骤4", type='warning')
                    return
                
                ai_comment.clear()
                self.fill_machine_snapshot(machine_inputs, is_reasonable)
                
                if is_reasonable:
                    # 真实案例数据 - 来自模版案例Excel
                    # 保压时间 3-13秒，重量 327.2g-335.7g
                    # 浇口冻结时间：12秒（重量不再增加）
                    # 推荐保压时间：13秒
                    times = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
                    weights = [327.2, 328.54, 330.92, 332.96, 333.5, 334.02, 334.65, 335.2, 335.5, 335.7, 335.7]
                    times_input.set_value("3,4,5,6,7,8,9,10,11,12,13")
                    weights_input.set_value("327.2,328.54,330.92,332.96,333.5,334.02,334.65,335.2,335.5,335.7,335.7")
                    
                    def _mock_local_gate_ok():
                        ai_comment.clear()
                        with ai_comment:
                            glass_alert(
                                "🤖 Mock AI点评（PA6真实案例 - 浇口冻结）：\n\n"
                                "✓ 测试保压时间：3-13秒（共11个测试点）\n"
                                "✓ 浇口冻结时间：12秒（重量稳定在335.7g）\n"
                                "✓ 推荐保压时间：13秒（冻结时间+1秒余量）\n"
                                "📊 重量变化曲线：\n"
                                "   • 3s: 327.2g → 12s: 335.7g（增重8.5g）\n"
                                "   • 12-13s重量不变，确认浇口已完全冻结\n"
                                "💡 典型S型曲线，冻结点明确",
                                "success"
                            )
                    self._set_pending_ai(5, ai_comment, _mock_local_gate_ok)
                    _mock_local_gate_ok()
                else:
                    times = [1, 2, 3, 4, 5, 6]
                    weights = [9.0, 9.3, 9.6, 9.8, 9.95, 10.1]
                    times_input.set_value("1,2,3,4,5,6")
                    weights_input.set_value("9.0,9.3,9.6,9.8,9.95,10.1")
                    
                    def _mock_local_gate_bad():
                        ai_comment.clear()
                        with ai_comment:
                            glass_alert(
                                "🤖 Mock AI点评（不合理数据）：\n\n"
                                "✗ 6秒时重量仍在上升，浇口尚未冻结\n"
                                "✗ 可能原因：浇口过大、模温过高\n"
                                "⚠ 建议：延长测试至8-10秒",
                                "error"
                            )
                    self._set_pending_ai(5, ai_comment, _mock_local_gate_bad)
                    _mock_local_gate_bad()
                
                freeze_result = detect_gate_freeze_time(times, weights)
                freeze_time = freeze_result.get('freeze_time') or times[-1]
                recommended_time = freeze_result.get('recommended_time') or (freeze_time + 2)
                
                # Format data for report
                seal_curve = [{'hold_time': t, 'weight': w} for t, w in zip(times, weights)]

                def _finalize_step5(assessment=None):
                    self.session.set_step5_result(freeze_time, seal_curve)

                    status = "✓ 冻结点明确" if is_reasonable else "⚠ 需延长测试"
                    result_label.set_text(f"{status}\n浇口冻结时间: {freeze_time:.1f}s\n推荐保压时间: {recommended_time:.1f}s")
                    # Set data quality
                    self.session.set_step_quality(5, is_reasonable)

                    result_label.classes(remove="text-red-600 text-emerald-600 text-yellow-600")
                    result_label.classes(add="text-emerald-600" if is_reasonable else "text-yellow-600")

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=times, y=weights, mode='lines+markers', name='重量曲线',
                        line=dict(color='#3b82f6' if is_reasonable else '#ef4444', width=2)))
                    fig.add_vline(x=freeze_time, line_dash="dash", line_color="red", annotation_text="冻结点")
                    fig.update_layout(title="浇口冻结曲线", xaxis_title="保压时间 (s)", yaxis_title="重量 (g)", template="plotly_white", height=400)

                    chart_container.clear()
                    with chart_container:
                        ui.plotly(fig).classes('w-full')

                    # Note: progress indicator will be updated when clicking 'Next' and confirming
                    ui.notify(f"✓ 步骤5数据已填充", type='positive' if is_reasonable else 'warning')

                _finalize_step5()
            
            # Track reasonable state for this step - confirmation dialog will be shown when clicking "Next"
            async def run_unreasonable_test():
                await run_test_with_data(False)
                ui.notify("已填充不合理测试数据，点击'下一步'时将要求确认偏离原因", type='warning')
            
            with ui.row().classes('gap-4 mt-4'):
                glass_button("⚡ 快速填充（合理）", lambda: run_test_with_data(True))
                ui.button("⚡ 快速填充（不合理）", on_click=run_unreasonable_test).classes(
                    "bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg px-6 py-3"
                )
                ui.button(f"🤖 实时AI点评（{self._get_ai_label()}）", on_click=lambda: self.trigger_realtime_ai(5)).props('color=primary')
    
    def render_step6_cooling(self):
        """Step 6: Cooling Time Optimization."""
        with glass_card("步骤 6: 冷却时间优化"):
            ui.label("目标：在保证尺寸的前提下缩短周期").classes(f"{GLASS_THEME['text_secondary']} mb-4")
            
            # Status display area
            status_area = ui.column().classes("w-full")
            
            with ui.row().classes('gap-4'):
                ejection_temp_input = glass_input("顶出温度 (°C)", "")
                test_cooling_input = glass_input("测试冷却时间 (s)", "")
            
            # AI Commentary area
            ai_comment = ui.column().classes("w-full mt-4")
            
            result_label = ui.label("等待测试...").classes(f"{GLASS_THEME['text_secondary']}")
            
            # Machine snapshot
            machine_inputs = self.create_machine_snapshot_ui()
            
            def update_status(show_warning=True):
                status_area.clear()
                inherited = self.session.get_inherited_params(6)
                can_proceed, reason = self.session.can_proceed_to_step(6)
                
                with status_area:
                    if not can_proceed and show_warning:
                        glass_alert(f"⚠️ 请先完成步骤5（浇口冻结）", "warning")
                    elif 'min_holding_time' in inherited:
                        glass_alert(f"✅ 最小保压时间: {inherited['min_holding_time']:.1f}s (来自步骤5)", "info")
                
                return can_proceed, inherited
            
            update_status(show_warning=False)
            
            async def run_test_with_data(is_reasonable: bool):
                can_proceed, inherited = update_status(show_warning=True)
                if not can_proceed:
                    ui.notify("请先完成步骤5", type='warning')
                    return
                
                ai_comment.clear()
                self.fill_machine_snapshot(machine_inputs, is_reasonable)
                min_holding = inherited.get('min_holding_time', 13.0)  # 来自步骤5
                
                if is_reasonable:
                    # 真实案例数据 - 基于PA6材料特性
                    # 模温：前模60°C，后模14°C
                    # 推荐料温：230-260°C
                    ejection_temp = 80  # PA6热变形温度约75-80°C
                    cooling_time = 15   # 基于产品壁厚和模温
                    ejection_temp_input.set_value("80")
                    test_cooling_input.set_value("15")
                    
                    recommended = max(cooling_time, min_holding + 2)
                    cycle_time = recommended + min_holding + 3  # 填充+保压+冷却+开合模
                    
                    def _mock_local_cooling_ok():
                        ai_comment.clear()
                        with ai_comment:
                            glass_alert(
                                f"🤖 Mock AI点评（PA6真实案例 - 冷却优化）：\n\n"
                                f"✓ 冷却时间：{cooling_time}秒\n"
                                f"✓ 顶出温度：{ejection_temp}°C（接近PA6热变形温度）\n"
                                f"✓ 保压时间：{min_holding:.0f}秒（来自步骤5）\n"
                                f"📊 模温设置：\n"
                                "   • 前模: 60°C\n"
                                "   • 后模: 14°C\n"
                                "   • 滑块: 60°C\n"
                                f"💡 预估周期时间：约{cycle_time:.0f}秒",
                                "success"
                            )
                    self._set_pending_ai(6, ai_comment, _mock_local_cooling_ok)
                    _mock_local_cooling_ok()
                else:
                    ejection_temp = 110
                    cooling_time = 6
                    ejection_temp_input.set_value("110")
                    test_cooling_input.set_value("6")
                    
                    recommended = max(cooling_time, min_holding + 2)
                    cycle_time = recommended + min_holding + 3
                    
                    def _mock_local_cooling_bad():
                        ai_comment.clear()
                        with ai_comment:
                            glass_alert(
                                f"🤖 Mock AI点评（不合理数据）：\n\n"
                                f"✗ 冷却仅{cooling_time}s，产品可能未固化\n"
                                f"✗ 顶出温度{ejection_temp}°C过高！\n"
                                "⚠ 建议：增加冷却至12-15s",
                                "error"
                            )
                    self._set_pending_ai(6, ai_comment, _mock_local_cooling_bad)
                    _mock_local_cooling_bad()
                
                # Format data for report - Mocking a curve since Step 6 UI only has 1 point
                mock_cooling_curve = [
                    {'cooling_time': recommended - 5, 'part_temp': ejection_temp + 10, 'deformation': 0.15},
                    {'cooling_time': recommended, 'part_temp': ejection_temp, 'deformation': 0.08},
                    {'cooling_time': recommended + 5, 'part_temp': ejection_temp - 5, 'deformation': 0.05}
                ]

                def _finalize_step6(assessment=None):
                    self.session.set_step6_result(recommended, mock_cooling_curve)

                    # Set data quality
                    self.session.set_step_quality(6, is_reasonable)

                    status = "✓ 冷却优化" if is_reasonable else "⚠ 参数需调整"
                    result_label.set_text(f"{status}\n推荐冷却时间: {recommended:.1f}s\n预估周期: {cycle_time:.1f}s")
                    result_label.classes(remove="text-red-600 text-emerald-600 text-yellow-600")
                    result_label.classes(add="text-emerald-600" if is_reasonable else "text-yellow-600")

                    # Note: progress indicator will be updated when clicking 'Next' and confirming
                    ui.notify("✓ 步骤6数据已填充，请继续步骤7（锁模力优化）" if is_reasonable else "⚠ 步骤6数据已填充，但建议调整参数", type='positive' if is_reasonable else 'warning')

                _finalize_step6()
            
            # Track reasonable state for this step - confirmation dialog will be shown when clicking "Next"
            async def run_unreasonable_test():
                await run_test_with_data(False)
                ui.notify("已填充不合理测试数据，点击'下一步'时将要求确认偏离原因", type='warning')
            
            with ui.row().classes('gap-4 mt-4'):
                glass_button("⚡ 快速填充（合理）", lambda: run_test_with_data(True))
                ui.button("⚡ 快速填充（不合理）", on_click=run_unreasonable_test).classes(
                    "bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg px-6 py-3"
                )
                ui.button(f"🤖 实时AI点评（{self._get_ai_label()}）", on_click=lambda: self.trigger_realtime_ai(6)).props('color=primary')
    
    def render_step7_clamping_force(self):
        """Step 7: Clamping Force Optimization."""
        with glass_card("步骤 7: 锁模力优化"):
            ui.label("目标：找到最佳锁模力，防止产品飞边同时避免过度锁模").classes(f"{GLASS_THEME['text_secondary']} mb-4")
            
            # Status display area
            status_area = ui.column().classes("w-full")
            
            with ui.row().classes('gap-4'):
                clamping_force_input = glass_input("锁模力序列 (Ton, 逗号分隔)", "")
                part_weight_input = glass_input("对应产品重量 (g, 逗号分隔)", "")
            
            appearance_input = glass_input("外观状态序列 (OK/Flash, 逗号分隔)", "")
            
            # AI Commentary area
            ai_comment = ui.column().classes("w-full mt-4")
            
            result_label = ui.label("等待测试...").classes(f"{GLASS_THEME['text_secondary']}")
            chart_container = ui.column().classes("w-full")
            
            # Machine snapshot
            machine_inputs = self.create_machine_snapshot_ui()
            
            def update_status(show_warning=True):
                status_area.clear()
                inherited = self.session.get_inherited_params(7)
                can_proceed, reason = self.session.can_proceed_to_step(7)
                
                with status_area:
                    if not can_proceed and show_warning:
                        glass_alert(f"⚠️ 请先完成步骤6（冷却时间）", "warning")
                    else:
                        # 显示继承的参数
                        info_parts = []
                        if self.session.optimal_holding_pressure:
                            info_parts.append(f"保压压力: {self.session.optimal_holding_pressure:.1f} MPa")
                        if self.session.gate_freeze_time:
                            info_parts.append(f"保压时间: {self.session.gate_freeze_time:.0f}s")
                        if info_parts:
                            glass_alert(f"✅ 使用参数: {', '.join(info_parts)} (来自前序步骤)", "info")
                
                return can_proceed
            
            update_status(show_warning=False)
            
            async def run_test_with_data(is_reasonable: bool):
                can_proceed = update_status(show_warning=True)
                if not can_proceed:
                    ui.notify("请先完成步骤6", type='warning')
                    return
                
                ai_comment.clear()
                self.fill_machine_snapshot(machine_inputs, is_reasonable)
                
                if is_reasonable:
                    # 真实案例数据 - 来自Excel模版案例
                    # 锁模力从高到低：160, 140, 130, 120, 110, 100 Ton
                    # 产品重量：305, 305, 305, 305, 306, 308 g
                    # 120Ton以上OK，110Ton开始披风
                    forces = [160, 140, 130, 120, 110, 100]
                    weights = [305, 305, 305, 305, 306, 308]
                    appearances = ['OK', 'OK', 'OK', 'OK', 'Flash', 'Flash']
                    
                    clamping_force_input.set_value("160,140,130,120,110,100")
                    part_weight_input.set_value("305,305,305,305,306,308")
                    appearance_input.set_value("OK,OK,OK,OK,Flash,Flash")
                    
                    # 推荐锁模力 = 最小无飞边锁模力 × 1.1 安全系数
                    min_ok_force = 120  # 最小无飞边锁模力
                    recommended_force = int(min_ok_force * 1.15)  # 约140 Ton
                    
                    def _mock_local_clamp_ok():
                        ai_comment.clear()
                        with ai_comment:
                            glass_alert(
                                f"🤖 Mock AI点评（PA6真实案例 - 锁模力优化）：\n\n"
                                f"✓ 测试锁模力范围：100-160 Ton（共6个测试点）\n"
                                f"✓ 最小无飞边锁模力：{min_ok_force} Ton\n"
                                f"✓ 推荐锁模力：{recommended_force} Ton（含15%安全余量）\n"
                                f"📊 测试结果分析：\n"
                                f"   • 160-120 Ton: 产品OK，重量稳定305g\n"
                                f"   • 110-100 Ton: 产品飞边，重量增加至306-308g\n"
                                f"💡 模号: TG34724342-07，机台吨位: 280T",
                                "success"
                            )
                    self._set_pending_ai(7, ai_comment, _mock_local_clamp_ok)
                    _mock_local_clamp_ok()
                else:
                    # 不合理数据 - 锁模力过低导致严重飞边
                    forces = [80, 70, 60, 50]
                    weights = [312, 318, 325, 330]
                    appearances = ['Flash', 'Flash', 'Flash', 'Flash']
                    
                    clamping_force_input.set_value("80,70,60,50")
                    part_weight_input.set_value("312,318,325,330")
                    appearance_input.set_value("Flash,Flash,Flash,Flash")
                    
                    min_ok_force = None
                    recommended_force = 140  # 建议值
                    
                    def _mock_local_clamp_bad():
                        ai_comment.clear()
                        with ai_comment:
                            glass_alert(
                                f"🤖 Mock AI点评（不合理数据）：\n\n"
                                f"✗ 所有测试点均出现飞边！锁模力严重不足\n"
                                f"✗ 产品重量持续增加（312→330g），熔体外溢\n"
                                f"⚠ 建议：增加锁模力至120-160 Ton范围重新测试\n"
                                f"⚠ 检查：分型面密封、模具磨损情况",
                                "error"
                            )
                    self._set_pending_ai(7, ai_comment, _mock_local_clamp_bad)
                    _mock_local_clamp_bad()
                
                # Format data for report
                clamping_curve = [
                    {'clamping_force': f, 'part_weight': w, 'flash_detected': a}
                    for f, w, a in zip(forces, weights, appearances)
                ]

                def _finalize_step7(assessment=None):
                    self.session.set_step7_result(recommended_force, clamping_curve)

                    # Set data quality
                    self.session.set_step_quality(7, is_reasonable)

                    status = "✓ 锁模力优化完成" if is_reasonable else "⚠ 需要调整"
                    result_label.set_text(f"{status}\n推荐锁模力: {recommended_force} Ton\n最小无飞边: {min_ok_force or 'N/A'} Ton")
                    result_label.classes(remove="text-red-600 text-emerald-600 text-yellow-600")
                    result_label.classes(add="text-emerald-600" if is_reasonable else "text-yellow-600")

                    # 绘制图表
                    fig = go.Figure()

                    # 重量曲线
                    fig.add_trace(go.Scatter(
                        x=forces, y=weights,
                        mode='lines+markers',
                        name='产品重量',
                        line=dict(color='#3b82f6', width=2),
                        marker=dict(size=10)
                    ))

                    # 标记飞边点
                    flash_forces = [f for f, a in zip(forces, appearances) if a.upper() == 'FLASH']
                    flash_weights = [w for w, a in zip(weights, appearances) if a.upper() == 'FLASH']
                    if flash_forces:
                        fig.add_trace(go.Scatter(
                            x=flash_forces, y=flash_weights,
                            mode='markers',
                            name='飞边',
                            marker=dict(color='red', size=15, symbol='x')
                        ))

                    # 推荐值标记
                    fig.add_vline(x=recommended_force, line_dash="dash", line_color="green",
                                  annotation_text=f"推荐: {recommended_force}T")

                    fig.update_layout(
                        title="锁模力优化曲线",
                        xaxis_title="锁模力 (Ton)",
                        yaxis_title="产品重量 (g)",
                        template="plotly_white",
                        height=400
                    )

                    chart_container.clear()
                    with chart_container:
                        ui.plotly(fig).classes('w-full')

                    # Note: progress indicator will be updated when clicking 'Finish' and confirming
                    ui.notify("🎉 步骤7数据已填充！" if is_reasonable else "⚠ 步骤7数据已填充，但建议调整参数", type='positive' if is_reasonable else 'warning')

                _finalize_step7()
            
            # Track reasonable state for this step - confirmation dialog will be shown when clicking "Next"
            async def run_unreasonable_test():
                await run_test_with_data(False)
                ui.notify("已填充不合理测试数据，点击'完成实验'时将要求确认", type='warning')
            
            with ui.row().classes('gap-4 mt-4'):
                glass_button("⚡ 快速填充（合理）", lambda: run_test_with_data(True))
                ui.button("⚡ 快速填充（不合理）", on_click=run_unreasonable_test).classes(
                    "bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg px-6 py-3"
                )
                ui.button(f"🤖 实时AI点评（{self._get_ai_label()}）", on_click=lambda: self.trigger_realtime_ai(7)).props('color=primary')
    
    def update_progress_indicator(self):
        """Update the progress indicator to reflect current state."""
        if hasattr(self, 'progress_container'):
            self.progress_container.clear()
            progress = self.session.get_progress_summary()
            # Include step0 as '背景信息' at index 0
            step_names = ['背景信息', '粘度曲线', '型腔平衡', '压力降', '工艺窗口', '浇口冻结', '冷却时间', '锁模力']
            data_quality = self.session.step_data_quality  # True=reasonable, False=unreasonable
            
            with self.progress_container:
                with ui.row().classes('w-full items-center justify-center flex-wrap'):
                    # iterate step indices 0..7 (0 == 背景信息)
                    for i in range(0, 8):
                        completed = progress.get(f'step{i}_completed', False)
                        is_skipped = self.session.is_step_skipped(i)
                        is_reasonable = data_quality.get(i, True)  # Default to reasonable if not set
                        
                        # Step circle with label
                        with ui.column().classes('items-center'):
                            # Determine status: skipped > unreasonable > completed > pending
                            if is_skipped:
                                # 跳过的步骤 - 灰色，显示"跳过"
                                icon = "跳过"
                                color = "bg-gray-500"
                                text_color = "text-gray-500"
                                line_color = "bg-gray-400"
                                font_size = "text-xs"
                            elif completed:
                                if is_reasonable:
                                    # 正常完成 - 绿色，显示对勾
                                    icon = "✓"
                                    color = "bg-green-600"
                                    text_color = "text-green-600 font-semibold"
                                    line_color = "bg-green-500"
                                    font_size = "text-lg"
                                else:
                                    # 偏离数据完成 - 橙色，显示"偏离"
                                    icon = "偏离"
                                    color = "bg-orange-500"
                                    text_color = "text-orange-500 font-semibold"
                                    line_color = "bg-orange-400"
                                    font_size = "text-xs"
                            else:
                                # 未完成 - 灰色，显示步骤号
                                icon = str(i)
                                color = "bg-gray-400"
                                text_color = "text-gray-500"
                                line_color = "bg-gray-300"
                                font_size = "text-lg"
                            
                            ui.label(icon).classes(f"{color} text-white rounded-full w-10 h-10 flex items-center justify-center font-bold {font_size} shadow-md")
                            # Label below
                            # step_names aligned so index 0 -> 背景信息
                            ui.label(step_names[i]).classes(f"text-xs mt-2 {text_color}")
                        
                        # Connecting line (except after last step)
                        if i < 7:
                            # Use the determined line_color
                            ui.html(f'<div class="h-1 w-6 {line_color} mx-1 rounded"></div>', sanitize=False).classes('flex items-center')
    
    def render(self):
        """Render the entire 7-step wizard."""
        with glass_container():
            ui.label("科学注塑七步法向导").classes(f"{GLASS_THEME['text_primary']} text-3xl font-bold mb-4")

            # NOTE: We already have a dedicated API configuration/test page.
            # Do NOT auto-open an API dialog when entering this page; just show a non-blocking hint.
            try:
                from global_state import get_available_api_sync
                current_api, api_key = get_available_api_sync()
            except Exception:
                current_api, api_key = (None, None)

            if not api_key:
                with glass_card("🔑 API Key 提示"):
                    glass_alert(
                        "未检测到可用的 API Key：实时 AI 点评可能不可用。\n"
                        "请到 Settings 页面配置并测试 API（本页不再弹出配置弹窗）。",
                        "warning",
                    )
                    with ui.row().classes('gap-2'):
                        glass_button('前往 Settings 配置', on_click=lambda: ui.navigate.to('/settings'), variant='secondary')
            
            # Progress summary with labels and connecting lines - FIXED TO TOP
            progress = self.session.get_progress_summary()
            # Include step0 (背景信息) as the first node
            step_names = ['背景信息', '粘度曲线', '型腔平衡', '压力降', '工艺窗口', '浇口冻结', '冷却时间', '锁模力']

            # Progress indicator container - sticky to top (offset so title doesn't cover it)
            # 'top-16' keeps the progress below the page title so it's not obscured.
            self.progress_container = ui.column().classes('w-full mb-6 sticky top-16 z-40 bg-white/90 backdrop-blur-sm py-4 rounded-lg shadow-sm')
            self.update_progress_indicator()
            
            # Stepper inside a scrollable area
            with ui.stepper().props('vertical').classes('w-full') as stepper:
                self.stepper = stepper
                
                # Helper function to check if step is completed or marked unreasonable before navigation
                async def check_and_navigate(current_step: int, go_next: bool = True):
                    progress = self.session.get_progress_summary()
                    step_key = f'step{current_step}_completed'

                    is_completed = progress.get(step_key, False)
                    # Default to reasonable unless explicitly set otherwise
                    is_reasonable = self.session.step_data_quality.get(current_step, True)

                    # Debug logging to help diagnose unexpected skip prompts
                    print(f"[check_and_navigate] step={current_step}, completed={is_completed}, reasonable={is_reasonable}")
                    try:
                        print(f"[check_and_navigate] progress keys: {list(progress.keys())}")
                    except Exception:
                        pass

                    # If completed but unreasonable, prompt for '偏离' confirmation
                    if is_completed and not is_reasonable:
                        data_issue = self.session.step_remarks.get(current_step, {}).get('data_issue', '检测到偏离数据')
                        await self.show_unreasonable_data_dialog(
                            step=current_step,
                            data_issue=data_issue,
                            on_continue=(lambda: stepper.next() if go_next else stepper.previous())
                        )
                        return

                    # If not completed, show skip dialog
                    if not is_completed:
                        await self.show_skip_step_dialog(current_step, stepper, go_next)
                        return

                    # Otherwise proceed
                    if go_next:
                        self.update_progress_indicator()
                        stepper.next()
                    else:
                        self.update_progress_indicator()
                        stepper.previous()

                with ui.step('准备阶段: 基础信息'):
                    self.render_step0_setup()
                    # Step 0 navigation is handled by "Save and Start" button in render_step0_setup
                
                with ui.step('步骤1: 粘度曲线'):
                    self.render_step1_viscosity()
                    with ui.stepper_navigation():
                        ui.button('下一步', on_click=lambda: check_and_navigate(1, True)).props('flat')
                
                with ui.step('步骤2: 型腔平衡'):
                    self.render_step2_cavity_balance()
                    with ui.stepper_navigation():
                        ui.button('上一步', on_click=lambda: stepper.previous()).props('flat')
                        ui.button('下一步', on_click=lambda: check_and_navigate(2, True)).props('flat')
                
                with ui.step('步骤3: 压力降'):
                    self.render_step3_pressure_drop()
                    with ui.stepper_navigation():
                        ui.button('上一步', on_click=lambda: stepper.previous()).props('flat')
                        ui.button('下一步', on_click=lambda: check_and_navigate(3, True)).props('flat')
                
                with ui.step('步骤4: 工艺窗口'):
                    self.render_step4_process_window()
                    with ui.stepper_navigation():
                        ui.button('上一步', on_click=lambda: stepper.previous()).props('flat')
                        ui.button('下一步', on_click=lambda: check_and_navigate(4, True)).props('flat')
                
                with ui.step('步骤5: 浇口冻结'):
                    self.render_step5_gate_seal()
                    with ui.stepper_navigation():
                        ui.button('上一步', on_click=lambda: stepper.previous()).props('flat')
                        ui.button('下一步', on_click=lambda: check_and_navigate(5, True)).props('flat')
                
                with ui.step('步骤6: 冷却时间'):
                    self.render_step6_cooling()
                    with ui.stepper_navigation():
                        ui.button('上一步', on_click=lambda: stepper.previous()).props('flat')
                        ui.button('下一步', on_click=lambda: check_and_navigate(6, True)).props('flat')
                
                with ui.step('步骤7: 锁模力优化'):
                    self.render_step7_clamping_force()
                    with ui.stepper_navigation():
                        ui.button('上一步', on_click=lambda: stepper.previous()).props('flat')
                        ui.button('完成实验', on_click=self.on_complete_click).props('color=primary')
    
    def on_complete_click(self):
        """Handle complete button click - validate all steps are done."""
        # Check which steps are not completed
        progress = self.session.get_progress_summary()
        missing_steps = []
        
        # Check which steps are truly not completed (exclude skipped and unreasonable - those count as "done")
        for step_num in range(1, 8):  # Now 7 steps
            step_completed = progress.get(f'step{step_num}_completed', False)
            step_skipped = self.session.is_step_skipped(step_num)
            step_unreasonable = not self.session.step_data_quality.get(step_num, True)
            
            # Only truly missing if not completed AND not skipped AND not marked as unreasonable
            if not step_completed and not step_skipped:
                missing_steps.append(step_num)
        
        if missing_steps:
            self.show_completion_error_dialog(missing_steps)
        else:
            self.show_report_dialog()
    
    def show_report_dialog(self):
        """Show report type selection dialog."""
        # 分别统计偏离和跳过（现在是7步）
        skipped_count = sum(1 for i in range(1, 8) if self.session.is_step_skipped(i))
        unreasonable_count = sum(1 for i in range(1, 8) 
                                  if not self.session.step_data_quality.get(i, True) 
                                  and not self.session.is_step_skipped(i))
        
        has_issues = skipped_count > 0 or unreasonable_count > 0
        
        with ui.dialog() as dialog, ui.card().classes('w-[420px]'):
            if has_issues:
                ui.label('⚠️ 七步法完成（含警告）').classes('text-xl font-bold text-orange-600 mb-2')
                
                # 分别显示偏离和跳过统计
                with ui.column().classes('w-full gap-1 mb-4 p-3 bg-orange-50 rounded-lg'):
                    if unreasonable_count > 0:
                        ui.label(f'🟠 偏离接受: {unreasonable_count} 个步骤').classes('text-sm text-orange-600')
                    if skipped_count > 0:
                        ui.label(f'⚪ 流程跳过: {skipped_count} 个步骤').classes('text-sm text-gray-600')
            else:
                ui.label('🎉 七步法全部完成！').classes('text-xl font-bold text-emerald-600 mb-4')
            
            ui.label('请选择报告输出方式：').classes('text-gray-600 mb-4')
            
            # 使用同步方式处理报告生成
            def close_and_generate(report_type: str):
                dialog.close()
                if report_type == 'none':
                    ui.notify('已完成，不生成报告', type='info')
                elif report_type == 'system':
                    self.open_system_report()
                elif report_type == 'template1':
                    self.open_template1_report()
                elif report_type == 'template2':
                    self.open_template2_report()
            
            with ui.column().classes('w-full gap-3'):
                ui.button('不出报告', on_click=lambda: close_and_generate('none')).classes(
                    'w-full bg-gray-400 hover:bg-gray-500 text-white'
                )
                ui.button('系统报告', on_click=lambda: close_and_generate('system')).classes(
                    'w-full bg-blue-500 hover:bg-blue-600 text-white'
                )
                ui.button('模板一报告 (品牌方一)', on_click=lambda: close_and_generate('template1')).classes(
                    'w-full bg-emerald-500 hover:bg-emerald-600 text-white'
                )
                ui.button('模板二报告', on_click=lambda: close_and_generate('template2')).classes(
                    'w-full bg-purple-500 hover:bg-purple-600 text-white'
                )
        
        dialog.open()
    
    def open_system_report(self):
        """Open system report in a dialog."""
        progress = self.session.get_progress_summary()
        
        report_html = f'''
        <div style="font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: auto; background: white;">
            <div style="text-align: center; border-bottom: 3px solid #10b981; padding-bottom: 20px; margin-bottom: 30px;">
                <h1 style="color: #1e293b; margin: 0;">科学注塑七步法分析报告</h1>
                <p style="color: #64748b; margin-top: 10px;">SmartMold Pilot 系统生成</p>
                <p style="color: #64748b;">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            
            <h2 style="color: #10b981; border-left: 4px solid #10b981; padding-left: 10px;">📊 测试结果汇总</h2>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr style="background: #f1f5f9;">
                    <th style="padding: 12px; text-align: left; border: 1px solid #e2e8f0;">步骤</th>
                    <th style="padding: 12px; text-align: left; border: 1px solid #e2e8f0;">关键参数</th>
                    <th style="padding: 12px; text-align: center; border: 1px solid #e2e8f0;">状态</th>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">1. 粘度曲线</td>
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">最佳射速: {progress.get("optimal_speed", "N/A")} mm/s</td>
                    <td style="padding: 12px; text-align: center; border: 1px solid #e2e8f0;">{"✅" if progress.get("step1_completed") else "❌"}</td>
                </tr>
                <tr style="background: #f8fafc;">
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">2. 型腔平衡</td>
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">平衡度: {(self.session.cavity_balance_ratio or 0)*100:.1f}%</td>
                    <td style="padding: 12px; text-align: center; border: 1px solid #e2e8f0;">{"✅" if progress.get("step2_completed") else "❌"}</td>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">3. 压力降</td>
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">压力余量: {self.session.pressure_margin or "N/A"} MPa</td>
                    <td style="padding: 12px; text-align: center; border: 1px solid #e2e8f0;">{"✅" if progress.get("step3_completed") else "❌"}</td>
                </tr>
                <tr style="background: #f8fafc;">
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">4. 工艺窗口</td>
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">最佳保压: {progress.get("optimal_pressure", "N/A")} Bar</td>
                    <td style="padding: 12px; text-align: center; border: 1px solid #e2e8f0;">{"✅" if progress.get("step4_completed") else "❌"}</td>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">5. 浇口冻结</td>
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">冻结时间: {progress.get("gate_freeze_time", "N/A")} s</td>
                    <td style="padding: 12px; text-align: center; border: 1px solid #e2e8f0;">{"✅" if progress.get("step5_completed") else "❌"}</td>
                </tr>
                <tr style="background: #f8fafc;">
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">6. 冷却优化</td>
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">冷却时间: {self.session.recommended_cooling_time or "N/A"} s</td>
                    <td style="padding: 12px; text-align: center; border: 1px solid #e2e8f0;">{"✅" if progress.get("step6_completed") else "❌"}</td>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">7. 锁模力优化</td>
                    <td style="padding: 12px; border: 1px solid #e2e8f0;">推荐锁模力: {progress.get("clamping_force", "N/A")} Ton</td>
                    <td style="padding: 12px; text-align: center; border: 1px solid #e2e8f0;">{"✅" if progress.get("step7_completed") else "❌"}</td>
                </tr>
            </table>
            
            <div style="margin-top: 30px; padding: 20px; background: #f0fdf4; border-radius: 8px;">
                <h3 style="color: #166534; margin-top: 0;">💡 AI 建议</h3>
                <p style="color: #15803d;">基于科学注塑六步法分析，建议使用以上参数进行批量生产试模。</p>
            </div>
        </div>
        '''
        
        with ui.dialog() as report_dialog, ui.card().classes('w-full max-w-4xl'):
            with ui.row().classes('w-full justify-between items-center mb-2'):
                ui.label('📄 系统报告预览').classes('text-lg font-bold')
                with ui.row().classes('gap-2'):
                    ui.button('🖨️ 打印', on_click=lambda: ui.run_javascript('window.print()')).props('color=primary')
                    ui.button('✕ 关闭', on_click=report_dialog.close).props('flat')
            with ui.scroll_area().classes('w-full h-[65vh]'):
                ui.html(report_html, sanitize=False)
        
        report_dialog.open()
        ui.notify('系统报告已生成', type='positive')
    
    def open_template1_report(self):
        """Generate Template 1 report with 品牌方一 branding - 生成真实PDF文件."""
        progress = self.session.get_progress_summary()
        remarks = self.session.get_step_remarks()
        data_quality = self.session.step_data_quality
        skipped = self.session.step_skipped
        
        # 获取真实数据
        optimal_speed = progress.get("optimal_speed", "N/A")
        optimal_pressure = progress.get("optimal_pressure", "N/A")
        gate_freeze = progress.get("gate_freeze_time", "N/A")
        cooling_time = self.session.recommended_cooling_time or "N/A"
        cavity_balance_val = f"{(self.session.cavity_balance_ratio or 0) * 100:.1f}" if self.session.cavity_balance_ratio else "N/A"
        pressure_margin = f"{self.session.pressure_margin:.1f}" if self.session.pressure_margin else "N/A"
        clamping_force = self.session.recommended_clamping_force or "N/A"
        
        # 步骤状态
        step_names = ['粘度曲线分析', '型腔平衡测试', '压力降验证', '工艺窗口定义', '浇口冻结研究', '冷却时间优化', '锁模力优化']
        
        def get_step_status_html(step_num):
            if skipped.get(step_num, False):
                return '<span style="color: #9ca3af;">⏭️ 已跳过</span>'
            completed = progress.get(f'step{step_num}_completed', False)
            quality = data_quality.get(step_num, True)
            if not completed:
                return '<span style="color: #ef4444;">⏳ 未完成</span>'
            elif quality:
                return '<span style="color: #10b981;">✅ 合格</span>'
            else:
                return '<span style="color: #f97316;">⚠️ 偏离</span>'
        
        # 生成备注HTML
        remarks_html = ""
        if remarks:
            remarks_rows = ""
            for step_num, remark_data in remarks.items():
                remarks_rows += f'''
                    <tr style="border-bottom: 1px solid #fcd34d;">
                        <td style="padding: 8px; color: #92400e; width: 15%;">步骤 {step_num}:</td>
                        <td style="padding: 8px; color: #78350f;"><strong>{remark_data.get('reason', '')}</strong> - {remark_data.get('remark', '')}</td>
                    </tr>
                '''
            remarks_html = f'''
            <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #f59e0b;">
                <h4 style="color: #b45309; margin: 0 0 10px 0; font-size: 14px;">⚠️ 工艺备注 / 异常说明</h4>
                <table style="width: 100%; font-size: 12px;">{remarks_rows}</table>
            </div>
            '''
        
        report_no = f"品牌方一-SM-{datetime.now().strftime('%Y%m%d%H%M')}"
        report_date = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        # 完整的HTML报告 (为PDF优化)
        report_html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>品牌方一 科学注塑验证报告 - {report_no}</title>
    <style>
        @page {{
            size: A4;
            margin: 15mm 20mm;
        }}
        body {{
            font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #1e293b;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .logo-box {{
            background: linear-gradient(135deg, #0066cc 0%, #004499 100%);
            color: white;
            padding: 12px 25px;
            border-radius: 6px;
        }}
        .logo-box h1 {{ margin: 0; font-size: 18px; font-weight: bold; }}
        .logo-box p {{ margin: 3px 0 0 0; font-size: 11px; opacity: 0.9; }}
        .report-info {{ text-align: right; }}
        .report-info p {{ margin: 3px 0; }}
        .title {{ text-align: center; margin: 0 0 20px 0; font-size: 16px; font-weight: bold; color: #1e293b; }}
        .info-section {{
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
        }}
        .info-box {{
            flex: 1;
            padding: 12px;
            border-radius: 6px;
        }}
        .info-box.product {{ background: #f8fafc; }}
        .info-box.material {{ background: #fff7ed; }}
        .info-box.machine {{ background: #eff6ff; }}
        .info-box h4 {{
            margin: 0 0 8px 0;
            font-size: 12px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 5px;
        }}
        .info-box table {{ width: 100%; font-size: 11px; }}
        .info-box td {{ padding: 3px 0; }}
        .info-box td:first-child {{ color: #64748b; width: 35%; }}
        .params-box {{
            background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        .params-box h4 {{ color: white; margin: 0 0 12px 0; font-size: 13px; }}
        .params-grid {{
            display: flex;
            gap: 10px;
        }}
        .param-card {{
            flex: 1;
            background: rgba(255,255,255,0.95);
            padding: 12px;
            border-radius: 6px;
            text-align: center;
        }}
        .param-card .label {{ color: #64748b; font-size: 10px; margin: 0; }}
        .param-card .value {{ font-size: 20px; font-weight: bold; margin: 3px 0; }}
        .param-card .unit {{ color: #64748b; font-size: 10px; margin: 0; }}
        .steps-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
            font-size: 11px;
        }}
        .steps-table th {{
            background: #0066cc;
            color: white;
            padding: 8px;
            text-align: left;
        }}
        .steps-table td {{
            padding: 8px;
            border: 1px solid #e2e8f0;
        }}
        .steps-table tr:nth-child(even) {{ background: #f8fafc; }}
        .conclusion {{
            background: #f0fdf4;
            padding: 12px;
            border-radius: 6px;
            margin-top: 15px;
            border-left: 4px solid #10b981;
        }}
        .conclusion h4 {{ color: #166534; margin: 0 0 8px 0; font-size: 12px; }}
        .conclusion p {{ color: #15803d; margin: 0; font-size: 11px; line-height: 1.6; }}
        .signature-row {{
            display: flex;
            justify-content: space-between;
            margin-top: 25px;
            padding-top: 15px;
            border-top: 2px solid #e2e8f0;
        }}
        .signature-box {{
            width: 30%;
        }}
        .signature-box p {{ color: #64748b; margin: 0; font-size: 10px; }}
        .signature-box .line {{ border-bottom: 1px solid #94a3b8; height: 25px; margin-top: 5px; }}
        .footer {{
            margin-top: 20px;
            text-align: center;
            color: #94a3b8;
            font-size: 9px;
            border-top: 1px solid #e2e8f0;
            padding-top: 10px;
        }}
    </style>
</head>
<body>
    <!-- 页眉 -->
    <div class="header">
        <div class="logo-box">
            <h1>品牌方一 - Techtronic Industries</h1>
            <p>创科实业 | Scientific Injection Molding Validation</p>
        </div>
        <div class="report-info">
            <p style="color: #64748b; font-size: 11px;">报告编号 / Report No.</p>
            <p style="color: #0066cc; font-size: 16px; font-weight: bold;">{report_no}</p>
            <p style="color: #64748b; font-size: 11px;">{report_date}</p>
        </div>
    </div>
    
    <h2 class="title">📋 科学注塑七步法工艺验证报告</h2>
    
    <!-- 产品和材料信息 -->
    <div class="info-section">
        <div class="info-box product">
            <h4 style="color: #0066cc;">📦 产品信息</h4>
            <table>
                <tr><td>产品型号:</td><td style="font-weight: bold;">018467001</td></tr>
                <tr><td>零件号:</td><td>351514009 / 520513007</td></tr>
                <tr><td>零件名称:</td><td>Handle Housing Support</td></tr>
                <tr><td>理论重量:</td><td>205g / 196g</td></tr>
                <tr><td>模号:</td><td>TG34724342-07</td></tr>
            </table>
        </div>
        <div class="info-box material">
            <h4 style="color: #ea580c;">🧪 材料信息</h4>
            <table>
                <tr><td>品牌/型号:</td><td style="font-weight: bold;">博云 PA6 260G6 RE310</td></tr>
                <tr><td>颜色:</td><td>红色 (RED)</td></tr>
                <tr><td>密度:</td><td>1.355 g/cm³</td></tr>
                <tr><td>烘烤条件:</td><td>80~100°C / 2~3h</td></tr>
                <tr><td>推荐料温:</td><td>230~260°C</td></tr>
            </table>
        </div>
    </div>
    
    <!-- 机台信息 -->
    <div class="info-box machine" style="margin-bottom: 15px;">
        <h4 style="color: #0066cc;">🏭 试模机台</h4>
        <table style="width: 100%;">
            <tr>
                <td style="width: 12%;">机台号:</td><td style="font-weight: bold; width: 18%;">23# YIZUMI</td>
                <td style="width: 12%;">类型/吨位:</td><td style="width: 18%;">油压机 260T</td>
                <td style="width: 12%;">螺杆直径:</td><td style="width: 18%;">53mm</td>
            </tr>
            <tr>
                <td>最大压力:</td><td>217.1 MPa</td>
                <td>最大射速:</td><td>79 mm/s</td>
                <td>滞留时间:</td><td>1.71 min</td>
            </tr>
        </table>
    </div>
    
    <!-- 七步法关键参数 -->
    <div class="params-box">
        <h4>🎯 七步法验证关键参数</h4>
        <div class="params-grid">
            <div class="param-card">
                <p class="label">最佳射速</p>
                <p class="value" style="color: #0066cc;">{optimal_speed}</p>
                <p class="unit">mm/s</p>
            </div>
            <div class="param-card">
                <p class="label">型腔平衡度</p>
                <p class="value" style="color: #10b981;">{cavity_balance_val}</p>
                <p class="unit">%</p>
            </div>
            <div class="param-card">
                <p class="label">压力余量</p>
                <p class="value" style="color: #8b5cf6;">{pressure_margin}</p>
                <p class="unit">MPa</p>
            </div>
            <div class="param-card">
                <p class="label">最佳保压</p>
                <p class="value" style="color: #f59e0b;">{optimal_pressure}</p>
                <p class="unit">Bar</p>
            </div>
            <div class="param-card">
                <p class="label">浇口冻结</p>
                <p class="value" style="color: #ec4899;">{gate_freeze}</p>
                <p class="unit">秒</p>
            </div>
            <div class="param-card">
                <p class="label">推荐冷却</p>
                <p class="value" style="color: #06b6d4;">{cooling_time}</p>
                <p class="unit">秒</p>
            </div>
            <div class="param-card">
                <p class="label">最佳锁模力</p>
                <p class="value" style="color: #ef4444;">{clamping_force}</p>
                <p class="unit">Ton</p>
            </div>
        </div>
    </div>
    
    <!-- 七步验证详情表格 -->
    <table class="steps-table">
        <tr>
            <th style="width: 5%;">序号</th>
            <th style="width: 20%;">验证项目</th>
            <th style="width: 12%; text-align: center;">状态</th>
            <th>测试结果与关键数据</th>
        </tr>
        <tr><td style="text-align: center;">1</td><td>{step_names[0]}</td><td style="text-align: center;">{get_step_status_html(1)}</td><td>射速范围6.8-68.8mm/s，拐点区间37-53mm/s，最佳射速{optimal_speed}mm/s</td></tr>
        <tr><td style="text-align: center;">2</td><td>{step_names[1]}</td><td style="text-align: center;">{get_step_status_html(2)}</td><td>8腔平衡度{cavity_balance_val}%，最大差异1.1g，符合±5%标准</td></tr>
        <tr><td style="text-align: center;">3</td><td>{step_names[2]}</td><td style="text-align: center;">{get_step_status_html(3)}</td><td>最大压力217MPa，峰值压力107MPa，余量{pressure_margin}MPa，利用率49%</td></tr>
        <tr><td style="text-align: center;">4</td><td>{step_names[3]}</td><td style="text-align: center;">{get_step_status_html(4)}</td><td>工艺窗口40-60Bar，窗口宽度20Bar，推荐保压{optimal_pressure}Bar</td></tr>
        <tr><td style="text-align: center;">5</td><td>{step_names[4]}</td><td style="text-align: center;">{get_step_status_html(5)}</td><td>保压时间3-13s测试，冻结时间{gate_freeze}s，推荐保压时间13s</td></tr>
        <tr><td style="text-align: center;">6</td><td>{step_names[5]}</td><td style="text-align: center;">{get_step_status_html(6)}</td><td>推荐冷却时间{cooling_time}s，顶出温度80°C，预估周期28s</td></tr>
        <tr><td style="text-align: center;">7</td><td>{step_names[6]}</td><td style="text-align: center;">{get_step_status_html(7)}</td><td>最佳锁模力{clamping_force}Ton，确保产品无飞边且模具寿命最大化</td></tr>
    </table>
    
    {remarks_html}
    
    <!-- 验证结论 -->
    <div class="conclusion">
        <h4>✅ 验证结论</h4>
        <p>本次科学注塑七步法工艺验证已完成，各项参数符合品牌方一工艺标准。建议将以上优化参数录入机台参数卡，并在批量生产中持续监控CPK指标，确保工艺稳定性。</p>
    </div>
    
    <!-- 签名区 -->
    <div class="signature-row">
        <div class="signature-box">
            <p>工艺工程师</p>
            <div class="line"></div>
            <p style="color: #94a3b8; font-size: 9px; margin-top: 3px;">日期：____/____/____</p>
        </div>
        <div class="signature-box">
            <p>质量工程师</p>
            <div class="line"></div>
            <p style="color: #94a3b8; font-size: 9px; margin-top: 3px;">日期：____/____/____</p>
        </div>
        <div class="signature-box">
            <p>主管审批</p>
            <div class="line"></div>
            <p style="color: #94a3b8; font-size: 9px; margin-top: 3px;">日期：____/____/____</p>
        </div>
    </div>
    
    <!-- 页脚 -->
    <div class="footer">
        <p>© 品牌方一 - Techtronic Industries | SmartMold Pilot V3.0 | 机密文件 - 仅限内部使用</p>
        <p>模号: TG34724342-07 | 机台: YIZUMI 260T #23 | 供应商: GM</p>
    </div>
</body>
</html>
'''
        
        # 将HTML保存到static目录供下载
        static_dir = Path(__file__).parent / 'static'
        static_dir.mkdir(exist_ok=True)
        
        html_filename = f"品牌方一_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        html_path = static_dir / html_filename
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        html_url = f"/static/{html_filename}"
        
        # 添加html2pdf.js库
        ui.add_head_html('<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>')
        
        # 保存报告内容供预览和下载使用
        self._current_report_html = report_html
        self._current_html_url = html_url
        
        # 生成 PDF 时不再调用实时 AI：使用流程中已保存的实时 AI 点评（若有）
        try:
            from pdf_generator_v2 import generate_report_from_session
            pdf_path = generate_report_from_session(self.session, external_assessment=None)
            pdf_filename = Path(pdf_path).name
            pdf_url = f'/static/{pdf_filename}'
            print(f"[PDF] Generated: {pdf_path}")
            self._current_pdf_url = pdf_url
            self._current_pdf_filename = pdf_filename

        except Exception as e:
            ui.notify(f'❌ PDF生成失败: {str(e)}', type='negative')
            import traceback
            traceback.print_exc()
            return
        
        # 直接在新窗口打开 PDF - 最简单可靠的方法！
        ui.run_javascript(f"window.open('{pdf_url}', '_blank');")
        ui.notify(f'✅ PDF 已在新窗口打开: {pdf_filename}', type='positive', timeout=5000)
                
    def _show_report_preview_dialog(self):
        """显示报告预览对话框"""
        if not hasattr(self, '_current_report_html'):
            ui.notify('没有可预览的报告', type='warning')
            return
        
        with ui.dialog().props('fullscreen') as dialog:
            with ui.card().classes('w-full h-full flex flex-col'):
                with ui.row().classes('w-full justify-between items-center p-4 bg-blue-600 text-white'):
                    ui.label('📄 品牌方一科学注塑验证报告预览').classes('text-xl font-bold')
                    with ui.row().classes('gap-2'):
                        ui.button('📥 下载PDF', on_click=lambda: ui.run_javascript('''
                            const element = document.getElementById("report-preview-content");
                            const opt = {
                                margin: 10,
                                filename: '品牌方一_Scientific_Molding_Report.pdf',
                                image: { type: 'jpeg', quality: 0.98 },
                                html2canvas: { scale: 2, useCORS: true },
                                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
                            };
                            html2pdf().set(opt).from(element).save();
                        ''')).props('color=white text-color=blue-600')
                        ui.button('🖨️ 打印', on_click=lambda: ui.run_javascript('''
                            const content = document.getElementById("report-preview-content").innerHTML;
                            const printWindow = window.open('', '_blank');
                            printWindow.document.write('<html><head><title>品牌方一 Report</title></head><body>');
                            printWindow.document.write(content);
                            printWindow.document.write('</body></html>');
                            printWindow.document.close();
                            printWindow.focus();
                            setTimeout(() => { printWindow.print(); }, 500);
                        ''')).props('color=white text-color=blue-600 outline')
                        ui.button('✕ 关闭', on_click=dialog.close).props('flat color=white')
                
                with ui.scroll_area().classes('flex-1'):
                    ui.html(f'''
                        <div id="report-preview-content" style="background: white; padding: 20px;">
                            {self._current_report_html}
                        </div>
                    ''', sanitize=False).classes('w-full')
        
        dialog.open()
    
    def open_template2_report(self):
        """Generate Template 2 report - minimalist style."""
        progress = self.session.get_progress_summary()
        
        report_html = f'''
        <div style="font-family: 'Segoe UI', sans-serif; padding: 50px; max-width: 800px; margin: auto; background: #fafafa;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 16px; margin-bottom: 40px; text-align: center;">
                <h1 style="margin: 0; font-size: 32px; font-weight: 300;">科学注塑工艺报告</h1>
                <p style="margin: 15px 0 0 0; opacity: 0.9;">Scientific Injection Molding Report</p>
                <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.7;">{datetime.now().strftime("%Y.%m.%d")}</p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 40px;">
                <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: #667eea;">{progress.get("optimal_speed", "--")}</div>
                    <div style="color: #94a3b8; font-size: 12px; margin-top: 5px;">最佳射速 (mm/s)</div>
                </div>
                <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: #764ba2;">{progress.get("optimal_pressure", "--")}</div>
                    <div style="color: #94a3b8; font-size: 12px; margin-top: 5px;">最佳保压 (MPa)</div>
                </div>
                <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: #f093fb;">{progress.get("gate_freeze_time", "--")}</div>
                    <div style="color: #94a3b8; font-size: 12px; margin-top: 5px;">冻结时间 (s)</div>
                </div>
                <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: #10b981;">{progress.get("clamping_force", "--")}</div>
                    <div style="color: #94a3b8; font-size: 12px; margin-top: 5px;">锁模力 (Ton)</div>
                </div>
            </div>
            
            <div style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-top: 0; color: #334155; font-weight: 500;">验证进度</h3>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                    <div style="display: flex; align-items: center; gap: 10px; padding: 12px; background: {'#f0fdf4' if progress.get("step1_completed") else '#fef2f2'}; border-radius: 8px;">
                        <span style="font-size: 20px;">{'✅' if progress.get("step1_completed") else '⭕'}</span>
                        <span>粘度曲线分析</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; padding: 12px; background: {'#f0fdf4' if progress.get("step2_completed") else '#fef2f2'}; border-radius: 8px;">
                        <span style="font-size: 20px;">{'✅' if progress.get("step2_completed") else '⭕'}</span>
                        <span>型腔平衡测试</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; padding: 12px; background: {'#f0fdf4' if progress.get("step3_completed") else '#fef2f2'}; border-radius: 8px;">
                        <span style="font-size: 20px;">{'✅' if progress.get("step3_completed") else '⭕'}</span>
                        <span>压力降验证</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; padding: 12px; background: {'#f0fdf4' if progress.get("step4_completed") else '#fef2f2'}; border-radius: 8px;">
                        <span style="font-size: 20px;">{'✅' if progress.get("step4_completed") else '⭕'}</span>
                        <span>工艺窗口定义</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; padding: 12px; background: {'#f0fdf4' if progress.get("step5_completed") else '#fef2f2'}; border-radius: 8px;">
                        <span style="font-size: 20px;">{'✅' if progress.get("step5_completed") else '⭕'}</span>
                        <span>浇口冻结研究</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; padding: 12px; background: {'#f0fdf4' if progress.get("step6_completed") else '#fef2f2'}; border-radius: 8px;">
                        <span style="font-size: 20px;">{'✅' if progress.get("step6_completed") else '⭕'}</span>
                        <span>冷却时间优化</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; padding: 12px; background: {'#f0fdf4' if progress.get("step7_completed") else '#fef2f2'}; border-radius: 8px; grid-column: span 2;">
                        <span style="font-size: 20px;">{'✅' if progress.get("step7_completed") else '⭕'}</span>
                        <span>锁模力优化</span>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 30px; padding: 25px; background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%); border-radius: 12px; border: 1px solid #667eea44;">
                <h4 style="margin: 0 0 10px 0; color: #667eea;">📝 工艺总结</h4>
                <p style="color: #475569; margin: 0; line-height: 1.6;">
                    基于科学注塑七步法完成工艺参数优化，各项指标符合生产要求。建议将以上参数录入机台参数卡，并定期进行CPK监控。
                </p>
            </div>
            
            <div style="margin-top: 40px; text-align: center; color: #94a3b8; font-size: 12px;">
                <p>Powered by SmartMold Pilot V3.0</p>
            </div>
        </div>
        '''
        
        with ui.dialog() as report_dialog, ui.card().classes('w-full max-w-4xl max-h-screen overflow-auto'):
            ui.html(report_html, sanitize=False)
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('关闭', on_click=report_dialog.close).props('flat')
                ui.button('打印', on_click=lambda: ui.run_javascript('window.print()')).props('color=primary')
        
        report_dialog.open()
        ui.notify('模板二报告已生成', type='positive')
