"""
测试从 session 生成完整PDF报告
模拟用户完成7步测试后生成报告
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seed_data import ScientificMoldingSeedData
from pdf_generator_v2 import generate_brand1_report_v2

# 使用 seed_data 生成物理真实数据
seed_gen = ScientificMoldingSeedData(seed=42)
suite = seed_gen.generate_complete_test_suite()

# 准备PDF数据结构（不依赖session）
pdf_data = {
    'header': {
        'model_no': '018467001',
        'part_no': '351514009',
        'part_name': 'Handle Housing Support',
        'supplier': 'GM',
        'owner': '张三',
        'part_theoretical_weight': 20.5,
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
        'screw_diameter': suite['machine_info']['screw_diameter'],
        'intensification_ratio': suite['machine_info']['intensification_ratio'],
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

# 生成PDF报告
print("正在生成完整的Brand1科学注塑验证报告...")
output_path = "Brand1_Report_Complete_Test.pdf"
generate_brand1_report_v2(pdf_data, output_path)
file_size = os.path.getsize(output_path)

print(f"\n[OK] PDF报告生成成功!")
print(f"  文件路径: {output_path}")
print(f"  文件大小: {file_size:,} 字节 ({file_size/1024:.1f} KB)")
print(f"\n报告包含以下内容:")
print(f"  [OK] 产品、模具、材料、机台信息")
print(f"  [OK] Step 1: 粘度曲线测试 ({len(suite['step1_viscosity'])} 个数据点)")
print(f"  [OK] Step 2: 型腔平衡测试 (短射+满射)")
print(f"  [OK] Step 3: 压力降测试 ({len(suite['step3_pressure_drop'])} 个测量点)")
print(f"  [OK] Step 4: 工艺窗口 ({len(suite['step4_process_window'])} 组参数)")
print(f"  [OK] Step 5: 浇口冻结 ({len(suite['step5_gate_freeze'])} 个时间点)")
print(f"  [OK] Step 6: 冷却时间 ({len(suite['step6_cooling_time'])} 次测试)")
print(f"  [OK] Step 7: 锁模力优化 ({len(suite['step7_clamping_force'])} 个测试点)")
print(f"\n使用以下命令查看PDF:")
print(f"  open {output_path}")
