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
    
    async def show_unreasonable_data_dialog(self, step: int, data_issue: str, on_continue: callable):
        """Show dialog for unreasonable data confirmation with remark input."""
        dialog_result = {'continue': False, 'remark': '', 'reason': ''}
        
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label(f"⚠️ 数据不合理警告").classes('text-xl font-bold text-orange-600')
            ui.label(f"步骤 {step} 检测到以下问题：").classes('text-gray-600 mt-2')
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
                dialog.close()
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
        """Show dialog when user tries to skip a step without completing it."""
        step_names = ['粘度曲线', '型腔平衡', '压力降', '工艺窗口', '浇口冻结', '冷却时间', '锁模力优化']
        step_name = step_names[step - 1]
        
        # 科学注塑跳过理由选项
        skip_reasons = [
            "该测试已在其他试模中完成",
            "使用历史数据/经验值",
            "客户提供参数，无需验证",
            "模具/材料限制，无法进行该测试",
            "时间紧迫，后续补做",
            "其他原因"
        ]
        
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label(f"⚠️ 步骤 {step} 未完成").classes('text-xl font-bold text-orange-600')
            ui.label(f"您即将跳过: {step_name}").classes('text-gray-600 mt-2')
            ui.label("该步骤在科学注塑流程中非常重要，跳过可能影响最终工艺的可靠性。").classes('text-sm text-red-500 mt-2 p-2 bg-red-50 rounded')
            
            ui.label("如需跳过，请选择原因：").classes('text-sm text-gray-500 mt-4')
            
            reason_select = ui.select(skip_reasons, label="选择跳过原因").classes('w-full')
            remark_input = ui.textarea(label="补充说明", placeholder="请说明跳过该步骤的具体原因...").classes('w-full')
            
            error_label = ui.label("").classes('text-red-500 text-sm')
            
            async def on_skip():
                if not reason_select.value:
                    error_label.set_text("请选择跳过原因")
                    return
                # "其他原因"必须填写备注
                if reason_select.value == "其他原因" and (not remark_input.value or len(remark_input.value.strip()) < 3):
                    error_label.set_text("选择'其他原因'时必须填写补充说明")
                    return
                
                # Mark step as skipped with reason
                self.session.set_step_remark(step, reason_select.value, remark_input.value or "（无补充说明）", "用户跳过该步骤")
                self.session.set_step_skipped(step, True)  # Mark as skipped
                
                # Update progress indicator to show skipped state
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
        """Create machine parameter snapshot input section. Returns the input references."""
        inputs = {}
        with ui.expansion("📝 机台参数快照", icon='settings').classes('w-full'):
            ui.label("记录当前机台参数（将随实验结果保存）").classes(f"{GLASS_THEME['text_secondary']} text-sm mb-4")
            
            with ui.grid(columns=3).classes('w-full gap-4'):
                inputs['barrel1'] = glass_input("料筒温度1 (°C)", "")
                inputs['barrel2'] = glass_input("料筒温度2 (°C)", "")
                inputs['barrel3'] = glass_input("料筒温度3 (°C)", "")
                inputs['barrel4'] = glass_input("料筒温度4 (°C)", "")
                inputs['barrel5'] = glass_input("料筒温度5 (°C)", "")
                inputs['nozzle'] = glass_input("喷嘴温度 (°C)", "")
                inputs['hot_runner'] = glass_input("热流道温度 (°C)", "")
                inputs['mold_fixed'] = glass_input("定模温度 (°C)", "")
                inputs['mold_moving'] = glass_input("动模温度 (°C)", "")
                inputs['max_inj_pressure'] = glass_input("最大注射压力 (MPa)", "")
                inputs['max_hold_pressure'] = glass_input("最大保压压力 (MPa)", "")
                inputs['vp_position'] = glass_input("V/P切换位置 (mm)", "")
                inputs['cycle_time'] = glass_input("成型周期 (s)", "")
            
            # AI comment area for machine params
            inputs['ai_comment'] = ui.column().classes("w-full mt-2")
        
        return inputs
    
    def fill_machine_snapshot(self, inputs: Dict, is_reasonable: bool):
        """Fill machine snapshot with simulated values and AI commentary."""
        if is_reasonable:
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
            
            inputs['ai_comment'].clear()
            with inputs['ai_comment']:
                glass_alert(
                    "🤖 机台参数点评（合理）：\n"
                    "✓ 料筒5段温度梯度合理（205→225°C），塑化均匀\n"
                    "✓ 模具温度55°C，冷却效率与表面质量平衡\n"
                    "✓ 周期稳定，保持在22.5s",
                    "success"
                )
        else:
            # 不合理的机台参数
            inputs['barrel1'].set_value("260")
            inputs['barrel2'].set_value("255")
            inputs['barrel3'].set_value("250")
            inputs['barrel4'].set_value("245")
            inputs['barrel5'].set_value("240")
            inputs['nozzle'].set_value("235")
            inputs['hot_runner'].set_value("230")
            inputs['mold_fixed'].set_value("30")
            inputs['mold_moving'].set_value("45")
            inputs['max_inj_pressure'].set_value("180")
            inputs['max_hold_pressure'].set_value("120")
            inputs['vp_position'].set_value("8")
            inputs['cycle_time'].set_value("35.0")
            
            inputs['ai_comment'].clear()
            with inputs['ai_comment']:
                glass_alert(
                    "🤖 机台参数点评（不合理）：\n"
                    "✗ 料筒温度倒梯度（260→240°C），易造成熔体不均\n"
                    "✗ 定模30°C动模45°C温差15°C，产品易翘曲变形\n"
                    "✗ 周期35s过长，生产效率低下",
                    "error"
                )
    
    def capture_snapshot(self) -> MachineSnapshot:
        """Capture current snapshot from UI inputs."""
        return MachineSnapshot(
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
            cycle_time=float(self.snapshot_inputs['cycle_time'].value or 0)
        )
    
    def save_machine_snapshot(self, inputs: Dict):
        """Save machine snapshot from user inputs to session."""
        try:
            self.session.machine_snapshot = MachineSnapshot(
                barrel_temp_zone1=float(inputs['barrel1'].value or 0),
                barrel_temp_zone2=float(inputs['barrel2'].value or 0),
                barrel_temp_zone3=float(inputs['barrel3'].value or 0),
                barrel_temp_zone4=float(inputs['barrel4'].value or 0),
                barrel_temp_zone5=float(inputs['barrel5'].value or 0),
                nozzle_temp=float(inputs['nozzle'].value or 0),
                hot_runner_temp=float(inputs['hot_runner'].value or 0),
                mold_temp_fixed=float(inputs['mold_fixed'].value or 0),
                mold_temp_moving=float(inputs['mold_moving'].value or 0),
                max_injection_pressure=float(inputs['max_inj_pressure'].value or 0),
                max_holding_pressure=float(inputs['max_hold_pressure'].value or 0),
                vp_transfer_position=float(inputs['vp_position'].value or 0),
                cycle_time=float(inputs['cycle_time'].value or 0)
            )
        except (ValueError, TypeError):
            pass  # 忽略无效输入
    
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
                    
                    with ai_comment:
                        if is_reasonable:
                            glass_alert(
                                f"🤖 AI点评（您的真实数据）：\n\n"
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
                                f"🤖 AI点评（您的真实数据）：\n\n"
                                f"⚠ 数据质量提醒:\n" + "\n".join([f"  • {i}" for i in issues]),
                                "warning"
                            )
                    
                    # 运行分析算法
                    inflection = find_viscosity_inflection_point(speeds, viscosities)
                    optimal_speed = inflection['optimal_speed']
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
                    
                    self.update_progress_indicator()
                    
                    if not is_reasonable:
                        await self.show_unreasonable_data_dialog(
                            step=1,
                            data_issue=f"测试点{len(speeds)}个，射速范围{speed_range:.1f}mm/s",
                            on_continue=lambda: ui.notify("✓ 步骤1完成（已记录备注）", type='warning')
                        )
                    else:
                        ui.notify("✓ 步骤1完成 - 使用您的真实数据", type='positive')
                
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
                        
                        with ai_comment:
                            glass_alert(
                                "🤖 AI点评（PA6 260G6模拟案例）：\n\n"
                                "✓ 射速6.8-68.8mm/s，覆盖完整剪切区\n"
                                "✓ 螺杆直径53mm，YIZUMI 260T油压机\n"
                                "✓ 粘度曲线在37-53mm/s区间有明显拐点\n"
                                "✓ 最佳射速推荐：45-53mm/s",
                                "success"
                            )
                    else:
                        speeds = [50, 55, 60]
                        viscosities = [75, 74, 73]
                        speeds_input.set_value("50,55,60")
                        viscosities_input.set_value("75,74,73")
                        screw_dia.set_value("80")
                        
                        with ai_comment:
                            glass_alert(
                                "🤖 AI点评（不合理模拟数据）：\n\n"
                                "✗ 射速范围太窄（仅50-60mm/s）\n"
                                "✗ 仅3个测试点不足以精确定位拐点\n"
                                "⚠ 建议：扩大射速范围",
                                "error"
                            )
                    
                    inflection = find_viscosity_inflection_point(speeds, viscosities)
                    optimal_speed = inflection['optimal_speed']
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
                    
                    self.update_progress_indicator()
                    
                    if not is_reasonable:
                        await self.show_unreasonable_data_dialog(
                            step=1,
                            data_issue="射速范围太窄，仅3个测试点",
                            on_continue=lambda: ui.notify("✓ 步骤1完成（已记录备注）", type='warning')
                        )
                    else:
                        ui.notify(f"✓ 步骤1完成", type='positive')
                
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
                glass_button("📋 加载示例数据", lambda: run_test_with_data(True))
                ui.button("⚠ 不合理示例", on_click=lambda: run_test_with_data(False)).classes(
                    "bg-orange-500 hover:bg-orange-600 text-white rounded-lg px-4 py-2 text-sm"
                )

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
                    with ai_comment:
                        glass_alert(
                            "🤖 AI点评（PA6真实案例 - 8腔模具）：\n\n"
                            "✓ 8个型腔短射重量范围：24.67g ~ 25.77g\n"
                            "✓ 最大差异1.1g，不平衡度约4.27%\n"
                            "⚠ 略超3%推荐标准，但属于可接受范围\n"
                            "📊 模号：TG34724342-07，1+1型腔\n"
                            "💡 建议：如需提升平衡度，可微调热流道温度",
                            "success"
                        )
                else:
                    weights = [10.50, 9.20, 10.80, 9.00, 10.30, 8.90, 10.60, 9.10]
                    for i, w in enumerate(weights, 1):
                        cavity_inputs[i].set_value(f"{w:.2f}")
                    
                    with ai_comment:
                        glass_alert(
                            "🤖 AI点评（不合理数据）：\n\n"
                            "✗ 型腔重量差异达1.9g，平衡度仅82%\n"
                            "✗ 远腔重量偏高，近腔偏低，流道设计不均\n"
                            "⚠ 建议：检查热流道温度，调整浇口尺寸",
                            "error"
                        )
                
                pressures = [w * 10 for w in weights]
                balance_ratio = cavity_balance(pressures)
                
                # Mock full shot weights (slightly higher and more balanced)
                full_shot_weights = {i: w * 2 * (1 + random.uniform(-0.01, 0.01)) for i, w in enumerate(weights, 1)}
                visual_data = {i: visual_inputs[i].value for i in range(1, 9)}
                
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
                
                # Update progress indicator
                self.update_progress_indicator()
                ui.notify(f"✓ 步骤2完成", type='positive' if is_reasonable else 'warning')
            
            # Track reasonable state for this step
            step2_is_reasonable = True
            
            async def run_unreasonable_test():
                nonlocal step2_is_reasonable
                step2_is_reasonable = False
                await run_test_with_data(False)
                # Show confirmation dialog for unreasonable data
                await self.show_unreasonable_data_dialog(
                    step=2,
                    data_issue="型腔重量差异超过5%，平衡度不合格",
                    on_continue=lambda: ui.notify("已记录备注，继续下一步", type='info')
                )
            
            with ui.row().classes('gap-4 mt-4'):
                glass_button("✓ 合理模拟数值", lambda: run_test_with_data(True))
                ui.button("✗ 不合理模拟数值", on_click=run_unreasonable_test).classes(
                    "bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg px-6 py-3"
                )
    
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
                    
                    with ai_comment:
                        glass_alert(
                            "🤖 AI点评（PA6真实案例 - YIZUMI 260T）：\n\n"
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
                else:
                    max_p, peak_p = 180, 172
                    max_pressure_input.set_value("180")
                    peak_pressure_input.set_value("172")
                    
                    with ai_comment:
                        glass_alert(
                            "🤖 AI点评（不合理数据）：\n\n"
                            "✗ 压力利用率96%，几乎无余量！\n"
                            "✗ 材料波动可能导致欠注或报警\n"
                            "⚠ 建议：降低射速或更换大机器",
                            "error"
                        )
                
                result = calculate_pressure_margin(max_p, peak_p)
                
                # Prepare detailed pressure drop data for report
                detailed_pressures = {
                    'positions': ["Nozzle", "Runner", "Gate", "Part_50%", "Part_99%"],
                    'pressures': [24.3, 28.2, 55.0, 77.3, 106.7] if is_reasonable else [30, 60, 100, 140, 172]
                }
                self.session.set_step3_result(result['margin'], result['is_limited'], detailed_data=detailed_pressures)
                
                # Set data quality
                self.session.set_step_quality(3, is_reasonable)
                
                status_icon = "✓" if not result['is_limited'] else "⚠"
                result_label.set_text(f"{status_icon} {result['status']}\n压力余量: {result['margin']:.1f} MPa\n压力利用率: {result['utilization_percent']:.1f}%")
                result_label.classes(remove="text-red-600 text-emerald-600 text-yellow-600")
                result_label.classes(add="text-emerald-600" if not result['is_limited'] else "text-red-600")
                
                # Update progress indicator
                self.update_progress_indicator()
                ui.notify(f"✓ 步骤3完成", type='positive' if is_reasonable else 'warning')
            
            # Track reasonable state for this step
            step3_is_reasonable = True
            
            async def run_unreasonable_test():
                nonlocal step3_is_reasonable
                step3_is_reasonable = False
                await run_test_with_data(False)
                # Show confirmation dialog for unreasonable data
                await self.show_unreasonable_data_dialog(
                    step=3,
                    data_issue="压力利用率96%，几乎无安全余量，材料波动可能导致欠注",
                    on_continue=lambda: ui.notify("已记录备注，继续下一步", type='info')
                )
            
            with ui.row().classes('gap-4 mt-4'):
                glass_button("✓ 合理模拟数值", lambda: run_test_with_data(True))
                ui.button("✗ 不合理模拟数值", on_click=run_unreasonable_test).classes(
                    "bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg px-6 py-3"
                )
    
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
                    
                    with ai_comment:
                        glass_alert(
                            "🤖 AI点评（PA6真实案例 - 工艺窗口）：\n\n"
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
                    
                    with ai_comment:
                        glass_alert(
                            "🤖 AI点评（不合理数据）：\n\n"
                            "✗ 工艺窗口仅4MPa，属于极窄窗口！\n"
                            "✗ 参数波动易导致短射或飞边\n"
                            "⚠ 建议：优化壁厚设计，调整浇口位置",
                            "error"
                        )
                
                window = find_process_window_center(test_points)
                
                if window['status'] == 'found':
                    optimal_pressure = window['center_pressure']
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
                    
                    # Update progress indicator
                    self.update_progress_indicator()
                    ui.notify(f"✓ 步骤4完成", type='positive' if is_reasonable else 'warning')
            
            # Track reasonable state for this step
            step4_is_reasonable = True
            
            async def run_unreasonable_test():
                nonlocal step4_is_reasonable
                step4_is_reasonable = False
                await run_test_with_data(False)
                # Show confirmation dialog for unreasonable data
                await self.show_unreasonable_data_dialog(
                    step=4,
                    data_issue="工艺窗口仅4MPa，属于极窄窗口，参数波动易导致短射或飞边",
                    on_continue=lambda: ui.notify("已记录备注，继续下一步", type='info')
                )
            
            with ui.row().classes('gap-4 mt-4'):
                glass_button("✓ 合理模拟数值", lambda: run_test_with_data(True))
                ui.button("✗ 不合理模拟数值", on_click=run_unreasonable_test).classes(
                    "bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg px-6 py-3"
                )
    
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
                    
                    with ai_comment:
                        glass_alert(
                            "🤖 AI点评（PA6真实案例 - 浇口冻结）：\n\n"
                            "✓ 测试保压时间：3-13秒（共11个测试点）\n"
                            "✓ 浇口冻结时间：12秒（重量稳定在335.7g）\n"
                            "✓ 推荐保压时间：13秒（冻结时间+1秒余量）\n"
                            "📊 重量变化曲线：\n"
                            "   • 3s: 327.2g → 12s: 335.7g（增重8.5g）\n"
                            "   • 12-13s重量不变，确认浇口已完全冻结\n"
                            "💡 典型S型曲线，冻结点明确",
                            "success"
                        )
                else:
                    times = [1, 2, 3, 4, 5, 6]
                    weights = [9.0, 9.3, 9.6, 9.8, 9.95, 10.1]
                    times_input.set_value("1,2,3,4,5,6")
                    weights_input.set_value("9.0,9.3,9.6,9.8,9.95,10.1")
                    
                    with ai_comment:
                        glass_alert(
                            "🤖 AI点评（不合理数据）：\n\n"
                            "✗ 6秒时重量仍在上升，浇口尚未冻结\n"
                            "✗ 可能原因：浇口过大、模温过高\n"
                            "⚠ 建议：延长测试至8-10秒",
                            "error"
                        )
                
                freeze_result = detect_gate_freeze_time(times, weights)
                freeze_time = freeze_result.get('freeze_time') or times[-1]
                recommended_time = freeze_result.get('recommended_time') or (freeze_time + 2)
                
                # Format data for report
                seal_curve = [{'hold_time': t, 'weight': w} for t, w in zip(times, weights)]
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
                
                # Update progress indicator
                self.update_progress_indicator()
                ui.notify(f"✓ 步骤5完成", type='positive' if is_reasonable else 'warning')
            
            # Track reasonable state for this step
            step5_is_reasonable = True
            
            async def run_unreasonable_test():
                nonlocal step5_is_reasonable
                step5_is_reasonable = False
                await run_test_with_data(False)
                # Show confirmation dialog for unreasonable data
                await self.show_unreasonable_data_dialog(
                    step=5,
                    data_issue="6秒时重量仍在上升，浇口尚未完全冻结，需延长测试时间",
                    on_continue=lambda: ui.notify("已记录备注，继续下一步", type='info')
                )
            
            with ui.row().classes('gap-4 mt-4'):
                glass_button("✓ 合理模拟数值", lambda: run_test_with_data(True))
                ui.button("✗ 不合理模拟数值", on_click=run_unreasonable_test).classes(
                    "bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg px-6 py-3"
                )
    
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
                    
                    with ai_comment:
                        glass_alert(
                            f"🤖 AI点评（PA6真实案例 - 冷却优化）：\n\n"
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
                else:
                    ejection_temp = 110
                    cooling_time = 6
                    ejection_temp_input.set_value("110")
                    test_cooling_input.set_value("6")
                    
                    recommended = max(cooling_time, min_holding + 2)
                    cycle_time = recommended + min_holding + 3
                    
                    with ai_comment:
                        glass_alert(
                            f"🤖 AI点评（不合理数据）：\n\n"
                            f"✗ 冷却仅{cooling_time}s，产品可能未固化\n"
                            f"✗ 顶出温度{ejection_temp}°C过高！\n"
                            "⚠ 建议：增加冷却至12-15s",
                            "error"
                        )
                
                # Format data for report - Mocking a curve since Step 6 UI only has 1 point
                mock_cooling_curve = [
                    {'cooling_time': recommended - 5, 'part_temp': ejection_temp + 10, 'deformation': 0.15},
                    {'cooling_time': recommended, 'part_temp': ejection_temp, 'deformation': 0.08},
                    {'cooling_time': recommended + 5, 'part_temp': ejection_temp - 5, 'deformation': 0.05}
                ]
                self.session.set_step6_result(recommended, mock_cooling_curve)
                
                # Set data quality
                self.session.set_step_quality(6, is_reasonable)
                
                status = "✓ 冷却优化" if is_reasonable else "⚠ 参数需调整"
                result_label.set_text(f"{status}\n推荐冷却时间: {recommended:.1f}s\n预估周期: {cycle_time:.1f}s")
                result_label.classes(remove="text-red-600 text-emerald-600 text-yellow-600")
                result_label.classes(add="text-emerald-600" if is_reasonable else "text-yellow-600")
                
                # Update progress indicator
                self.update_progress_indicator()
                ui.notify("✓ 步骤6完成，请继续步骤7（锁模力优化）" if is_reasonable else "⚠ 步骤6完成，但建议调整参数", type='positive' if is_reasonable else 'warning')
            
            # Track reasonable state for this step
            step6_is_reasonable = True
            
            async def run_unreasonable_test():
                nonlocal step6_is_reasonable
                step6_is_reasonable = False
                await run_test_with_data(False)
                # Show confirmation dialog for unreasonable data
                await self.show_unreasonable_data_dialog(
                    step=6,
                    data_issue="冷却时间过短，产品可能未完全固化，顶出温度过高",
                    on_continue=lambda: ui.notify("已记录备注，请继续步骤7", type='info')
                )
            
            with ui.row().classes('gap-4 mt-4'):
                glass_button("✓ 合理模拟数值", lambda: run_test_with_data(True))
                ui.button("✗ 不合理模拟数值", on_click=run_unreasonable_test).classes(
                    "bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg px-6 py-3"
                )
    
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
                    
                    with ai_comment:
                        glass_alert(
                            f"🤖 AI点评（PA6真实案例 - 锁模力优化）：\n\n"
                            f"✓ 测试锁模力范围：100-160 Ton（共6个测试点）\n"
                            f"✓ 最小无飞边锁模力：{min_ok_force} Ton\n"
                            f"✓ 推荐锁模力：{recommended_force} Ton（含15%安全余量）\n"
                            f"📊 测试结果分析：\n"
                            f"   • 160-120 Ton: 产品OK，重量稳定305g\n"
                            f"   • 110-100 Ton: 产品飞边，重量增加至306-308g\n"
                            f"💡 模号: TG34724342-07，机台吨位: 280T",
                            "success"
                        )
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
                    
                    with ai_comment:
                        glass_alert(
                            f"🤖 AI点评（不合理数据）：\n\n"
                            f"✗ 所有测试点均出现飞边！锁模力严重不足\n"
                            f"✗ 产品重量持续增加（312→330g），熔体外溢\n"
                            f"⚠ 建议：增加锁模力至120-160 Ton范围重新测试\n"
                            f"⚠ 检查：分型面密封、模具磨损情况",
                            "error"
                        )
                
                # Format data for report
                clamping_curve = [
                    {'clamping_force': f, 'part_weight': w, 'flash_detected': a} 
                    for f, w, a in zip(forces, weights, appearances)
                ]
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
                
                # Update progress indicator
                self.update_progress_indicator()
                ui.notify("🎉 七步法全部完成！" if is_reasonable else "⚠ 步骤7完成，但建议调整参数", type='positive' if is_reasonable else 'warning')
            
            # Track reasonable state for this step
            step7_is_reasonable = True
            
            async def run_unreasonable_test():
                nonlocal step7_is_reasonable
                step7_is_reasonable = False
                await run_test_with_data(False)
                # Show confirmation dialog for unreasonable data
                await self.show_unreasonable_data_dialog(
                    step=7,
                    data_issue="所有测试点均出现飞边，锁模力严重不足",
                    on_continue=lambda: ui.notify("已记录备注，流程完成", type='info')
                )
            
            with ui.row().classes('gap-4 mt-4'):
                glass_button("✓ 合理模拟数值", lambda: run_test_with_data(True))
                ui.button("✗ 不合理模拟数值", on_click=run_unreasonable_test).classes(
                    "bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg px-6 py-3"
                )
    
    def update_progress_indicator(self):
        """Update the progress indicator to reflect current state."""
        if hasattr(self, 'progress_container'):
            self.progress_container.clear()
            progress = self.session.get_progress_summary()
            step_names = ['粘度曲线', '型腔平衡', '压力降', '工艺窗口', '浇口冻结', '冷却时间', '锁模力']
            data_quality = self.session.step_data_quality  # True=reasonable, False=unreasonable
            
            with self.progress_container:
                with ui.row().classes('w-full items-center justify-center flex-wrap'):
                    for i in range(1, 8):
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
                            ui.label(step_names[i-1]).classes(f"text-xs mt-2 {text_color}")
                        
                        # Connecting line (except after last step)
                        if i < 7:
                            # Use the determined line_color
                            ui.html(f'<div class="h-1 w-6 {line_color} mx-1 rounded"></div>', sanitize=False).classes('flex items-center')
    
    def render(self):
        """Render the entire 7-step wizard."""
        with glass_container():
            ui.label("科学注塑七步法向导").classes(f"{GLASS_THEME['text_primary']} text-3xl font-bold mb-4")
            
            # Progress summary with labels and connecting lines - FIXED TO TOP
            progress = self.session.get_progress_summary()
            step_names = ['粘度曲线', '型腔平衡', '压力降', '工艺窗口', '浇口冻结', '冷却时间', '锁模力']
            
            # Progress indicator container - sticky to top
            self.progress_container = ui.column().classes('w-full mb-6 sticky top-0 z-50 bg-white/90 backdrop-blur-sm py-4 rounded-lg shadow-sm')
            self.update_progress_indicator()
            
            # Stepper inside a scrollable area
            with ui.stepper().props('vertical').classes('w-full') as stepper:
                self.stepper = stepper
                
                # Helper function to check if step is completed before navigation
                async def check_and_navigate(current_step: int, go_next: bool = True):
                    progress = self.session.get_progress_summary()
                    step_key = f'step{current_step}_completed'
                    
                    if not progress.get(step_key, False):
                        # Step not completed, show skip dialog
                        await self.show_skip_step_dialog(current_step, stepper, go_next)
                    else:
                        # Step completed, proceed normally
                        if go_next:
                            stepper.next()
                        else:
                            stepper.previous()
                
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
                ui.button('模板一报告 (TTI品牌)', on_click=lambda: close_and_generate('template1')).classes(
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
        """Generate Template 1 report with TTI branding - 生成真实PDF文件."""
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
        
        report_no = f"TTI-SM-{datetime.now().strftime('%Y%m%d%H%M')}"
        report_date = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        # 完整的HTML报告 (为PDF优化)
        report_html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>TTI 科学注塑验证报告 - {report_no}</title>
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
            <h1>TTI - Techtronic Industries</h1>
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
        <p>本次科学注塑七步法工艺验证已完成，各项参数符合TTI工艺标准。建议将以上优化参数录入机台参数卡，并在批量生产中持续监控CPK指标，确保工艺稳定性。</p>
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
        <p>© TTI - Techtronic Industries | SmartMold Pilot V3.0 | 机密文件 - 仅限内部使用</p>
        <p>模号: TG34724342-07 | 机台: YIZUMI 260T #23 | 供应商: GM</p>
    </div>
</body>
</html>
'''
        
        # 将HTML保存到static目录供下载
        static_dir = Path(__file__).parent / 'static'
        static_dir.mkdir(exist_ok=True)
        
        html_filename = f"TTI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        html_path = static_dir / html_filename
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        html_url = f"/static/{html_filename}"
        
        # 添加html2pdf.js库
        ui.add_head_html('<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>')
        
        # 保存报告内容供预览和下载使用
        self._current_report_html = report_html
        self._current_html_url = html_url
        
        # 先生成 PDF 文件
        try:
            from pdf_generator_v2 import generate_report_from_session
            pdf_path = generate_report_from_session(self.session)
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
                    ui.label('📄 TTI科学注塑验证报告预览').classes('text-xl font-bold')
                    with ui.row().classes('gap-2'):
                        ui.button('📥 下载PDF', on_click=lambda: ui.run_javascript('''
                            const element = document.getElementById("report-preview-content");
                            const opt = {
                                margin: 10,
                                filename: 'TTI_Scientific_Molding_Report.pdf',
                                image: { type: 'jpeg', quality: 0.98 },
                                html2canvas: { scale: 2, useCORS: true },
                                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
                            };
                            html2pdf().set(opt).from(element).save();
                        ''')).props('color=white text-color=blue-600')
                        ui.button('🖨️ 打印', on_click=lambda: ui.run_javascript('''
                            const content = document.getElementById("report-preview-content").innerHTML;
                            const printWindow = window.open('', '_blank');
                            printWindow.document.write('<html><head><title>TTI Report</title></head><body>');
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
