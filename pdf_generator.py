"""
PDF Report Generator - MIL Scientific Injection Molding Validation
按照 TTI Excel 模板格式生成专业的科学注塑验证报告

作者: SmartMold Pilot V3
版本: 2.0 (7步法完整版)
"""

from fpdf import FPDF
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import os


class MILReportPDF(FPDF):
    """MIL 科学注塑验证报告 PDF 生成器"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        # 加载中文字体 (STHeiti Medium 支持中英文)
        self.add_font('CN', '', '/System/Library/Fonts/STHeiti Medium.ttc')
        self.page_title = ""
        
    def header(self):
        """页眉 - TTI Logo"""
        # TTI Logo 蓝色背景
        self.set_fill_color(0, 51, 102)
        self.rect(10, 8, 30, 12, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('CN', '', 10)
        self.set_xy(12, 11)
        self.cell(26, 6, 'TTi', align='C')
        
        # 报告标题
        if self.page_title:
            self.set_text_color(0, 51, 102)
            self.set_font('CN', '', 12)
            self.set_xy(45, 10)
            self.cell(0, 8, self.page_title, align='L')
        
        # 报告编号和日期
        self.set_text_color(100, 100, 100)
        self.set_font('CN', '', 8)
        self.set_xy(150, 10)
        self.cell(0, 4, f"Report No: TTI-SM-{datetime.now().strftime('%Y%m%d')}", align='R')
        self.set_xy(150, 15)
        self.cell(0, 4, datetime.now().strftime("%Y-%m-%d"), align='R')
        
        self.ln(18)
        
    def footer(self):
        """页脚"""
        self.set_y(-12)
        self.set_font('CN', '', 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, f'SmartMold Pilot V3.0 | MIL Scientific Injection Molding | Page {self.page_no()}', align='C')

    # ==================== 辅助方法 ====================
    
    def section_title(self, title_cn: str, title_en: str = "", color=(0, 51, 102)):
        """章节标题"""
        self.set_font('CN', '', 11)
        self.set_text_color(*color)
        text = f"{title_cn} {title_en}" if title_en else title_cn
        self.cell(0, 7, text, new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(*color)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        
    def info_table(self, data: List[tuple], cols: int = 2, label_width: float = 35):
        """信息表格 - [(label, value), ...]"""
        col_width = 190 / cols
        self.set_font('CN', '', 8)
        
        for i, (label, value) in enumerate(data):
            if i > 0 and i % cols == 0:
                self.ln()
            self.set_text_color(80, 80, 80)
            self.cell(label_width, 5, str(label), align='L')
            self.set_text_color(0, 0, 0)
            self.cell(col_width - label_width, 5, str(value), align='L')
        self.ln(6)
        
    def data_table(self, headers: List[str], rows: List[List], col_widths: List[float] = None,
                   header_color=(0, 51, 102), alt_row=True):
        """数据表格"""
        if not col_widths:
            col_widths = [190 / len(headers)] * len(headers)
            
        # 表头
        self.set_fill_color(*header_color)
        self.set_text_color(255, 255, 255)
        self.set_font('CN', '', 8)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, str(h), border=1, align='C', fill=True)
        self.ln()
        
        # 数据行
        self.set_text_color(0, 0, 0)
        self.set_font('CN', '', 8)
        for idx, row in enumerate(rows):
            fill = alt_row and idx % 2 == 1
            if fill:
                self.set_fill_color(245, 245, 245)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 5, str(cell), border=1, align='C', fill=fill)
            self.ln()
            
    def result_box(self, label: str, value: str, unit: str = "", width: float = 60):
        """结果框"""
        self.set_fill_color(230, 242, 255)
        self.set_draw_color(0, 102, 204)
        h = 12
        self.rect(self.get_x(), self.get_y(), width, h, 'DF')
        
        self.set_font('CN', '', 7)
        self.set_text_color(60, 60, 60)
        x = self.get_x()
        y = self.get_y()
        self.set_xy(x + 2, y + 1)
        # 将换行符替换为空格，避免字体警告
        label_clean = label.replace('\n', ' ')
        self.cell(width - 4, 4, label_clean, align='L')
        
        self.set_font('CN', '', 10)
        self.set_text_color(0, 51, 102)
        self.set_xy(x + 2, y + 6)
        self.cell(width - 4, 5, f"{value} {unit}".strip(), align='C')
        
        self.set_xy(x + width + 3, y)
        
    def warning_box(self, step: int, reason: str, issue: str, remark: str):
        """警告/备注框 - 用于偏离或跳过说明"""
        self.ln(3)
        self.set_fill_color(255, 248, 220)
        self.set_draw_color(255, 165, 0)
        self.set_line_width(0.5)
        
        y_start = self.get_y()
        self.rect(10, y_start, 190, 16, 'DF')
        
        self.set_xy(12, y_start + 1)
        self.set_font('CN', '', 9)
        self.set_text_color(180, 95, 6)
        status = "Skipped" if "跳过" in reason or "Skip" in reason else "Deviated"
        self.cell(0, 5, f"Step {step} - {status}: {reason}")
        
        self.set_xy(12, y_start + 6)
        self.set_font('CN', '', 8)
        self.set_text_color(100, 80, 50)
        self.cell(0, 4, f"Issue: {issue}")
        
        self.set_xy(12, y_start + 10)
        self.cell(0, 4, f"Remark: {remark}")
        
        self.ln(18)
        
    def purpose_section(self, purpose_cn: str, purpose_en: str):
        """目的说明区域"""
        self.set_font('CN', '', 9)
        self.set_text_color(60, 60, 60)
        self.set_fill_color(250, 250, 250)
        self.multi_cell(190, 5, f"目的 (PURPOSE)\n{purpose_cn}\n{purpose_en}", fill=True)
        self.ln(2)


def generate_mil_report(session_data: Dict[str, Any], output_path: str = None) -> str:
    """
    生成完整的 MIL 科学注塑验证报告 PDF
    
    Args:
        session_data: 包含所有试验数据的字典
        output_path: 输出文件路径
    
    Returns:
        生成的PDF文件路径
    """
    
    if output_path is None:
        static_dir = Path(__file__).parent / 'static'
        static_dir.mkdir(exist_ok=True)
        output_path = static_dir / f"TTI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    pdf = MILReportPDF()
    remarks = session_data.get('step_remarks', {})
    
    # ==================== 第1页: 总结页 ====================
    pdf.add_page()
    pdf.page_title = "MIL Scientific Injection Molding Validation"
    
    # 产品信息
    pdf.section_title("产品信息", "Part Information")
    pdf.info_table([
        ("Model No", session_data.get('model_no', 'N/A')),
        ("Supplier/供应商", session_data.get('supplier', 'N/A')),
        ("Part No", session_data.get('part_no', 'N/A')),
        ("Part Name/产品名称", session_data.get('part_name', 'N/A')),
        ("Part Weight/产品重量(g)", session_data.get('part_weight', 'N/A')),
        ("Shot Weight/模次重量(g)", session_data.get('shot_weight', 'N/A')),
    ], cols=2, label_width=45)
    
    # 模具信息
    pdf.section_title("模具信息", "Tooling Information")
    pdf.info_table([
        ("Mold No/模具编号", session_data.get('mold_no', 'N/A')),
        ("Runner Type/流道类型", session_data.get('runner_type', 'N/A')),
        ("CAV/型腔数", session_data.get('cavities', 'N/A')),
        ("Cycle Time/周期(s)", session_data.get('cycle_time', 'N/A')),
    ], cols=2, label_width=45)
    
    # 材料信息
    pdf.section_title("材料信息", "Material Information")
    pdf.info_table([
        ("Brand/品牌", session_data.get('material_brand', 'N/A')),
        ("Type/型号", session_data.get('material_type', 'N/A')),
        ("Color/颜色", session_data.get('color', 'N/A')),
        ("Density/密度(g/cm3)", session_data.get('density', 'N/A')),
        ("Drying Temp/烘料温度(C)", session_data.get('drying_temp', 'N/A')),
        ("Drying Time/烘料时间(H)", session_data.get('drying_time', 'N/A')),
    ], cols=2, label_width=50)
    
    # 机台信息
    pdf.section_title("试模机台", "Injection Machine")
    machine = session_data.get('machine', {})
    pdf.info_table([
        ("Machine No/机号", machine.get('no', 'N/A')),
        ("Brand/品牌", machine.get('brand', 'N/A')),
        ("Type/类型", machine.get('type', 'N/A')),
        ("Tonnage/吨位(T)", machine.get('tonnage', 'N/A')),
        ("Screw Dia/螺杆直径(mm)", machine.get('screw_diameter', 'N/A')),
        ("Max Pressure/最大压力(MPa)", machine.get('max_pressure', 'N/A')),
    ], cols=2, label_width=50)
    
    # 测试结果总结
    pdf.ln(3)
    pdf.section_title("测试结果总结", "Test Results Summary", (0, 128, 0))
    
    results = session_data.get('results', {})
    pdf.result_box("推荐注塑速度\nRecommended Speed", str(results.get('speed', 'N/A')), "mm/s", 62)
    pdf.result_box("推荐保压\nRecommended Pressure", str(results.get('pressure', 'N/A')), "Bar", 62)
    pdf.result_box("推荐保压时间\nHolding Time", str(results.get('hold_time', 'N/A')), "s", 62)
    pdf.ln(15)
    pdf.result_box("型腔平衡\nCAV Balance", results.get('balance', 'N/A'), "", 62)
    pdf.result_box("推荐冷却时间\nCooling Time", str(results.get('cooling_time', 'N/A')), "s", 62)
    pdf.result_box("推荐锁模力\nClamping Force", str(results.get('clamping_force', 'N/A')), "Ton", 62)
    
    # 七步验证状态表
    pdf.ln(18)
    pdf.section_title("七步验证结果", "7-Step Validation Results")
    
    steps = session_data.get('steps', [])
    step_names = [
        ('粘度曲线', 'Viscosity Curve'),
        ('型腔平衡', 'CAV Balance'),
        ('压力降测试', 'Pressure Drop'),
        ('工艺窗口', 'Process Window'),
        ('浇口冻结', 'Gate Freeze'),
        ('冷却时间', 'Cooling Time'),
        ('锁模力优化', 'Clamping Force'),
    ]
    
    step_rows = []
    for i, (cn, en) in enumerate(step_names):
        step = steps[i] if i < len(steps) else {}
        status = step.get('status', 'Pending')
        result = step.get('result', '-')
        step_rows.append([str(i+1), f"{cn} {en}", status, result])
    
    pdf.data_table(
        ['No.', 'Step Name / 步骤名称', 'Status / 状态', 'Result / 结果'],
        step_rows,
        [12, 80, 30, 68]
    )
    
    # ==================== 第2页: 温度设置 ====================
    pdf.add_page()
    pdf.page_title = "温度设置 Temperature Set"
    
    temp = session_data.get('temperature', {})
    barrel = temp.get('barrel', {})
    
    # 炮台温度
    pdf.section_title("炮台温度", "Barrel Temp (°C)")
    pdf.data_table(
        ['射咀 Nozzle', '第一段 Zone1', '第二段 Zone2', '第三段 Zone3', '第四段 Zone4', '第五段 Zone5'],
        [[barrel.get('nozzle', 'N/A'), barrel.get('zone1', 'N/A'), barrel.get('zone2', 'N/A'),
          barrel.get('zone3', 'N/A'), barrel.get('zone4', 'N/A'), barrel.get('zone5', 'N/A')]],
        [32, 32, 32, 32, 32, 30]
    )
    
    # 前模温度
    pdf.ln(3)
    pdf.section_title("前模温度", "CAV Temp (°C)")
    cav_temp = temp.get('cavity', {})
    pdf.info_table([
        ("设置温度 Set Temp", f"{cav_temp.get('set', 'N/A')} °C"),
        ("实际温度 Actual", f"{cav_temp.get('actual', 'N/A')} °C"),
    ], cols=2)
    
    # 后模温度
    pdf.section_title("后模温度", "COR Temp (°C)")
    core_temp = temp.get('core', {})
    pdf.info_table([
        ("设置温度 Set Temp", f"{core_temp.get('set', 'N/A')} °C"),
        ("实际温度 Actual", f"{core_temp.get('actual', 'N/A')} °C"),
    ], cols=2)
    
    # ==================== 第3页: 粘度曲线 ====================
    pdf.add_page()
    pdf.page_title = "粘度曲线 Viscosity Curve"
    
    pdf.purpose_section(
        "找到最佳射胶速度",
        "Find the optimal injection speed"
    )
    
    # 粘度数据表
    pdf.section_title("有效粘度", "Effective Viscosity")
    viscosity = session_data.get('step1', {})
    v_data = viscosity.get('data', [])
    
    if v_data:
        pdf.data_table(
            ['填充速度\nFill speed %', 'mm/s', '切换位置\nSwitch Pos', '填充时间\nFill Time', 
             '注塑峰值压力\nPeak Press (Bar)', '剪切率\nShear Rate', '有效粘度\nViscosity (MPa*s)'],
            v_data,
            [25, 22, 28, 28, 35, 26, 26]
        )
    else:
        pdf.set_font('CN', '', 9)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "No test data available / 无测试数据", align='C')
        pdf.ln()
    
    # 推荐结果
    pdf.ln(5)
    pdf.section_title("推荐注塑速度", "Recommended Injection Speed", (0, 128, 0))
    pdf.result_box("百分比 Percent", viscosity.get('speed_range', 'N/A'), "%", 80)
    pdf.result_box("速度 Speed", str(viscosity.get('speed_mms', 'N/A')), "mm/s", 80)
    
    # 偏离/跳过备注
    if 1 in remarks:
        r = remarks[1]
        pdf.warning_box(1, r.get('reason', ''), r.get('data_issue', ''), r.get('remark', ''))
    
    # ==================== 第4页: 型腔平衡 ====================
    pdf.add_page()
    pdf.page_title = "型腔平衡测试 CAV Balance Test"
    
    pdf.purpose_section(
        "确认多型腔模具的平衡性",
        "Confirm the balance of the multi-cavity mold"
    )
    
    cavity = session_data.get('step2', {})
    
    # 短射测试数据
    pdf.section_title("短射产品体积20%~70%", "Short Shot Volume 20%~70%")
    c_data = cavity.get('short_shot_data', [])
    if c_data:
        headers = ['型腔# Cav#'] + [f'Shot{i+1}' for i in range(len(c_data[0])-2)] + ['平均重量 Ave(g)']
        pdf.data_table(headers, c_data, None)
    
    # 结果
    pdf.ln(3)
    pdf.section_title("结果", "Result", (0, 128, 0))
    pdf.result_box("最大值 Max", str(cavity.get('max_weight', 'N/A')), "g", 60)
    pdf.result_box("最小值 Min", str(cavity.get('min_weight', 'N/A')), "g", 60)
    pdf.result_box("不平衡程度 Imbalance", str(cavity.get('imbalance', 'N/A')), "%", 60)
    pdf.ln(15)
    
    balance_ok = cavity.get('judgment', 'N/A')
    if balance_ok == 'OK':
        pdf.set_fill_color(200, 255, 200)
    else:
        pdf.set_fill_color(255, 200, 200)
    pdf.set_draw_color(0, 128, 0) if balance_ok == 'OK' else pdf.set_draw_color(200, 0, 0)
    pdf.rect(10, pdf.get_y(), 50, 10, 'DF')
    pdf.set_font('CN', '', 12)
    pdf.set_text_color(0, 100, 0) if balance_ok == 'OK' else pdf.set_text_color(180, 0, 0)
    pdf.cell(50, 10, f"Result: {balance_ok}", align='C')
    
    if 2 in remarks:
        pdf.ln(12)
        r = remarks[2]
        pdf.warning_box(2, r.get('reason', ''), r.get('data_issue', ''), r.get('remark', ''))
    
    # ==================== 第5页: 压力降测试 ====================
    pdf.add_page()
    pdf.page_title = "动态压力降测试 Dynamic Pressure Test"
    
    pdf.purpose_section(
        "确定在填充过程中注射压力的损失情况",
        "Determine the loss of injection pressure during the filling process"
    )
    
    pressure = session_data.get('step3', {})
    
    pdf.section_title("压力分布", "Pressure Distribution (Bar)")
    p_data = pressure.get('data', [])
    if p_data:
        pdf.data_table(
            ['序号 No.', '流动截面 Flow Section', '峰值压力 Peak Pressure (Bar)'],
            p_data,
            [30, 100, 60]
        )
    
    # 结果
    pdf.ln(5)
    pdf.section_title("结果", "Result", (0, 128, 0))
    pdf.result_box("填充V/P位置压力\nV/P Pressure", str(pressure.get('vp_pressure', 'N/A')), "Bar", 90)
    pdf.result_box("峰值压力占机台%\nPeak Pressure %", str(pressure.get('peak_pct', 'N/A')), "%", 90)
    
    pdf.ln(18)
    pdf.set_font('CN', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, "备注: 动态压力降测试属于选做项\n填充到产品体积99%，推荐填充压力不超过机台最大压力的85%\nNote: Dynamic pressure test is optional. Fill up to 99% of product volume. Peak pressure should not exceed 85% of machine max.")
    
    if 3 in remarks:
        r = remarks[3]
        pdf.warning_box(3, r.get('reason', ''), r.get('data_issue', ''), r.get('remark', ''))
    
    # ==================== 第6页: 工艺窗口 ====================
    pdf.add_page()
    pdf.page_title = "压力工艺窗口 Pressure Process Window"
    
    pdf.purpose_section(
        "找到最佳保压压力",
        "Find the optimal pressure-holding pressure"
    )
    
    window = session_data.get('step4', {})
    
    pdf.section_title("测试数据", "Test Data")
    w_data = window.get('data', [])
    if w_data:
        pdf.data_table(
            ['保压压力(Bar)\nHolding Pressure', '保压时间(s)\nHolding Time', '产品重量(g)\nPart Weight', 
             '产品外观\nAppearance', '照片\nPicture'],
            w_data,
            [38, 38, 38, 46, 30]
        )
    
    # 结果
    pdf.ln(5)
    pdf.section_title("推荐参数", "Recommended Parameters", (0, 128, 0))
    pdf.result_box("最小压力(Bar)\nMin Pressure", str(window.get('min_pressure', 'N/A')), "", 60)
    pdf.result_box("最大压力(Bar)\nMax Pressure", str(window.get('max_pressure', 'N/A')), "", 60)
    pdf.result_box("推荐压力(Bar)\nRecommended", str(window.get('recommended', 'N/A')), "", 60)
    
    if 4 in remarks:
        pdf.ln(18)
        r = remarks[4]
        pdf.warning_box(4, r.get('reason', ''), r.get('data_issue', ''), r.get('remark', ''))
    
    # ==================== 第7页: 浇口冻结 ====================
    pdf.add_page()
    pdf.page_title = "浇口冻结测试 Gate Freezing Test"
    
    pdf.purpose_section(
        "确认浇口冻结时间，确认保压时间",
        "Confirm the freezing time of the gate and the holding pressure time"
    )
    
    gate = session_data.get('step5', {})
    
    pdf.section_title("测试数据", "Test Data")
    g_data = gate.get('data', [])
    if g_data:
        pdf.data_table(
            ['模次 Shot', '保压时间 Holding Time(s)', '零件重量 Part Weight(g)'],
            g_data,
            [40, 75, 75]
        )
    
    # 结果
    pdf.ln(5)
    pdf.section_title("结果", "Result", (0, 128, 0))
    pdf.result_box("浇口冻结时间\nGate Freeze Time", str(gate.get('freeze_time', 'N/A')), "s", 90)
    pdf.result_box("推荐保压时间\nRecommended Hold Time", str(gate.get('hold_time', 'N/A')), "s", 90)
    
    if 5 in remarks:
        pdf.ln(18)
        r = remarks[5]
        pdf.warning_box(5, r.get('reason', ''), r.get('data_issue', ''), r.get('remark', ''))
    
    # ==================== 第8页: 冷却时间 ====================
    pdf.add_page()
    pdf.page_title = "冷却时间优化 Cooling Time Optimization"
    
    pdf.purpose_section(
        "确定最佳冷却时间",
        "Determine the optimal cooling time"
    )
    
    cooling = session_data.get('step6', {})
    
    pdf.section_title("测试数据", "Test Data")
    cool_data = cooling.get('data', [])
    if cool_data:
        pdf.data_table(
            ['模次 Shot', '冷却时间 Cooling Time(s)', '产品重量 Part Weight(g)', '变形情况 Deformation'],
            cool_data,
            [35, 50, 50, 55]
        )
    
    # 结果
    pdf.ln(5)
    pdf.section_title("结果", "Result", (0, 128, 0))
    pdf.result_box("推荐冷却时间\nRecommended Cooling", str(cooling.get('cooling_time', 'N/A')), "s", 90)
    pdf.result_box("预计周期时间\nEstimated Cycle", str(cooling.get('cycle_time', 'N/A')), "s", 90)
    
    if 6 in remarks:
        pdf.ln(18)
        r = remarks[6]
        pdf.warning_box(6, r.get('reason', ''), r.get('data_issue', ''), r.get('remark', ''))
    
    # ==================== 第9页: 锁模力优化 ====================
    pdf.add_page()
    pdf.page_title = "锁模力优化 Optimization of Clamping Force"
    
    pdf.purpose_section(
        "找到最佳锁模力",
        "Find the optimal clamping force"
    )
    
    clamping = session_data.get('step7', {})
    
    pdf.section_title("测试数据", "Test Data")
    clamp_data = clamping.get('data', [])
    if clamp_data:
        pdf.data_table(
            ['模次 Shot', '锁模力 Clamping Force(Ton)', '产品重量 Part Weight(g)', 
             '产品外观(是否有披风)\nAppearance', '照片 Picture'],
            clamp_data,
            [25, 45, 40, 55, 25]
        )
    
    # 结果
    pdf.ln(5)
    pdf.section_title("结果", "Result", (0, 128, 0))
    pdf.result_box("合模最大液压压力\nMax Hydraulic Press", str(clamping.get('max_hydraulic', 'N/A')), "", 90)
    pdf.result_box("推荐锁模力(Ton)\nRecommended Force", str(clamping.get('recommended', 'N/A')), "Ton", 90)
    
    if 7 in remarks:
        pdf.ln(18)
        r = remarks[7]
        pdf.warning_box(7, r.get('reason', ''), r.get('data_issue', ''), r.get('remark', ''))
    
    # ==================== 第10页: 机台参数卡 ====================
    pdf.add_page()
    pdf.page_title = "MIL INJECTION MOLD TRIAL SHOT RECORD 试模参数记录表"
    
    # M/C Set Up
    pdf.section_title("M/C Set Up 机台设置")
    mc = session_data.get('machine_setup', session_data.get('machine', {}))
    pdf.info_table([
        ("Machine Brand/啤机品牌", mc.get('brand', 'N/A')),
        ("Machine Type/机器类型", mc.get('type', 'N/A')),
        ("Machine Size/啤机吨位", f"{mc.get('tonnage', 'N/A')} T"),
        ("Screw Diameter/螺杆直径", f"{mc.get('screw_diameter', 'N/A')} mm"),
        ("Max Inj Pressure/最大注射压力", f"{mc.get('max_pressure', 'N/A')} MPa"),
        ("Intensification Ratio/增强比", mc.get('ratio', 'N/A')),
    ], cols=2, label_width=55)
    
    # Molding Condition
    pdf.section_title("Molding Condition 成型条件")
    cond = session_data.get('molding_condition', {})
    pdf.info_table([
        ("Injection Speed/射胶速度", f"{cond.get('inj_speed', 'N/A')} mm/s"),
        ("V/P Position/VP切换位置", f"{cond.get('vp_pos', 'N/A')} mm"),
        ("Hold Pressure/保压压力", f"{cond.get('hold_pressure', 'N/A')} Bar"),
        ("Hold Time/保压时间", f"{cond.get('hold_time', 'N/A')} s"),
        ("Cooling Time/冷却时间", f"{cond.get('cooling_time', 'N/A')} s"),
        ("Cycle Time/周期时间", f"{cond.get('cycle_time', 'N/A')} s"),
    ], cols=2, label_width=50)
    
    # 签名区
    pdf.ln(10)
    pdf.set_font('CN', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(60, 6, 'Process Engineer 工艺工程师:', align='L')
    pdf.cell(60, 6, 'Quality Engineer 质量工程师:', align='L')
    pdf.cell(0, 6, 'Approved by 批准:', align='L', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)
    pdf.cell(60, 8, '_________________________', align='L')
    pdf.cell(60, 8, '_________________________', align='L')
    pdf.cell(0, 8, '_________________________', align='L')
    
    # 保存
    pdf.output(str(output_path))
    return str(output_path)


def generate_report_from_session(session) -> str:
    """
    从 SevenStepSessionState 对象生成完整报告
    
    Args:
        session: SevenStepSessionState 实例
    
    Returns:
        生成的PDF文件路径
    """
    progress = session.get_progress_summary()
    remarks = session.get_step_remarks()
    skipped = session.step_skipped
    quality = session.step_data_quality
    
    # 获取机台快照
    snapshot = session.machine_snapshot
    
    # 构建温度数据
    temp_data = {'barrel': {}, 'cavity': {}, 'core': {}}
    if snapshot:
        temp_data['barrel'] = {
            'nozzle': snapshot.nozzle_temp or 'N/A',
            'zone1': snapshot.barrel_temp_zone1 or 'N/A',
            'zone2': snapshot.barrel_temp_zone2 or 'N/A',
            'zone3': snapshot.barrel_temp_zone3 or 'N/A',
            'zone4': 'N/A',
            'zone5': 'N/A',
        }
        temp_data['cavity'] = {
            'set': snapshot.mold_temp_fixed or 'N/A',
            'actual': 'N/A',
        }
        temp_data['core'] = {
            'set': snapshot.mold_temp_moving or 'N/A',
            'actual': 'N/A',
        }
    
    # 构建步骤状态
    steps = []
    step_results = [
        f"Speed: {progress.get('optimal_speed', 'N/A')} mm/s",
        f"Balance: {(session.cavity_balance_ratio or 0)*100:.1f}%",
        f"Margin: {session.pressure_margin:.1f} MPa" if session.pressure_margin else "N/A",
        f"Pressure: {progress.get('optimal_pressure', 'N/A')} Bar",
        f"Freeze: {progress.get('gate_freeze_time', 'N/A')} s",
        f"Cooling: {session.recommended_cooling_time or 'N/A'} s",
        f"Force: {session.recommended_clamping_force or 'N/A'} Ton",
    ]
    
    for i in range(1, 8):
        if skipped.get(i, False):
            status = 'Skipped'
        elif progress.get(f'step{i}_completed', False):
            status = 'OK' if quality.get(i, True) else 'Deviated'
        else:
            status = 'Pending'
        steps.append({'status': status, 'result': step_results[i-1]})
    
    # 构建完整数据
    session_data = {
        # 产品信息 (示例数据，实际应从数据库获取)
        'model_no': '018467001',
        'supplier': 'GM',
        'part_no': '351514009 / 520513007',
        'part_name': 'Handle Housing Support',
        'part_weight': '205',
        'shot_weight': '424',
        
        # 模具信息
        'mold_no': 'TG34724342-07',
        'runner_type': 'Sub gate',
        'cavities': '1+1',
        'cycle_time': '55',
        
        # 材料信息
        'material_brand': 'KING FA',
        'material_type': 'PA6+30GF% KA501',
        'color': 'RED',
        'density': '1.366',
        'drying_temp': '80~100',
        'drying_time': '2~3',
        
        # 机台信息
        'machine': {
            'no': '23#',
            'brand': snapshot.machine_brand if snapshot else 'YIZUMI',
            'type': 'Hydraulic',
            'tonnage': snapshot.max_clamping_force if snapshot else '280',
            'screw_diameter': snapshot.screw_diameter if snapshot else '60',
            'max_pressure': snapshot.max_injection_pressure if snapshot else '217',
        },
        
        # 温度设置
        'temperature': temp_data,
        
        # 测试结果
        'results': {
            'speed': progress.get('optimal_speed', 'N/A'),
            'pressure': progress.get('optimal_pressure', 'N/A'),
            'hold_time': progress.get('gate_freeze_time', 'N/A'),
            'balance': 'OK' if (session.cavity_balance_ratio or 0) >= 0.97 else 'NG',
            'cooling_time': session.recommended_cooling_time or 'N/A',
            'clamping_force': session.recommended_clamping_force or 'N/A',
        },
        
        # 步骤状态
        'steps': steps,
        'step_remarks': {int(k): v for k, v in remarks.items()},
        
        # 各步骤数据
        'step1': {
            'data': [],  # 粘度曲线数据点
            'speed_range': '70%~90%',
            'speed_mms': progress.get('optimal_speed', 'N/A'),
        },
        'step2': {
            'short_shot_data': [],
            'max_weight': 'N/A',
            'min_weight': 'N/A',
            'imbalance': f"{(1-(session.cavity_balance_ratio or 1))*100:.2f}" if session.cavity_balance_ratio else 'N/A',
            'judgment': 'OK' if (session.cavity_balance_ratio or 0) >= 0.97 else 'NG',
        },
        'step3': {
            'data': [
                ['1', '喷咀 Nozzle', 'N/A'],
                ['2', '流道 Runner', 'N/A'],
                ['3', '浇口 Gate', 'N/A'],
                ['4', '50%产品 fill 50% part', 'N/A'],
                ['5', '产品V/P V/P part', 'N/A'],
            ],
            'vp_pressure': 'N/A',
            'peak_pct': f"{100 - (session.pressure_margin or 0) / 2.17:.0f}" if session.pressure_margin else 'N/A',
        },
        'step4': {
            'data': [],
            'min_pressure': session.process_window_bounds.get('low', 'N/A') if session.process_window_bounds else 'N/A',
            'max_pressure': session.process_window_bounds.get('high', 'N/A') if session.process_window_bounds else 'N/A',
            'recommended': progress.get('optimal_pressure', 'N/A'),
        },
        'step5': {
            'data': [],
            'freeze_time': progress.get('gate_freeze_time', 'N/A'),
            'hold_time': f"{(progress.get('gate_freeze_time') or 0) + 1}" if progress.get('gate_freeze_time') else 'N/A',
        },
        'step6': {
            'data': [],
            'cooling_time': session.recommended_cooling_time or 'N/A',
            'cycle_time': '55',
        },
        'step7': {
            'data': [],
            'max_hydraulic': 'N/A',
            'recommended': session.recommended_clamping_force or 'N/A',
        },
        
        # 成型条件
        'molding_condition': {
            'inj_speed': progress.get('optimal_speed', 'N/A'),
            'vp_pos': 'N/A',
            'hold_pressure': progress.get('optimal_pressure', 'N/A'),
            'hold_time': progress.get('gate_freeze_time', 'N/A'),
            'cooling_time': session.recommended_cooling_time or 'N/A',
            'cycle_time': '55',
        },
    }
    
    return generate_mil_report(session_data)


# 保持向后兼容
def generate_tti_report(session_data: dict, output_path: str = None) -> str:
    return generate_mil_report(session_data, output_path)


def generate_detailed_report(session_data: dict, output_path: str = None) -> str:
    return generate_mil_report(session_data, output_path)


if __name__ == '__main__':
    # 测试数据
    test_data = {
        'model_no': '018467001',
        'supplier': 'GM',
        'part_no': '370922001 / 370923001',
        'part_name': 'Handle Housing Support',
        'part_weight': '251 / 222',
        'shot_weight': '493',
        'mold_no': 'TG3A0004695-01',
        'runner_type': 'Sub gate',
        'cavities': '1+1',
        'cycle_time': '55',
        'material_brand': 'KING FA',
        'material_type': 'PA6+30GF%',
        'color': 'RED',
        'density': '1.366',
        'drying_temp': '80~100',
        'drying_time': '2~3',
        'machine': {
            'no': '23#',
            'brand': 'YIZUMI',
            'type': 'Hydraulic',
            'tonnage': '280',
            'screw_diameter': '60',
            'max_pressure': '217',
        },
        'temperature': {
            'barrel': {'nozzle': 255, 'zone1': 265, 'zone2': 265, 'zone3': 261, 'zone4': 255, 'zone5': 245},
            'cavity': {'set': 60, 'actual': 58},
            'core': {'set': 14, 'actual': 15},
        },
        'results': {
            'speed': '53~69',
            'pressure': '50',
            'hold_time': '13',
            'balance': 'OK',
            'cooling_time': '25',
            'clamping_force': '220',
        },
        'steps': [
            {'status': 'OK', 'result': 'Speed: 53~69 mm/s'},
            {'status': 'OK', 'result': 'Balance: 96.94%'},
            {'status': 'OK', 'result': 'Margin: 61.0%'},
            {'status': 'OK', 'result': 'Pressure: 50 Bar'},
            {'status': 'OK', 'result': 'Freeze: 12s'},
            {'status': 'Skipped', 'result': 'N/A'},
            {'status': 'OK', 'result': 'Force: 220 Ton'},
        ],
        'step_remarks': {
            6: {'reason': '跳过 Skipped', 'data_issue': '使用默认冷却时间', 'remark': 'Default cooling time used'}
        },
        'step1': {
            'data': [
                ['90%', '68.8', '30', '2', '115', '0.500', '230'],
                ['80%', '60.9', '30', '2.3', '110', '0.435', '253'],
                ['70%', '52.9', '30', '2.6', '105.8', '0.385', '275.08'],
                ['60%', '45.3', '30', '3', '101.7', '0.333', '305.1'],
                ['50%', '37.3', '30', '3.6', '97.4', '0.278', '350.64'],
                ['30%', '22.2', '30', '5.9', '87.7', '0.169', '517.43'],
                ['10%', '6.8', '30', '19.6', '94.1', '0.051', '1844.36'],
            ],
            'speed_range': '70%~90%',
            'speed_mms': '53~69',
        },
        'step2': {
            'short_shot_data': [
                ['1', '25', '25', '24.5', '24.83'],
                ['2', '25.3', '25.2', '25.1', '25.2'],
                ['3', '25.8', '26', '25.5', '25.77'],
                ['4', '24.9', '24.5', '24.8', '24.73'],
                ['5', '25.3', '25.2', '25.5', '25.33'],
                ['6', '24.6', '24.8', '25', '24.8'],
                ['7', '24.9', '24.5', '24.6', '24.67'],
                ['8', '25.5', '25.2', '25.4', '25.37'],
            ],
            'max_weight': '25.77',
            'min_weight': '24.67',
            'imbalance': '4.27',
            'judgment': 'OK',
        },
        'step3': {
            'data': [
                ['1', '喷咀 Nozzle', '24.3'],
                ['2', '流道 Runner', '28.2'],
                ['3', '浇口 Gate', '55'],
                ['4', '50%产品 fill 50% part', '77.3'],
                ['5', '产品V/P V/P part', '106.7'],
            ],
            'vp_pressure': '106.7',
            'peak_pct': '61.0',
        },
        'step4': {
            'data': [
                ['30', '15', '329.2', '产品缩水 shrink', ''],
                ['40', '15', '331.5', 'OK', ''],
                ['50', '15', '335.6', 'OK', ''],
                ['60', '15', '336.4', 'OK', ''],
                ['70', '15', '339.1', '产品披风 flash', ''],
                ['80', '15', '340.4', '产品披风 flash', ''],
            ],
            'min_pressure': '40',
            'max_pressure': '60',
            'recommended': '50',
        },
        'step5': {
            'data': [
                ['1', '3', '327.2'],
                ['2', '4', '328.54'],
                ['3', '5', '330.92'],
                ['4', '6', '332.96'],
                ['5', '7', '333.5'],
                ['6', '8', '334.02'],
                ['7', '9', '334.65'],
                ['8', '10', '335.2'],
                ['9', '11', '335.5'],
                ['10', '12', '335.7'],
                ['11', '13', '335.7'],
            ],
            'freeze_time': '12',
            'hold_time': '13',
        },
        'step6': {
            'data': [],
            'cooling_time': '25',
            'cycle_time': '55',
        },
        'step7': {
            'data': [
                ['1', '240', '335.5', '外观OK', ''],
                ['2', '220', '335.5', '外观OK', ''],
                ['3', '215', '338.2', '产品披风', ''],
                ['4', '183', '341.9', '产品披风', ''],
            ],
            'max_hydraulic': '140',
            'recommended': '220',
        },
        'molding_condition': {
            'inj_speed': '53~69',
            'vp_pos': '30',
            'hold_pressure': '50',
            'hold_time': '13',
            'cooling_time': '25',
            'cycle_time': '55',
        },
    }
    
    path = generate_mil_report(test_data, 'test_mil_report.pdf')
    print(f"PDF generated: {path}")
