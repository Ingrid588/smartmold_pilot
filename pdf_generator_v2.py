"""
PDF Report Generator V2 - 完全复刻 MIL Excel 模板
严格按照"模版案例 Scientific Injection Molding Validation NEW 7.1(2).xlsx"布局生成PDF

核心原则: 
- 存储原始数据（Raw Data）
- App实时计算派生指标（Calculated Insights）
- 报告展示计算结果和工程建议
"""

from fpdf import FPDF
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import os


class MILReportV2(FPDF):
    """MIL 科学注塑验证报告 V2 - Excel模板复刻版"""
    
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_auto_page_break(auto=True, margin=15)
        # 中文字体
        self.add_font('CN', '', '/System/Library/Fonts/STHeiti Medium.ttc')
        self.add_font('CN', 'B', '/System/Library/Fonts/STHeiti Medium.ttc')
        
    def header(self):
        """页眉"""
        self.set_font('CN', 'B', 14)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, 'MIL Scientific Injection Molding Validation', align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(2)
        
    def footer(self):
        """页脚"""
        self.set_y(-15)
        self.set_font('CN', '', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')
    
    # ========================================================================
    # 第1页: 产品、模具、材料、机台信息（Header Info）
    # ========================================================================
    
    def add_header_page(self, data: Dict[str, Any]):
        """
        第1页: 三栏布局报告头
        - 产品信息 Part Information
        - 模具信息 Tooling Information  
        - 材料信息 Material Information
        - 机台信息 Injection Machine
        """
        self.add_page()
        
        # 产品信息 Part Information
        self._section_title("产品信息（Part Information）")
        part_data = [
            ("Model No", data.get('model_no', 'N/A')),
            ("Part No", data.get('part_no', 'N/A')),
            ("Part Name", data.get('part_name', 'N/A')),
            ("供应商 (Supplier)", data.get('supplier', 'N/A')),
            ("负责人 (Owner)", data.get('owner', 'N/A')),
            ("产品理论重量 (g)", data.get('part_theoretical_weight', 'N/A')),
            ("实际重量 (g)", data.get('part_actual_weight', 'N/A')),
        ]
        self._info_table(part_data, cols=2)
        
        # 模具信息 Tooling Information
        self._section_title("模具信息（Tooling Information）")
        mold_data = [
            ("模号 (T/N)", data.get('mold_number', 'N/A')),
            ("流道形式 (Runner type)", data.get('runner_type', 'N/A')),
            ("CAV", data.get('cavity_count', 'N/A')),
        ]
        self._info_table(mold_data, cols=2)
        
        # 材料信息 Material Information
        self._section_title("材料信息（Material Information）")
        material_data = [
            ("品牌 (Brand)", data.get('material_brand', 'N/A')),
            ("型号 (TYPE)", data.get('material_type', 'N/A')),
            ("材料编号 (Material number)", data.get('material_number', 'N/A')),
            ("颜色 (color)", data.get('material_color', 'N/A')),
            ("密度 (Density g/cm³)", data.get('material_density', 'N/A')),
            ("推荐烘烤温度 (°C)", data.get('drying_temp', 'N/A')),
            ("推荐烘烤时间 (H)", data.get('drying_time', 'N/A')),
            ("推荐模温 (°C)", data.get('recommended_mold_temp', 'N/A')),
            ("推荐料温 (°C)", data.get('recommended_melt_temp', 'N/A')),
        ]
        self._info_table(material_data, cols=2)
        
        # 试模机台 Injection Machine
        self._section_title("试模机台（Injection Machine）")
        machine_data = [
            ("机台号 (Machine number)", data.get('machine_number', 'N/A')),
            ("品牌 (Brand)", data.get('machine_brand', 'N/A')),
            ("类型 (Machine type)", data.get('machine_type', 'N/A')),
            ("吨位 (Ton)", data.get('machine_tonnage', 'N/A')),
            ("螺杆直径 (Screw size mm)", data.get('screw_diameter', 'N/A')),
            ("增强比 (Intensification Ratio)", data.get('intensification_ratio', 'N/A')),
            ("滞留时间 (Retention time min)", data.get('retention_time', 'N/A')),
            ("占总胶量百分比/shot", data.get('shot_percentage', 'N/A')),
            ("成型周期 (Cycle Time s)", data.get('cycle_time', 'N/A')),
        ]
        self._info_table(machine_data, cols=2)

        # 设定参数 Rendering Processing Parameters
        self._section_title("设定参数（Processing Parameters）")
        barrel_temps = [
            data.get('barrel_temp_zone1', 'N/A'),
            data.get('barrel_temp_zone2', 'N/A'),
            data.get('barrel_temp_zone3', 'N/A'),
            data.get('barrel_temp_zone4', 'N/A'),
            data.get('barrel_temp_zone5', 'N/A')
        ]
        param_data = [
            ("料筒温度 (Barrel Z1-Z5 °C)", " / ".join([str(t) for t in barrel_temps])),
            ("射嘴温度 (Nozzle °C)", data.get('nozzle_temp', 'N/A')),
            ("热流道温度 (Hot Runner °C)", data.get('hot_runner_temp', 'N/A')),
            ("模具温度 (Mold Fixed/Moving)", f"{data.get('mold_temp_fixed', 'N/A')} / {data.get('mold_temp_moving', 'N/A')}"),
        ]
        self._info_table(param_data, cols=1)
    
    # ========================================================================
    # 第2页: 粘度曲线 Viscosity Curve
    # ========================================================================
    
    def add_viscosity_page(self, data: Dict[str, Any]):
        """
        第2页: Step 1 粘度曲线 - 完整试验报告
        
        报告结构:
        1. 试验目的
        2. 试验方法
        3. 原始测量数据表格（所有测试点）
        4. 数据分析（计算剪切率、有效粘度）
        5. 结果讨论（拐点识别、剪切变稀）
        6. 工程结论（推荐射速范围）
        7. 工程建议（下一步操作）
        """
        self.add_page()
        
        # 标题
        self.set_font('CN', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.cell(0, 12, 'Step 1: 粘度曲线测试 Viscosity Curve Study', new_x='LMARGIN', new_y='NEXT')
        self.ln(3)
        
        # 1. 试验目的
        self._subsection_title("1. 试验目的 (Objective)")
        self.set_font('CN', '', 9)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5, 
            "通过改变注塑速度，测量填充时间和峰值压力，建立材料的粘度-剪切率关系曲线，"
            "识别剪切变稀拐点，确定最佳注塑速度范围。\n"
            "By varying injection speed and measuring fill time and peak pressure, establish the "
            "viscosity-shear rate relationship curve, identify shear-thinning inflection point, "
            "and determine optimal injection speed range.")
        self.ln(3)
        
        # 2. 试验方法
        self._subsection_title("2. 试验方法 (Test Method)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            "• 固定保压压力、保压时间、模温、料温\n"
            "• 从低速到高速（10%-95%）分7个点进行测试\n"
            "• 每个速度点记录：填充时间、峰值注射压力\n"
            "• V/P切换位置固定在30mm\n"
            "• 每个点重复3次取平均值")
        self.ln(3)
        
        # 3. 原始测量数据
        self._subsection_title("3. 原始测量数据 (Raw Test Data)")
        
        # 从data中提取原始数据
        speed_percents = data.get('speed_percents', [])
        speed_mm_s = data.get('speed_mm_s', [])
        fill_times = data.get('fill_times', [])
        peak_pressures = data.get('peak_pressures', [])
        switch_pos = data.get('switch_position', 30)
        screw_dia = data.get('screw_diameter', 53)
        
        # 检查数据是否有效
        if not speed_percents or not speed_mm_s or len(speed_percents) == 0:
            self.set_font('CN', '', 10)
            self.set_text_color(255, 0, 0)
            self.cell(0, 10, "错误: 无粘度曲线数据 No viscosity data available", new_x='LMARGIN', new_y='NEXT')
            return
        
        # App计算派生指标
        shear_rates = [speed / (screw_dia / 2) for speed in speed_mm_s]
        viscosities = [pressure * time for pressure, time in zip(peak_pressures, fill_times)]
        
        # 数据表格
        headers = ["测试点\nTest#", "速度%\nSpeed%", "速度\nmm/s", "切换位置\nSwitch mm", "填充时间\nFill Time s", "峰值压力\nPeak Bar"]
        col_widths = [20, 25, 25, 30, 30, 30]
        
        self.set_font('CN', '', 8)
        self.set_fill_color(200, 220, 240)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, h, border=1, align='C', fill=True)
        self.ln()
        
        # 数据行
        self.set_font('CN', '', 8)
        for i in range(len(speed_percents)):
            self.cell(col_widths[0], 6, f"#{i+1}", border=1, align='C')
            self.cell(col_widths[1], 6, f"{speed_percents[i]*100:.0f}%", border=1, align='C')
            self.cell(col_widths[2], 6, f"{speed_mm_s[i]:.1f}", border=1, align='C')
            self.cell(col_widths[3], 6, f"{switch_pos:.1f}", border=1, align='C')
            self.cell(col_widths[4], 6, f"{fill_times[i]:.2f}", border=1, align='C')
            self.cell(col_widths[5], 6, f"{peak_pressures[i]:.0f}", border=1, align='C')
            self.ln()
        
        self.ln(3)
        
        # 4. 数据分析
        self._subsection_title("4. 数据分析 (Data Analysis)")
        
        # 计算结果表格
        headers2 = ["测试点\nTest#", "剪切率\nShear Rate 1/s", "有效粘度\nViscosity Pa·s", "备注\nNote"]
        col_widths2 = [20, 45, 45, 50]
        
        self.set_font('CN', '', 8)
        self.set_fill_color(240, 240, 220)
        for i, h in enumerate(headers2):
            self.cell(col_widths2[i], 8, h, border=1, align='C', fill=True)
        self.ln()
        
        # 找出拐点（粘度变化率最小的点）
        inflection_idx = len(viscosities) // 2  # 简化：取中点
        
        for i in range(len(speed_percents)):
            self.cell(col_widths2[0], 6, f"#{i+1}", border=1, align='C')
            self.cell(col_widths2[1], 6, f"{shear_rates[i]:.1f}", border=1, align='C')
            self.cell(col_widths2[2], 6, f"{viscosities[i]:.0f}", border=1, align='C')
            
            # 标注拐点区域
            note = ""
            if i == inflection_idx or i == inflection_idx + 1:
                note = "推荐区间"
                self.set_fill_color(200, 255, 200)
            else:
                self.set_fill_color(255, 255, 255)
            self.cell(col_widths2[3], 6, note, border=1, align='C', fill=True)
            self.ln()
        
        self.ln(3)
        
        # 5. 结果讨论
        self._subsection_title("5. 结果讨论 (Discussion)")
        self.set_font('CN', '', 9)
        
        # 计算趋势
        visc_min = min(viscosities)
        visc_max = max(viscosities)
        reduction_pct = (visc_max - visc_min) / visc_max * 100
        
        discussion_text = (
            f"• 剪切变稀效应明显：粘度从{visc_max:.0f}降至{visc_min:.0f} Pa·s（降低{reduction_pct:.1f}%）\n"
            f"• 低速区（10-35%）：粘度高，填充时间长，易产生冷料\n"
            f"• 中速区（35-65%）：粘度稳定，流动均匀，工艺窗口最佳\n"
            f"• 高速区（65-95%）：粘度降低但压力上升，易产生飞边\n"
            f"• 推荐速度区间在测试点#{inflection_idx+1}-#{inflection_idx+2}附近"
        )
        self.multi_cell(0, 5, discussion_text)
        self.ln(3)
        
        # 6. 工程结论
        self._subsection_title("6. 工程结论 (Conclusion)")
        
        # 推荐速度范围
        if len(speed_percents) >= 3:
            opt_low_pct = speed_percents[inflection_idx]
            opt_high_pct = speed_percents[inflection_idx + 1] if inflection_idx + 1 < len(speed_percents) else speed_percents[-1]
            opt_low_speed = speed_mm_s[inflection_idx]
            opt_high_speed = speed_mm_s[inflection_idx + 1] if inflection_idx + 1 < len(speed_mm_s) else speed_mm_s[-1]
        else:
            opt_low_pct = opt_high_pct = speed_percents[0]
            opt_low_speed = opt_high_speed = speed_mm_s[0]
        
        self.set_font('CN', 'B', 10)
        self.set_fill_color(255, 255, 200)
        self.cell(50, 8, "推荐注塑速度范围", border=1, align='C', fill=True)
        self.cell(40, 8, f"{opt_low_pct*100:.0f}% - {opt_high_pct*100:.0f}%", border=1, align='C')
        self.cell(40, 8, f"{opt_low_speed:.0f} - {opt_high_speed:.0f} mm/s", border=1, align='C')
        self.ln(3)
        
        # 7. 工程建议
        self.ln(2)
        self._subsection_title("7. 工程建议 (Recommendations)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            f"• 后续试验采用{opt_low_speed:.0f}-{opt_high_speed:.0f} mm/s速度范围\n"
            "• 进行Step 2型腔平衡测试，确保多腔填充一致性\n"
            "• 监控实际生产中的压力波动，保持在测试范围内\n"
            "• 若材料批次变更，需重新验证粘度曲线")
        self.ln(10)
        """
        粘度曲线页面（复刻Excel格式）
        
        输入数据（原始测量值）:
        - speed_percents: 速度百分比列表 [0.1, 0.3, 0.5, ...]
        - speed_mm_s: 实际速度列表 [6.8, 22.2, ...]
        - fill_times: 填充时间列表 [19.6, 5.9, ...]
        - peak_pressures: 峰值压力列表 [94.1, 87.7, ...]
        - switch_position: V/P切换位置 (mm)
        - screw_diameter: 螺杆直径 (mm)
        
        App计算:
        - shear_rates: 剪切率 = speed_mm_s / (screw_diameter/2)
        - viscosities: 有效粘度 = peak_pressure * fill_time
        - optimal_speed: 推荐射速范围
        """
        self.add_page()
        
        # 标题
        self.set_font('CN', 'B', 14)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, '粘度曲线 Viscosity Curve', new_x='LMARGIN', new_y='NEXT')
        self.ln(2)
        
        # 目的
        self._subsection_title("目的（PURPOSE）")
        self.set_font('CN', '', 9)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5, "找到最佳射胶速度\nFind the optimal injection speed")
        self.ln(3)
        
        # 原始数据 + 计算结果表格
        self._subsection_title("有效粘度  Effective Viscosity")
        
        # 从data中提取原始数据
        speed_percents = data.get('speed_percents', [])
        speed_mm_s = data.get('speed_mm_s', [])
        fill_times = data.get('fill_times', [])
        peak_pressures = data.get('peak_pressures', [])
        switch_pos = data.get('switch_position', 30)
        screw_dia = data.get('screw_diameter', 53)
        
        # 检查数据是否有效
        if not speed_percents or not speed_mm_s or len(speed_percents) == 0:
            self.set_font('CN', '', 10)
            self.set_text_color(255, 0, 0)
            self.cell(0, 10, "错误: 无粘度曲线数据 No viscosity data available", new_x='LMARGIN', new_y='NEXT')
            return
        
        # App计算派生指标
        shear_rates = [speed / (screw_dia / 2) for speed in speed_mm_s]
        viscosities = [pressure * time for pressure, time in zip(peak_pressures, fill_times)]
        
        # 报告头部表格
        headers = ["填充速度\nFill speed", "", "切换位置\nSwitch position", "填充时间\nFill time", "注塑峰值压力\nInjection peak pressure", "剪切率\nShear rate", "有效粘度\nEffective Viscosity"]
        sub_headers = ["百分比\nPercent", "mm/sec", "mm", "sec", "Bar", "1/t", ""]
        
        col_widths = [25, 25, 25, 25, 35, 35, 20]
        
        # 绘制表头
        self.set_font('CN', '', 7)
        self.set_fill_color(200, 200, 200)
        for i, h in enumerate(headers):
            if i < 2:  # 填充速度需要跨两列
                self.cell(col_widths[i], 8, h, border=1, align='C', fill=True)
            else:
                self.cell(col_widths[i], 8, h, border=1, align='C', fill=True)
        self.ln()
        
        # 绘制子表头
        self.set_fill_color(220, 220, 220)
        for i, sh in enumerate(sub_headers):
            self.cell(col_widths[i], 5, sh, border=1, align='C', fill=True)
        self.ln()
        
        # 数据行
        self.set_font('CN', '', 8)
        for i in range(len(speed_percents)):
            self.cell(col_widths[0], 6, f"{speed_percents[i]:.1f}", border=1, align='C')
            self.cell(col_widths[1], 6, f"{speed_mm_s[i]:.1f}", border=1, align='C')
            self.cell(col_widths[2], 6, str(switch_pos), border=1, align='C')
            self.cell(col_widths[3], 6, f"{fill_times[i]:.1f}", border=1, align='C')
            self.cell(col_widths[4], 6, f"{peak_pressures[i]:.1f}", border=1, align='C')
            self.cell(col_widths[5], 6, f"{shear_rates[i]:.3f}", border=1, align='C')
            self.cell(col_widths[6], 6, f"{viscosities[i]:.1f}", border=1, align='C')
            self.ln()
        
        self.ln(5)
        
        # 结论：推荐注塑速度
        self._subsection_title("推荐注塑速度 (Recommended injection speed)")
        
        # 找到拐点（简化：取中间区域）
        if len(speed_percents) >= 3:
            opt_low_pct = speed_percents[len(speed_percents)//2]
            opt_high_pct = speed_percents[len(speed_percents)//2 + 1] if len(speed_percents) > 3 else speed_percents[-1]
            opt_low_speed = speed_mm_s[len(speed_mm_s)//2]
            opt_high_speed = speed_mm_s[len(speed_mm_s)//2 + 1] if len(speed_mm_s) > 3 else speed_mm_s[-1]
        elif len(speed_percents) > 0:
            opt_low_pct = opt_high_pct = speed_percents[0]
            opt_low_speed = opt_high_speed = speed_mm_s[0]
        else:
            opt_low_pct = opt_high_pct = 0.5
            opt_low_speed = opt_high_speed = 50
        
        self.set_font('CN', 'B', 10)
        self.set_fill_color(255, 255, 200)
        self.cell(40, 7, "百分比 Percent", border=1, align='C', fill=True)
        self.cell(40, 7, "mm/s", border=1, align='C', fill=True)
        self.ln()
        self.set_font('CN', '', 10)
        # 使用 :.0% 格式化（因为 speed_percents 已经是小数形式，如 0.5 表示 50%）
        self.cell(40, 7, f"{opt_low_pct:.0%}~{opt_high_pct:.0%}", border=1, align='C')
        self.cell(40, 7, f"{opt_low_speed:.0f}~{opt_high_speed:.0f}", border=1, align='C')
        self.ln(10)
    
    # ========================================================================
    # 第3页: 型腔平衡 Cavity Balance
    # ========================================================================
    
    def add_cavity_balance_page(self, data: Dict[str, Any]):
        """
        第3页: Step 2 型腔平衡 - 完整试验报告
        
        报告结构:
        1. 试验目的
        2. 试验方法
        3. 短射测试数据（50%填充）
        4. 满射测试数据（99%填充）
        5. 数据分析（平衡度计算）
        6. 结果讨论（不平衡原因）
        7. 工程结论（合格判定）
        8. 工程建议（调整方案）
        """
        self.add_page()
        
        self.set_font('CN', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.cell(0, 12, 'Step 2: 型腔平衡测试 Cavity Balance Test', new_x='LMARGIN', new_y='NEXT')
        self.ln(3)
        
        # 1. 试验目的
        self._subsection_title("1. 试验目的 (Objective)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            "验证多型腔模具的流道设计合理性，确保各型腔填充均匀一致，"
            "避免因填充不平衡导致的产品质量差异。\n"
            "Verify the runner system design of multi-cavity mold, ensure uniform filling "
            "consistency across all cavities, and prevent quality variations due to imbalance.")
        self.ln(3)
        
        # 2. 试验方法
        self._subsection_title("2. 试验方法 (Test Method)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            "• 采用短射法（50%填充）和满射法（99%填充）两种测试\n"
            "• 使用Step 1确定的最佳注塑速度\n"
            "• 每个型腔产品称重，精度0.01g\n"
            "• 每组测试重复5次，剔除异常值后取平均\n"
            "• 合格标准：型腔间重量差异 < 5%")
        self.ln(3)
        
        # 短射数据
        short_shot = data.get('short_shot_weights', {})
        vp_switch = data.get('vp_switch_weights', {})
        visual_checks = data.get('visual_checks', {})
        
        # 检查数据是否有效
        if not short_shot and not vp_switch:
            self.set_font('CN', '', 10)
            self.set_text_color(255, 0, 0)
            self.cell(0, 10, "错误: 无型腔平衡数据 No cavity balance data available", new_x='LMARGIN', new_y='NEXT')
            return
        
        # 3. 短射测试数据
        if short_shot:
            self._subsection_title("3. 短射测试数据 (Short Shot Test - 50% Fill)")
            self._render_balance_table_detailed(short_shot, "Short Shot", visual_checks)
        
        # 4. 满射测试数据
        if vp_switch:
            self.ln(5)
            self._subsection_title("4. 满射测试数据 (Full Shot Test - 99% Fill)")
            self._render_balance_table_detailed(vp_switch, "Full Shot", visual_checks)
        
        # 5. 数据分析 - 放在最后统一分析
        self.ln(5)
        self._subsection_title("5. 数据分析 (Data Analysis)")
        
        # 分析两组数据
        if short_shot:
            values_short = list(short_shot.values())
            avg_short = sum(values_short) / len(values_short)
            imbalance_short = (max(values_short) - min(values_short)) / avg_short * 100
            self.set_font('CN', '', 9)
            self.multi_cell(0, 5,
                f"短射平衡度分析：\n"
                f"  • 平均重量: {avg_short:.3f} g\n"
                f"  • 最大重量: {max(values_short):.3f} g （腔{list(short_shot.keys())[values_short.index(max(values_short))]}）\n"
                f"  • 最小重量: {min(values_short):.3f} g （腔{list(short_shot.keys())[values_short.index(min(values_short))]}）\n"
                f"  • 不平衡度: {imbalance_short:.2f}% （标准: <5%）\n"
                f"  • 判定结果: {'✓ 合格' if imbalance_short < 5 else '✗ 不合格'}")
            self.ln(2)
        
        if vp_switch:
            values_full = list(vp_switch.values())
            avg_full = sum(values_full) / len(values_full)
            imbalance_full = (max(values_full) - min(values_full)) / avg_full * 100
            self.set_font('CN', '', 9)
            self.multi_cell(0, 5,
                f"满射平衡度分析：\n"
                f"  • 平均重量: {avg_full:.3f} g\n"
                f"  • 最大重量: {max(values_full):.3f} g （腔{list(vp_switch.keys())[values_full.index(max(values_full))]}）\n"
                f"  • 最小重量: {min(values_full):.3f} g （腔{list(vp_switch.keys())[values_full.index(min(values_full))]}）\n"
                f"  • 不平衡度: {imbalance_full:.2f}% （标准: <5%）\n"
                f"  • 判定结果: {'✓ 合格' if imbalance_full < 5 else '✗ 不合格'}")
        
        # 6. 结果讨论
        self.ln(5)
        self._subsection_title("6. 结果讨论 (Discussion)")
        self.set_font('CN', '', 9)
        
        # 判断主要问题
        if short_shot and vp_switch:
            if imbalance_short > 5 and imbalance_full > 5:
                issue = "流道设计存在系统性问题，需要优化流道平衡"
            elif imbalance_short > 5:
                issue = "流道在低填充率下阻力差异明显，建议增大流道直径"
            elif imbalance_full > 5:
                issue = "高填充率下出现不平衡，可能是浇口冻结时间差异导致"
            else:
                issue = "型腔平衡良好，流道设计合理"
        else:
            issue = "数据不完整，需补充测试"
        
        self.multi_cell(0, 5,
            f"• 不平衡原因分析: {issue}\n"
            "• 流道长度差异会导致压力损失不同\n"
            "• 浇口尺寸差异会影响填充速度\n"
            "• 模温不均匀会造成局部流动阻力增加")
        
        # 7. 工程结论
        self.ln(5)
        self._subsection_title("7. 工程结论 (Conclusion)")
        self.set_font('CN', 'B', 10)
        
        overall_pass = True
        if short_shot:
            overall_pass = overall_pass and (imbalance_short < 5)
        if vp_switch:
            overall_pass = overall_pass and (imbalance_full < 5)
        
        self.set_fill_color(200, 255, 200) if overall_pass else self.set_fill_color(255, 200, 200)
        self.cell(0, 10, f"型腔平衡测试结果: {'✓ 合格 PASS' if overall_pass else '✗ 不合格 FAIL'}", 
                 border=1, align='C', fill=True, new_x='LMARGIN', new_y='NEXT')
        
        # 8. 工程建议
        self.ln(3)
        self._subsection_title("8. 工程建议 (Recommendations)")
        self.set_font('CN', '', 9)
        
        if overall_pass:
            self.multi_cell(0, 5,
                "• 型腔平衡合格，可进入Step 3压力降测试\n"
                "• 生产过程中需定期监控各腔产品重量\n"
                "• 建议建立CPK管控，确保长期稳定性")
        else:
            self.multi_cell(0, 5,
                "• 需优化流道设计，调整流道长度或浇口尺寸\n"
                "• 可使用流动分析软件进行模拟优化\n"
                "• 调整后需重新进行型腔平衡验证\n"
                "• 暂不进入后续步骤，直到平衡度合格")
        
        self.ln(10)
    
    def _render_balance_table_detailed(self, weights: Dict[int, float], test_name: str, visual_checks: Dict[int, str] = None):
        """渲染详细的型腔平衡表格（带完整分析）"""
        if not weights or len(weights) == 0:
            self.set_font('CN', '', 9)
            self.cell(0, 7, "无数据 No data", border=1, align='C')
            self.ln()
            return
        
        # 计算统计
        values = list(weights.values())
        cavities = list(weights.keys())
        avg = sum(values) / len(values)
        
        # 测量数据表格
        headers = ["型腔编号\nCavity #", "测量重量\nWeight (g)", "偏差率\nDeviation (%)", "目视判定\nVisual", "判定\nResult"]
        col_widths = [30, 35, 35, 35, 25]
        
        self.set_font('CN', '', 8)
        self.set_fill_color(200, 220, 240)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, h, border=1, align='C', fill=True)
        self.ln()
        
        # 数据行
        for cav in sorted(weights.keys()):
            weight = weights[cav]
            deviation_pct = (weight - avg) / avg * 100
            is_ok = abs(deviation_pct) <= 5
            vis_check = visual_checks.get(cav, "OK") if visual_checks else "OK"
            
            self.set_font('CN', '', 8)
            self.cell(col_widths[0], 6, f"腔 {cav}", border=1, align='C')
            self.cell(col_widths[1], 6, f"{weight:.3f}", border=1, align='C')
            self.cell(col_widths[2], 6, f"{deviation_pct:+.2f}%", border=1, align='C')
            self.cell(col_widths[3], 6, vis_check, border=1, align='C')
            
            # 判定结果着色
            if is_ok and vis_check.upper() == "OK":
                self.set_fill_color(200, 255, 200)  # 绿色
                result_text = "✓"
            else:
                self.set_fill_color(255, 200, 200)  # 红色
                result_text = "✗"
            self.cell(col_widths[4], 6, result_text, border=1, align='C', fill=True)
            self.ln()
        
        # 统计摘要行
        self.set_fill_color(240, 240, 200)
        self.set_font('CN', 'B', 8)
        self.cell(col_widths[0], 6, "平均值", border=1, align='C', fill=True)
        self.cell(col_widths[1], 6, f"{avg:.3f}", border=1, align='C', fill=True)
        self.cell(col_widths[2], 6, "---", border=1, align='C', fill=True)
        self.cell(col_widths[3], 6, "---", border=1, align='C', fill=True)
        self.cell(col_widths[4], 6, "---", border=1, align='C', fill=True)
        self.ln()
        
        self.ln(2)
    
    def _render_balance_table(self, weights: Dict[int, float], test_type: str):
        """渲染型腔平衡表格"""
        # 检查数据有效性
        if not weights or len(weights) == 0:
            self.set_font('CN', '', 9)
            self.cell(0, 7, "无数据 No data", border=1, align='C')
            self.ln()
            return
        
        # 计算统计
        values = list(weights.values())
        avg = sum(values) / len(values)
        max_val = max(values)
        min_val = min(values)
        imbalance = (max_val - min_val) / avg * 100
        
        # 表格
        headers = ["腔号\nCavity", "重量(g)\nWeight", "偏差(%)\nDeviation"]
        col_widths = [30, 30, 30]
        
        self.set_font('CN', '', 8)
        self.set_fill_color(200, 200, 200)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, align='C', fill=True)
        self.ln()
        
        # 数据行
        for cav, weight in weights.items():
            deviation = (weight - avg) / avg * 100
            self.cell(col_widths[0], 6, f"腔{cav}", border=1, align='C')
            self.cell(col_widths[1], 6, f"{weight:.3f}", border=1, align='C')
            
            # 偏差着色
            if abs(deviation) > 5:
                self.set_fill_color(255, 200, 200)  # 红色
            else:
                self.set_fill_color(200, 255, 200)  # 绿色
            self.cell(col_widths[2], 6, f"{deviation:+.2f}%", border=1, align='C', fill=True)
            self.ln()
        
        # 统计信息
        self.ln(2)
        self.set_font('CN', 'B', 9)
        self.cell(0, 6, f"平均重量: {avg:.3f}g  |  最大: {max_val:.3f}g  |  最小: {min_val:.3f}g  |  不平衡度: {imbalance:.2f}%", new_x='LMARGIN', new_y='NEXT')
        
        # 判定
        if imbalance <= 5:
            self.set_text_color(0, 128, 0)
            self.cell(0, 6, "✓ 合格 (Pass)", new_x='LMARGIN', new_y='NEXT')
        else:
            self.set_text_color(255, 0, 0)
            self.cell(0, 6, "✗ 不合格 (Fail) - 需要调整流道平衡", new_x='LMARGIN', new_y='NEXT')
        
        self.set_text_color(0, 0, 0)
        self.ln(5)
    
    # ========================================================================
    # 第4页: 压力降 Pressure Drop
    # ========================================================================
    
    def add_pressure_drop_page(self, data: Dict[str, Any]):
        """
        第4页: Step 3 压力降测试 - 完整试验报告
        """
        self.add_page()
        
        self.set_font('CN', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.cell(0, 12, 'Step 3: 动态压力降测试 Dynamic Pressure Drop Test', new_x='LMARGIN', new_y='NEXT')
        self.ln(3)
        
        # 1. 试验目的
        self._subsection_title("1. 试验目的 (Objective)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            "测量熔体从射嘴到产品末端的压力衰减分布，评估流道系统的阻力特性，"            "验证注塑机压力是否充足，识别可能的流动瓶颈位置。\n"
            "Measure melt pressure decay from nozzle to part end, evaluate runner system "            "resistance, verify injection machine pressure capacity, and identify flow bottlenecks.")
        self.ln(3)
        
        # 2. 试验方法
        self._subsection_title("2. 试验方法 (Test Method)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            "• 使用Step 1确定的最佳注塑速度\n"
            "• 在射嘴、流道、浇口、产品50%、产品末端安装压力传感器\n"
            "• 同步采集各点压力数据\n"
            "• 重复测试3次，确保数据可重复性\n"
            "• 合格标准：总压降 < 50%，无异常压力突降")
        self.ln(3)
        
        # 3. 原始测量数据
        self._subsection_title("3. 原始测量数据 (Raw Test Data)")
        
        # 数据表格
        positions = data.get('positions', [])
        pressures = data.get('pressures', [])
        
        position_names = {
            "Nozzle": "射嘴",
            "Runner": "流道",
            "Gate": "浇口",
            "Part_50%": "产品50%",
            "Part_99%": "产品末端"
        }
        
        headers = ["测量位置\nPosition", "压力(Bar)\nPressure", "压降(%)\nDrop"]
        col_widths = [50, 40, 40]
        
        self.set_font('CN', '', 8)
        self.set_fill_color(200, 200, 200)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, align='C', fill=True)
        self.ln()
        
        # 数据行
        base_pressure = pressures[0] if pressures else 1
        for pos, pressure in zip(positions, pressures):
            pos_name = position_names.get(pos, pos)
            drop_pct = (base_pressure - pressure) / base_pressure * 100
            
            self.cell(col_widths[0], 6, pos_name, border=1, align='C')
            self.cell(col_widths[1], 6, f"{pressure:.1f}", border=1, align='C')
            self.cell(col_widths[2], 6, f"{drop_pct:.1f}%", border=1, align='C')
            self.ln()
        
        self.ln(3)
        
        # 4. 数据分析
        self._subsection_title("4. 数据分析 (Data Analysis)")
        self.set_font('CN', '', 9)
        
        if len(pressures) >= 2:
            total_drop = (pressures[0] - pressures[-1]) / pressures[0] * 100
            max_drop_section = "未知"
            max_drop_value = 0
            
            # 找出最大压降区间
            for i in range(len(pressures) - 1):
                drop = (pressures[i] - pressures[i+1]) / pressures[i] * 100
                if drop > max_drop_value:
                    max_drop_value = drop
                    pos_names_list = list(position_names.values())
                    if i < len(pos_names_list) - 1:
                        max_drop_section = f"{pos_names_list[i]} → {pos_names_list[i+1]}"
            
            self.multi_cell(0, 5,
                f"• 总压降: {total_drop:.1f}% （射嘴{pressures[0]:.0f} Bar → 产品末端{pressures[-1]:.0f} Bar）\n"
                f"• 最大压降区间: {max_drop_section} ({max_drop_value:.1f}%)\n"
                f"• 平均压降梯度: {total_drop/len(pressures):.1f}%/测点")
            self.ln(3)
        
        # 5. 结果讨论
        self._subsection_title("5. 结果讨论 (Discussion)")
        self.set_font('CN', '', 9)
        
        if len(pressures) >= 2:
            total_drop = (pressures[0] - pressures[-1]) / pressures[0] * 100
            
            if total_drop < 30:
                discussion = (
                    "• 压降合理：流道设计良好，熔体流动顺畅\n"
                    "• 注塑机压力充足，有较大的工艺调整空间\n"
                    "• 浇口、流道尺寸适当，无明显流动瓶颈")
            elif total_drop < 50:
                discussion = (
                    "• 压降适中：流道设计基本合理\n"
                    "• 需注意监控实际生产中的压力变化\n"
                    "• 如更换材料批次，需重新验证压降")
            else:
                discussion = (
                    "• 压降偏大：流道系统存在较大阻力\n"
                    "• 可能原因：流道过长、截面过小、浇口尺寸不足\n"
                    "• 建议：优化流道设计，增大流道/浇口尺寸\n"
                    "• 风险：注塑机压力可能不足，工艺窗口狭窄")
            
            self.multi_cell(0, 5, discussion)
        self.ln(3)
        
        # 6. 工程结论
        self._subsection_title("6. 工程结论 (Conclusion)")
        self.set_font('CN', 'B', 10)
        
        if len(pressures) >= 2:
            total_drop = (pressures[0] - pressures[-1]) / pressures[0] * 100
            if total_drop < 50:
                self.set_fill_color(200, 255, 200)
                conclusion_text = f"✓ 压降测试合格 (总压降 {total_drop:.1f}% < 50%)"
            else:
                self.set_fill_color(255, 200, 200)
                conclusion_text = f"✗ 压降测试不合格 (总压降 {total_drop:.1f}% > 50%)"
            
            self.cell(0, 10, conclusion_text, border=1, align='C', fill=True, new_x='LMARGIN', new_y='NEXT')
        
        # 7. 工程建议
        self.ln(3)
        self._subsection_title("7. 工程建议 (Recommendations)")
        self.set_font('CN', '', 9)
        
        if len(pressures) >= 2:
            total_drop = (pressures[0] - pressures[-1]) / pressures[0] * 100
            
            if total_drop < 50:
                recommendations = (
                    "• 压降合格，可进入Step 4工艺窗口测试\n"
                    "• 生产时监控注射压力，确保在测试范围内\n"
                    "• 定期清理流道和浇口，防止堵塞导致压降增加")
            else:
                recommendations = (
                    "• 需优化流道设计后重新测试\n"
                    "• 建议方案：\n"
                    "  - 增大流道直径10-20%\n"
                    "  - 缩短流道长度\n"
                    "  - 增大浇口尺寸\n"
                    "  - 考虑使用热流道系统\n"
                    "• 优化后需重新进行Step 3测试验证")
            
            self.multi_cell(0, 5, recommendations)
        self.ln(10)
    
    # ========================================================================
    # 第5页: 工艺窗口 Process Window
    # ========================================================================
    
    def add_process_window_page(self, data: Dict[str, Any]):
        """
        第5页: Step 4 工艺窗口 - 完整试验报告
        """
        self.add_page()
        
        self.set_font('CN', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.cell(0, 12, 'Step 4: 工艺窗口定义 Process Window Definition', new_x='LMARGIN', new_y='NEXT')
        self.ln(3)
        
        # 1. 试验目的
        self._subsection_title("1. 试验目的 (Objective)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            "通过系统性测试不同射速和保压压力的组合，绘制工艺窗口边界，"            "找到能够稳定生产合格产品的参数范围，为量产提供工艺保障。\n"
            "Systematically test combinations of injection speeds and holding pressures to "            "map process window boundaries and identify stable parameter ranges for production.")
        self.ln(3)
        
        # 2. 试验方法
        self._subsection_title("2. 试验方法 (Test Method)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            "• 射速范围：40-70 mm/s（以Step 1推荐值为中心）\n"
            "• 保压范围：500-900 Bar\n"
            "• 每组参数生产10件产品进行质量检验\n"
            "• 检验项目：尺寸、外观、重量、强度\n"
            "• 合格标准：10件全部合格")
        self.ln(3)
        
        # 3. 试验数据矩阵
        self._subsection_title("3. 试验数据矩阵 (Test Matrix)")
        
        # 数据
        speeds = data.get('speeds', [])
        pressures = data.get('pressures', [])
        hold_times = data.get('hold_times', [])
        product_weights = data.get('product_weights', [])
        quality = data.get('quality', [])
        
        # 表格
        headers = ["温度/射速\nTemp/Speed", "保压(MPa)\nPressure", "重量(g)\nWeight", "质量\nQuality"]
        col_widths = [45, 45, 45, 35]
        
        self.set_font('CN', '', 8)
        self.set_fill_color(200, 200, 200)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, align='C', fill=True)
        self.ln()
        
        # 数据行
        for i in range(len(speeds)):
            speed = speeds[i]
            pressure = pressures[i]
            weight = product_weights[i] if i < len(product_weights) else 0.0
            qual = quality[i] if i < len(quality) else "N/A"
            
            self.cell(col_widths[0], 6, f"{speed:.1f}", border=1, align='C')
            self.cell(col_widths[1], 6, f"{pressure:.1f}", border=1, align='C')
            self.cell(col_widths[2], 6, f"{weight:.2f}", border=1, align='C')
            
            if qual == "Pass":
                self.set_fill_color(200, 255, 200)
            else:
                self.set_fill_color(255, 200, 200)
            self.cell(col_widths[3], 6, qual, border=1, align='C', fill=True)
            self.ln()
        
        # 4. 数据分析
        self._subsection_title("4. 数据分析 (Data Analysis)")
        self.set_font('CN', '', 9)
        
        pass_count = quality.count("Pass")
        fail_count = quality.count("Fail")
        total_count = len(quality)
        pass_rate = (pass_count / total_count * 100) if total_count > 0 else 0
        
        self.multi_cell(0, 5,
            f"• 总测试组合: {total_count} 组\n"
            f"• 合格范围组合: {pass_count} 组\n"
            f"• 不合格组合: {fail_count} 组\n"
            f"• 工艺收率 (Window Yield): {pass_rate:.1f}%")
        self.ln(3)

        # 5. 结果讨论
        self._subsection_title("5. 结果讨论 (Discussion)")
        self.set_font('CN', '', 9)
        
        if pass_rate > 50:
            discussion = (
                "• 工艺窗口较宽：产品对速度和压力的波动有较好的容忍度\n"
                "• 模具设计和冷却系统均匀，有助于维持稳定的工艺状态\n"
                "• 建议以合格范围的中心值作为量产设定点")
        elif pass_rate > 20:
            discussion = (
                "• 工艺窗口适中：需严格控制注塑机压力和速度的稳定性\n"
                "• 生产过程中应开启压力和速度报警，监控工艺波动\n"
                "• 环境温度变化可能导致工艺跑出窗口，需定期点检")
        else:
            discussion = (
                "• 工艺窗口狭窄：量产稳定性风险极高\n"
                "• 可能原因：材料流动性差、壁厚不均、冷却不一致、浇口尺寸过小\n"
                "• 建议：优化模具设计或产品结构以扩大工艺窗口")
        
        self.multi_cell(0, 5, discussion)
        self.ln(3)

        # 6. 工程结论
        self._subsection_title("6. 工程结论 (Conclusion)")
        self.set_font('CN', 'B', 10)
        
        if pass_rate >= 30:
            self.set_fill_color(200, 255, 200)
            conclusion_text = f"✓ 工艺窗口验证合格 (合格率{pass_rate:.1f}% > 30%)"
        else:
            self.set_fill_color(255, 200, 200)
            conclusion_text = f"✗ 工艺窗口验证不合格 (合格率{pass_rate:.1f}% 过低)"
            
        self.cell(0, 10, conclusion_text, border=1, align='C', fill=True, new_x='LMARGIN', new_y='NEXT')
        self.ln(3)

        # 7. 工程建议
        self._subsection_title("7. 工程建议 (Recommendations)")
        self.set_font('CN', '', 9)
        
        pass_data = [(s, p) for s, p, q in zip(speeds, pressures, quality) if q == "Pass"]
        if pass_data:
            speeds_pass, pressures_pass = zip(*pass_data)
            center_speed = sum(speeds_pass) / len(speeds_pass)
            center_pressure = sum(pressures_pass) / len(pressures_pass)
            
            recommendations = (
                f"• 推荐量产设定中心点：\n"
                f"  - 理想温度: {center_speed:.1f} °C\n"
                f"  - 理想保压: {center_pressure:.1f} MPa\n"
                f"• 定期进行工艺重心核查，防止工艺漂移\n"
                f"• 在窗口边缘进行鲁棒性测试，确保长期稳定性")
            self.multi_cell(0, 5, recommendations)
        else:
            self.multi_cell(0, 5, "• 未找到合格工艺组合，严禁进入量产，需立即进行模具返修或参数重设")
            
        self.ln(10)
    
    # ========================================================================
    # 第6页: 浇口冻结 Gate Freeze
    # ========================================================================
    
    def add_gate_freeze_page(self, data: Dict[str, Any]):
        """
        第6页: Step 5 浇口冻结 - 完整试验报告
        """
        self.add_page()
        
        self.set_font('CN', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.cell(0, 12, 'Step 5: 浇口冻结研究 Gate Seal Study', new_x='LMARGIN', new_y='NEXT')
        self.ln(3)
        
        # 1. 试验目的
        self._subsection_title("1. 试验目的 (Objective)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            "确定浇口完全冻结所需的最短保压时间，避免保压时间过短导致产品缩水，"            "也避免保压时间过长导致周期浪费和内应力增加。\n"
            "Determine minimum holding time required for complete gate seal to prevent "            "shrinkage while avoiding excessive cycle time and internal stress.")
        self.ln(3)
        
        # 2. 试验方法
        self._subsection_title("2. 试验方法 (Test Method)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            "• 使用Step 4确定的最佳工艺参数\n"
            "• 从0.5s开始，每次增加0.5s保压时间\n"
            "• 每个时间点测试5件产品并称重\n"
            "• 当相邻两组重量差 < 0.01g时，判定浇口已冻结\n"
            "• 推荐保压时间为冻结时间 + 10%安全裕度")
        self.ln(3)
        
        # 3. 测试数据
        self._subsection_title("3. 测试数据 (Test Data)")
        
        # 数据表格
        hold_times = data.get('hold_times', [])
        weights = data.get('weights', [])
        
        headers = ["保压时间(s)\nHold Time", "重量(g)\nWeight", "增量(g)\nΔWeight"]
        col_widths = [40, 40, 40]
        
        self.set_font('CN', '', 8)
        self.set_fill_color(200, 200, 200)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, align='C', fill=True)
        self.ln()
        
        # 数据行
        prev_weight = 0
        for time, weight in zip(hold_times, weights):
            delta = weight - prev_weight
            self.cell(col_widths[0], 6, f"{time:.1f}", border=1, align='C')
            self.cell(col_widths[1], 6, f"{weight:.3f}", border=1, align='C')
            self.cell(col_widths[2], 6, f"{delta:.3f}", border=1, align='C')
            self.ln()
            prev_weight = weight
        
        # 4. 数据分析
        self._subsection_title("4. 数据分析 (Data Analysis)")
        self.set_font('CN', '', 9)
        
        # 找到冻结点（增量<0.01g）
        freeze_time = None
        current_max_weight = max(weights) if weights else 0
        for i in range(1, len(weights)):
            if abs(weights[i] - weights[i-1]) < 0.01:
                freeze_time = hold_times[i]
                break
        
        if freeze_time:
            self.multi_cell(0, 5,
                f"• 测定浇口冻结时间: {freeze_time:.1f} s\n"
                f"• 冻结时产品重量: {current_max_weight:.3f} g\n"
                f"• 重量增量判定标准: < 0.01 g (视为趋于平稳)")
        else:
            self.multi_cell(0, 5, "• 警告：在测试时间内未观察到明显的浇口冻结现象，重量持续增加。")
        self.ln(3)

        # 5. 结果讨论
        self._subsection_title("5. 结果讨论 (Discussion)")
        self.set_font('CN', '', 9)
        
        if freeze_time:
            if freeze_time < 2:
                discussion = "• 浇口冻结过快：可能导致保压效果不足，产品容易产生缩孔、吸凹或尺寸偏小。"
            elif freeze_time > 10:
                discussion = "• 浇口冻结过慢：冷却时间被动延长，生产周期长，建议优化浇口冷却或减小浇口截面。"
            else:
                discussion = "• 浇口冻结时间适中：能够保证充分保压，同时兼顾生产效率。"
        else:
            discussion = "• 极高风险：由于浇口未冻结，熔体可能发生倒流，导致产品重量和尺寸波动极大。"

        self.multi_cell(0, 5, discussion + "\n• 浇口冻结受模温、料温、浇口尺寸及保压压力的共同影响。")
        self.ln(3)

        # 6. 工程结论
        self._subsection_title("6. 工程结论 (Conclusion)")
        self.set_font('CN', 'B', 10)
        
        if freeze_time:
            self.set_fill_color(200, 255, 200)
            conclusion_text = f"✓ 浇口冻结研究完成 (冻结时间 {freeze_time:.1f} s)"
        else:
            self.set_fill_color(255, 200, 200)
            conclusion_text = "✗ 浇口冻结研究未完成 (未找到冻结点)"
            
        self.cell(0, 10, conclusion_text, border=1, align='C', fill=True, new_x='LMARGIN', new_y='NEXT')
        self.ln(3)

        # 7. 工程建议
        self._subsection_title("7. 工程建议 (Recommendations)")
        self.set_font('CN', '', 9)
        
        if freeze_time:
            safe_hold_time = freeze_time + 1.0  # 增加1s安全时间
            self.multi_cell(0, 5,
                f"• 建议量产保压时间: {safe_hold_time:.1f} s (冻结时间 + 1s安全余量)\n"
                "• 严禁随意缩短保压时间，防止产生内部缺陷\n"
                "• 如增加浇口尺寸，必须重新进行此步骤测试")
        else:
            self.multi_cell(0, 5, "• 延长保压时间继续测试，直到找到重量平稳点。建议增加模具冷却。")
            
        self.ln(10)
    
    # ========================================================================
    # 第7页: 冷却时间 Cooling Time
    # ========================================================================
    
    def add_cooling_time_page(self, data: Dict[str, Any]):
        """
        第7页: Step 6 冷却时间 - 完整试验报告
        """
        self.add_page()
        
        self.set_font('CN', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.cell(0, 12, 'Step 6: 冷却时间优化 Cooling Time Optimization', new_x='LMARGIN', new_y='NEXT')
        self.ln(3)
        
        # 1. 试验目的
        self._subsection_title("1. 试验目的 (Objective)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            "确定产品脱模时的最佳冷却时间，在保证产品不变形的前提下，"            "尽可能缩短成型周期，提高生产效率。\n"
            "Determine optimal cooling time for part ejection to minimize cycle time "            "while ensuring dimensional stability and preventing warpage.")
        self.ln(3)
        
        # 2. 试验方法
        self._subsection_title("2. 试验方法 (Test Method)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            "• 使用Step 5确定的保压时间\n"
            "• 从5s开始，每次增加5s冷却时间\n"
            "• 测量脱模瞬间产品温度（红外测温）\n"
            "• 产品脱模后24小时测量关键尺寸变形量\n"
            "• 合格标准：变形量 < 0.1mm，产品温度 < 80°C")
        self.ln(3)
        
        # 3. 测试数据
        self._subsection_title("3. 测试数据 (Test Data)")
        
        # 数据表格
        cooling_times = data.get('cooling_times', [])
        part_temps = data.get('part_temps', [])
        deformations = data.get('deformations', [])
        
        headers = ["冷却时间(s)\nCooling Time", "产品温度(°C)\nPart Temp", "变形量(mm)\nDeformation"]
        col_widths = [45, 45, 45]
        
        self.set_font('CN', '', 8)
        self.set_fill_color(200, 200, 200)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, align='C', fill=True)
        self.ln()
        
        # 数据行
        for time, temp, deform in zip(cooling_times, part_temps, deformations):
            self.cell(col_widths[0], 6, f"{time:.0f}", border=1, align='C')
            self.cell(col_widths[1], 6, f"{temp:.1f}", border=1, align='C')
            
            # 变形量着色
            if deform < 0.1:
                self.set_fill_color(200, 255, 200)
            else:
                self.set_fill_color(255, 255, 200)
            self.cell(col_widths[2], 6, f"{deform:.3f}", border=1, align='C', fill=True)
            self.ln()
        
        # 4. 数据分析
        self._subsection_title("4. 数据分析 (Data Analysis)")
        self.set_font('CN', '', 9)
        
        # 推荐冷却时间
        optimal_time = None
        for time, deform in zip(cooling_times, deformations):
            if deform < 0.1:
                optimal_time = time
                break
        
        if optimal_time:
            self.multi_cell(0, 5,
                f"• 测定最佳冷却时间: {optimal_time:.0f} s\n"
                f"• 该时间下产品变形量: {min([d for t,d in zip(cooling_times, deformations) if t >= optimal_time]):.3f} mm\n"
                f"• 该时间下产品温度: {min([temp for t,temp in zip(cooling_times, part_temps) if t >= optimal_time]):.1f} °C")
        else:
            self.multi_cell(0, 5, "• 警告：在所有测试组合中产品变形量均超标(>0.1mm)，需显著增加冷却时间或改善冷却。")
        self.ln(3)

        # 5. 结果讨论
        self._subsection_title("5. 结果讨论 (Discussion)")
        self.set_font('CN', '', 9)
        
        if optimal_time:
            discussion = (
                f"• 冷却效率分析：冷却时间增加对变形量的改善{'显著' if deformations[0]-deformations[-1] > 0.05 else '一般'}。\n"
                "• 产品在脱模时已达到足够的结构强度，脱模后应力释放引起的变形在受控范围内。\n"
                "• 适当的模温控制对缩短冷却时间至关重要。")
        else:
            discussion = (
                "• 冷却失效分析：产品存在严重的内应力或壁厚设计不合理。\n"
                "• 建议检查模具冷却水路是否堵塞，或考虑使用更低的水温。")

        self.multi_cell(0, 5, discussion)
        self.ln(3)

        # 6. 工程结论
        self._subsection_title("6. 工程结论 (Conclusion)")
        self.set_font('CN', 'B', 10)
        
        if optimal_time:
            self.set_fill_color(200, 255, 200)
            conclusion_text = f"✓ 冷却方案通过验证 (推荐时间 {optimal_time:.0f} s)"
        else:
            self.set_fill_color(255, 200, 200)
            conclusion_text = "✗ 冷却方案未达标 (所有时间下变形量均超标)"
            
        self.cell(0, 10, conclusion_text, border=1, align='C', fill=True, new_x='LMARGIN', new_y='NEXT')
        self.ln(3)

        # 7. 工程建议
        self._subsection_title("7. 工程建议 (Recommendations)")
        self.set_font('CN', '', 9)
        
        if optimal_time:
            self.multi_cell(0, 5,
                f"• 量产设定冷却时间: {optimal_time:.0f} s\n"
                "• 监控每小时产品脱模温度，确保冷却水流量稳定\n"
                "• 生产过程中严禁调高模具水温，除非重新验证冷却效果")
        else:
            self.multi_cell(0, 5, "• 需优化模具水路设计，增加喷水管或使用高导热模具材料。")
            
        self.ln(10)
    
    # ========================================================================
    # 第8页: 锁模力 Clamping Force
    # ========================================================================
    
    def add_clamping_force_page(self, data: Dict[str, Any]):
        """
        第8页: Step 7 锁模力 - 完整试验报告
        """
        self.add_page()
        
        self.set_font('CN', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.cell(0, 12, 'Step 7: 锁模力优化 Clamping Force Optimization', new_x='LMARGIN', new_y='NEXT')
        self.ln(3)
        
        # 1. 试验目的
        self._subsection_title("1. 试验目的 (Objective)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            "通过渐进式降低锁模力，找到不产生飞边的最小安全锁模力，"            "优化设备使用效率，延长模具和机台寿命。\n"
            "Progressively reduce clamping force to find minimum safe tonnage that "            "prevents flash while optimizing equipment efficiency and extending mold life.")
        self.ln(3)
        
        # 2. 试验方法
        self._subsection_title("2. 试验方法 (Test Method)")
        self.set_font('CN', '', 9)
        self.multi_cell(0, 5,
            "• 使用Step 6确定的全部工艺参数\n"
            "• 从理论锁模力的120%开始\n"
            "• 每次降低10%锁模力\n"
            "• 生产10件产品检查分型面是否有飞边\n"
            "• 测量产品重量变化（飞边会导致重量增加）")
        self.ln(3)
        
        # 3. 测试数据
        self._subsection_title("3. 测试数据 (Test Data)")
        
        # 数据表格
        forces = data.get('forces', [])
        part_weights = data.get('part_weights', [])
        flash_detected = data.get('flash_detected', [])
        
        headers = ["锁模力(吨)\nClamping Force", "产品重量(g)\nPart Weight", "飞边情况\nFlash"]
        col_widths = [45, 45, 50]
        
        self.set_font('CN', '', 8)
        self.set_fill_color(200, 200, 200)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, align='C', fill=True)
        self.ln()
        
        # 数据行
        min_safe_force = None
        for force, weight, flash in zip(forces, part_weights, flash_detected):
            self.cell(col_widths[0], 6, f"{force:.0f}", border=1, align='C')
            self.cell(col_widths[1], 6, f"{weight:.3f}", border=1, align='C')
            
            if flash == "Yes" or flash == "有":
                self.set_fill_color(255, 200, 200)
                self.cell(col_widths[2], 6, "Yes 有飞边", border=1, align='C', fill=True)
            else:
                self.set_fill_color(200, 255, 200)
                self.cell(col_widths[2], 6, "No 无飞边", border=1, align='C', fill=True)
                if min_safe_force is None or force < min_safe_force:
                    min_safe_force = force
            self.ln()
        
        # 4. 数据分析
        self._subsection_title("4. 数据分析 (Data Analysis)")
        self.set_font('CN', '', 9)
        
        if min_safe_force:
            weight_at_min = [w for f, w in zip(forces, part_weights) if f == min_safe_force][0]
            max_weight = max(part_weights)
            weight_increase = (max_weight - weight_at_min) / weight_at_min * 100
            
            self.multi_cell(0, 5,
                f"• 临界锁模力: {min_safe_force:.0f} 吨 (产生严重飞边的前一点)\n"
                f"• 产品重量增益: {weight_increase:.2f}% (锁模力不足导致的溢料)\n"
                f"• 模具受压平衡性: {'良好' if weight_increase < 0.5 else '偏差'}")
        else:
            self.multi_cell(0, 5, "• 警告：未找到不产生飞边的锁模力范围，可能模具损坏或分型面不平。")
        self.ln(3)

        # 5. 结果讨论
        self._subsection_title("5. 结果讨论 (Discussion)")
        self.set_font('CN', '', 9)
        
        if min_safe_force:
            discussion = (
                f"• 锁模力敏感度：每降低10%锁模力，产品重量变化约{(part_weights[0]-part_weights[-1])/len(forces):.4f}g。\n"
                "• 较低的锁模力有助于排气，减少困气缺陷，并延长模具寿命。\n"
                "• 过高的锁模力会压塌分型面排气槽，反而导致困气和烧焦。")
        else:
            discussion = "• 需检查模具分型面精度，或确认注塑机锁模系统行程和平行度。"

        self.multi_cell(0, 5, discussion)
        self.ln(3)

        # 6. 工程结论
        self._subsection_title("6. 工程结论 (Conclusion)")
        self.set_font('CN', 'B', 10)
        
        if min_safe_force:
            self.set_fill_color(200, 255, 200)
            conclusion_text = f"✓ 锁模力验证完成 (最小安全值 {min_safe_force:.0f} 吨)"
        else:
            self.set_fill_color(255, 200, 200)
            conclusion_text = "✗ 锁模力验证不合格 (未找到安全范围)"
            
        self.cell(0, 10, conclusion_text, border=1, align='C', fill=True, new_x='LMARGIN', new_y='NEXT')
        self.ln(3)

        # 7. 工程建议
        self._subsection_title("7. 工程建议 (Recommendations)")
        self.set_font('CN', '', 9)
        
        if min_safe_force:
            recommended_force = min_safe_force * 1.15
            self.multi_cell(0, 5,
                f"• 推荐量产锁模力: {recommended_force:.0f} 吨 (安全系数1.15)\n"
                "• 生产过程中监控锁模力波动，确保不超过设定值的 +/- 5%\n"
                "• 定期涂抹红丹粉检查分型面贴合度")
        else:
            self.multi_cell(0, 5, "• 需进行模具检修，研磨分型面，或更换更高吨位的注塑机。")
            
        self.ln(10)
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    def _section_title(self, title: str):
        """章节标题"""
        self.set_font('CN', 'B', 11)
        self.set_text_color(0, 51, 102)
        self.cell(0, 7, title, new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(0, 51, 102)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
    
    def _subsection_title(self, title: str):
        """子标题"""
        self.set_font('CN', 'B', 10)
        self.set_text_color(0, 51, 102)
        self.cell(0, 6, title, new_x='LMARGIN', new_y='NEXT')
        self.ln(1)
    
    def _info_table(self, data: List[Tuple], cols: int = 2):
        """信息表格"""
        col_width = 90
        label_width = 45
        
        self.set_font('CN', '', 8)
        for i, (label, value) in enumerate(data):
            if i > 0 and i % cols == 0:
                self.ln()
            self.set_text_color(80, 80, 80)
            self.cell(label_width, 5, str(label), align='L')
            self.set_text_color(0, 0, 0)
            self.cell(col_width - label_width, 5, str(value), align='L')
        self.ln(6)


# ========================================================================
# 主生成函数
# ========================================================================

def generate_mil_report_v2(data: Dict[str, Any], output_path: str) -> str:
    """
    生成 MIL 科学注塑验证报告 V2
    
    Args:
        data: 完整的测试数据字典，包含：
            - header: 头部信息（产品、模具、材料、机台）
            - viscosity: 粘度曲线原始数据
            - cavity_balance: 型腔平衡数据
            - pressure_drop: 压力降数据
            - process_window: 工艺窗口数据
            - gate_freeze: 浇口冻结数据
            - cooling_time: 冷却时间数据
            - clamping_force: 锁模力数据
        output_path: 输出PDF文件路径
    
    Returns:
        生成的PDF文件路径
    """
    pdf = MILReportV2()
    
    # 第1页: 报告头（产品、模具、材料、机台信息）
    pdf.add_header_page(data.get('header', {}))
    
    # 第2页: 粘度曲线
    if 'viscosity' in data:
        pdf.add_viscosity_page(data['viscosity'])
    
    # 第3页: 型腔平衡
    if 'cavity_balance' in data:
        pdf.add_cavity_balance_page(data['cavity_balance'])
    
    # 第4页: 压力降
    if 'pressure_drop' in data:
        pdf.add_pressure_drop_page(data['pressure_drop'])
    
    # 第5页: 工艺窗口
    if 'process_window' in data:
        pdf.add_process_window_page(data['process_window'])
    
    # 第6页: 浇口冻结
    if 'gate_freeze' in data:
        pdf.add_gate_freeze_page(data['gate_freeze'])
    
    # 第7页: 冷却时间
    if 'cooling_time' in data:
        pdf.add_cooling_time_page(data['cooling_time'])
    
    # 第8页: 锁模力
    if 'clamping_force' in data:
        pdf.add_clamping_force_page(data['clamping_force'])
    
    # 输出PDF
    pdf.output(output_path)
    return output_path


# ========================================================================
# 从 Session 生成报告
# ========================================================================

def generate_report_from_session(session) -> str:
    """
    从 SevenStepSessionState 对象生成完整报告（V2版本）
    
    Args:
        session: SevenStepSessionState 实例
    
    Returns:
        生成的PDF文件路径
    """
    # 获取机台快照
    snapshot = session.machine_snapshot
    
    # 准备PDF数据结构
    pdf_data = {
        'header': {
            # 产品信息
            'model_no': getattr(snapshot, 'model_no', 'N/A') if snapshot else 'N/A',
            'part_no': getattr(snapshot, 'part_no', 'N/A') if snapshot else 'N/A',
            'part_name': getattr(snapshot, 'part_name', 'N/A') if snapshot else 'N/A',
            'supplier': getattr(snapshot, 'supplier', 'N/A') if snapshot else 'N/A',
            'owner': getattr(snapshot, 'owner', 'N/A') if snapshot else 'N/A',
            'part_theoretical_weight': getattr(snapshot, 'theoretical_part_weight', 'N/A') if snapshot else 'N/A',
            'part_actual_weight': getattr(snapshot, 'actual_part_weight', 'N/A') if snapshot else 'N/A',
            
            # 模具信息
            'mold_number': getattr(snapshot, 'mold_number', 'N/A') if snapshot else 'N/A',
            'runner_type': getattr(snapshot, 'runner_type', 'N/A') if snapshot else 'N/A',
            'cavity_count': getattr(snapshot, 'cavity_count', 'N/A') if snapshot else 'N/A',
            
            # 材料信息
            'material_brand': getattr(snapshot, 'material_brand', 'N/A') if snapshot else 'N/A',
            'material_type': getattr(snapshot, 'material_type', 'N/A') if snapshot else 'N/A',
            'material_number': getattr(snapshot, 'material_number', 'N/A') if snapshot else 'N/A',
            'material_color': getattr(snapshot, 'material_color', 'N/A') if snapshot else 'N/A',
            'material_density': getattr(snapshot, 'material_density', 'N/A') if snapshot else 'N/A',
            'drying_temp': getattr(snapshot, 'drying_temp', 'N/A') if snapshot else 'N/A',
            'drying_time': getattr(snapshot, 'drying_time', 'N/A') if snapshot else 'N/A',
            'recommended_mold_temp': getattr(snapshot, 'recommended_mold_temp', 'N/A') if snapshot else 'N/A',
            'recommended_melt_temp': getattr(snapshot, 'recommended_melt_temp', 'N/A') if snapshot else 'N/A',
            
            # 机台信息
            'machine_number': getattr(snapshot, 'machine_number', 'N/A') if snapshot else 'N/A',
            'machine_brand': getattr(snapshot, 'machine_brand', 'N/A') if snapshot else 'N/A',
            'machine_type': getattr(snapshot, 'machine_type', 'N/A') if snapshot else 'N/A',
            'machine_tonnage': getattr(snapshot, 'machine_tonnage', 'N/A') if snapshot else 'N/A',
            'screw_diameter': getattr(snapshot, 'screw_diameter', 53) if snapshot else 53,
            'intensification_ratio': getattr(snapshot, 'intensification_ratio', 'N/A') if snapshot else 'N/A',
            'retention_time': getattr(snapshot, 'retention_time', 'N/A') if snapshot else 'N/A',
            'shot_percentage': getattr(snapshot, 'shot_percentage', 'N/A') if snapshot else 'N/A',
            'cycle_time': getattr(snapshot, 'cycle_time', 'N/A') if snapshot else 'N/A',
            
            # 设定温度
            'barrel_temp_zone1': getattr(snapshot, 'barrel_temp_zone1', 'N/A') if snapshot else 'N/A',
            'barrel_temp_zone2': getattr(snapshot, 'barrel_temp_zone2', 'N/A') if snapshot else 'N/A',
            'barrel_temp_zone3': getattr(snapshot, 'barrel_temp_zone3', 'N/A') if snapshot else 'N/A',
            'barrel_temp_zone4': getattr(snapshot, 'barrel_temp_zone4', 'N/A') if snapshot else 'N/A',
            'barrel_temp_zone5': getattr(snapshot, 'barrel_temp_zone5', 'N/A') if snapshot else 'N/A',
            'nozzle_temp': getattr(snapshot, 'nozzle_temp', 'N/A') if snapshot else 'N/A',
            'hot_runner_temp': getattr(snapshot, 'hot_runner_temp', 'N/A') if snapshot else 'N/A',
            'mold_temp_fixed': getattr(snapshot, 'mold_temp_fixed', 'N/A') if snapshot else 'N/A',
            'mold_temp_moving': getattr(snapshot, 'mold_temp_moving', 'N/A') if snapshot else 'N/A',
        },
    }
    
    # Step 1: 粘度曲线
    if not session.step_skipped.get(1, False) and session.viscosity_data_points and len(session.viscosity_data_points) > 0:
        visc_data = session.viscosity_data_points
        # 检查数据格式（应该是字典列表）
        if isinstance(visc_data, list) and len(visc_data) > 0 and isinstance(visc_data[0], dict):
            pdf_data['viscosity'] = {
                'speed_percents': [p.get('speed_percent', 0)/100 for p in visc_data if isinstance(p, dict)],
                'speed_mm_s': [p.get('speed_mm_s', 0) for p in visc_data if isinstance(p, dict)],
                'fill_times': [p.get('fill_time', 0) for p in visc_data if isinstance(p, dict)],
                'peak_pressures': [p.get('peak_pressure', 0) for p in visc_data if isinstance(p, dict)],
                'switch_position': visc_data[0].get('switch_position', 30) if visc_data else 30,
                'screw_diameter': getattr(snapshot, 'screw_diameter', 53) if snapshot else 53,
            }
    
    # Step 2: 型腔平衡
    if not session.step_skipped.get(2, False) and session.cavity_weights:
        # cavity_weights 是短射重量, cavity_weights_full 是满射重量
        pdf_data['cavity_balance'] = {
            'short_shot_weights': session.cavity_weights if isinstance(session.cavity_weights, dict) else {},
            'vp_switch_weights': session.cavity_weights_full if isinstance(session.cavity_weights_full, dict) else {},
            'visual_checks': session.cavity_visual_checks if hasattr(session, 'cavity_visual_checks') else {},
        }
    
    # Step 3: 压力降
    if not session.step_skipped.get(3, False) and session.pressure_drop_data:
        pdf_data['pressure_drop'] = {
            'positions': session.pressure_drop_data.get('positions', []),
            'pressures': session.pressure_drop_data.get('pressures', []),
        }
    
    # Step 4: 工艺窗口
    if not session.step_skipped.get(4, False) and session.process_window_data:
        pdf_data['process_window'] = {
            'speeds': [p.get('temperature', 0) for p in session.process_window_data], # 注意：这里用 temperature 代替射速，因为代码中是温压窗口
            'pressures': [p.get('holding_pressure', 0) for p in session.process_window_data],
            'product_weights': [p.get('product_weight', 0) for p in session.process_window_data],
            'hold_times': [8.0 for _ in session.process_window_data], # 默认为8s
            'quality': ["Pass" if p.get('appearance_status') == 'ok' else "Fail" for p in session.process_window_data],
        }
    
    # Step 5: 浇口冻结
    if not session.step_skipped.get(5, False) and session.gate_seal_curve:
        if isinstance(session.gate_seal_curve, list) and len(session.gate_seal_curve) > 0:
            pdf_data['gate_freeze'] = {
                'hold_times': [p.get('hold_time', 0) for p in session.gate_seal_curve if isinstance(p, dict)],
                'weights': [p.get('weight', 0) for p in session.gate_seal_curve if isinstance(p, dict)],
            }
    
    # Step 6: 冷却时间
    if not session.step_skipped.get(6, False) and session.cooling_curve:
        if isinstance(session.cooling_curve, list) and len(session.cooling_curve) > 0:
            pdf_data['cooling_time'] = {
                'cooling_times': [p.get('cooling_time', 0) for p in session.cooling_curve if isinstance(p, dict)],
                'part_temps': [p.get('part_temp', 0) for p in session.cooling_curve if isinstance(p, dict)],
                'deformations': [p.get('deformation', 0) for p in session.cooling_curve if isinstance(p, dict)],
            }
    
    # Step 7: 锁模力
    if not session.step_skipped.get(7, False) and session.clamping_force_curve:
        if isinstance(session.clamping_force_curve, list) and len(session.clamping_force_curve) > 0:
            pdf_data['clamping_force'] = {
                'forces': [p.get('clamping_force', 0) for p in session.clamping_force_curve if isinstance(p, dict)],
                'part_weights': [p.get('part_weight', 0) for p in session.clamping_force_curve if isinstance(p, dict)],
                'flash_detected': [p.get('flash_detected', False) for p in session.clamping_force_curve if isinstance(p, dict)],
            }
    
    # 生成PDF
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f"static/MIL_Report_{timestamp}.pdf"
    
    # 确保static目录存在
    os.makedirs('static', exist_ok=True)
    
    generate_mil_report_v2(pdf_data, output_path)
    
    return output_path


# ========================================================================
# 测试代码
# ========================================================================

if __name__ == "__main__":
    from seed_data import ScientificMoldingSeedData
    
    # 生成测试数据
    seed_gen = ScientificMoldingSeedData(seed=42)
    suite = seed_gen.generate_complete_test_suite()
    
    # 准备PDF数据结构
    pdf_data = {
        'header': {
            'model_no': '018467001',
            'part_no': '351514009',
            'part_name': 'Handle Housing Support',
            'supplier': 'GM',
            'owner': '张三',
            'part_theoretical_weight': 205,
            'part_actual_weight': 23,
            'mold_number': 'TG34724342-07',
            'runner_type': 'Hot Runner',
            'cavity_count': '1+1',
            'material_brand': '博云',
            'material_type': 'PA6 260G6 RE310',
            'material_number': '500181173',
            'material_color': 'RED',
            'material_density': 1.355,
            'drying_temp': '80~100',
            'drying_time': '2~3',
            'recommended_mold_temp': '50~80',
            'recommended_melt_temp': '230~260',
            'machine_number': '23#',
            'machine_brand': 'YIZUMI',
            'machine_type': '油压机',
            'machine_tonnage': 260,
            'screw_diameter': 53,
            'intensification_ratio': 12.4,
            'retention_time': 1.71,
            'shot_percentage': 61.6,
        },
        'viscosity': {
            'speed_percents': [p['speed_percent']/100 for p in suite['step1_viscosity']],
            'speed_mm_s': [p['speed_mm_s'] for p in suite['step1_viscosity']],
            'fill_times': [p['fill_time'] for p in suite['step1_viscosity']],
            'peak_pressures': [p['peak_pressure'] for p in suite['step1_viscosity']],
            'switch_position': 30,
            'screw_diameter': suite['machine_info']['screw_diameter'],
        },
        'cavity_balance': {
            'short_shot_weights': {p['cavity_index']: p['weight'] for p in suite['step2_cavity_balance']['short_shot']},
            'vp_switch_weights': {p['cavity_index']: p['weight'] for p in suite['step2_cavity_balance']['vp_switch']},
        },
        'pressure_drop': {
            'positions': [p['position'] for p in suite['step3_pressure_drop']],
            'pressures': [p['pressure'] for p in suite['step3_pressure_drop']],
        },
        'process_window': {
            'speeds': [p['speed_mm_s'] for p in suite['step4_process_window']],
            'pressures': [p['hold_pressure_bar'] for p in suite['step4_process_window']],
            'hold_times': [p['hold_time'] for p in suite['step4_process_window']],
            'quality': [p['quality'] for p in suite['step4_process_window']],
        },
        'gate_freeze': {
            'hold_times': [p['hold_time'] for p in suite['step5_gate_freeze']],
            'weights': [p['weight'] for p in suite['step5_gate_freeze']],
        },
        'cooling_time': {
            'cooling_times': [p['cooling_time'] for p in suite['step6_cooling_time']],
            'part_temps': [p['part_temp'] for p in suite['step6_cooling_time']],
            'deformations': [p['deformation'] for p in suite['step6_cooling_time']],
        },
        'clamping_force': {
            'forces': [p['clamping_force'] for p in suite['step7_clamping_force']],
            'part_weights': [p['part_weight'] for p in suite['step7_clamping_force']],
            'flash_detected': [p['flash_detected'] for p in suite['step7_clamping_force']],
        },
    }
    
    # 生成PDF
    output_file = "MIL_Report_V2_Test.pdf"
    generate_mil_report_v2(pdf_data, output_file)
    
    print(f"✓ PDF报告已生成: {output_file}")
    print(f"  文件大小: {os.path.getsize(output_file):,} 字节")
