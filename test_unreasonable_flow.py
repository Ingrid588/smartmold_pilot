#!/usr/bin/env python3
"""
测试从0到1的科学注塑流程，使用不合理数据和跳过步骤，最后生成PDF报告。
要求使用实时AI点评。
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from session_state import get_session_state, MachineSnapshot
from scientific_molding_6steps import _get_ai_assessment
from global_state import app_state
from datetime import datetime

def create_test_session():
    """创建测试会话，使用不合理数据"""
    session = get_session_state()
    session.reset()

    # 设置不合理的机器快照数据
    session.machine_snapshot = MachineSnapshot(
        part_name='TestPart_Unreasonable',
        mold_number='M-TEST-UNREASONABLE',
        machine_brand='TestBrand',
        machine_tonnage=-100,  # 不合理：负吨位
        material_brand='TestMaterial',
        material_type='Plastic',
        cycle_time=0,  # 不合理：0秒
        barrel_temp_zone1=1000,  # 不合理：过高温度
        recommended_melt_temp=500,  # 不合理：过高
        mold_temp_fixed=200,  # 不合理：过高
        max_injection_pressure=-50,  # 不合理：负压力
        max_holding_pressure=0,
        vp_transfer_position=-10,  # 不合理：负位置
        vp_transfer_pressure=-500  # 不合理：负力
    )

    # 设置步骤跳过和数据质量
    session.step_skipped = {i: False for i in range(1, 8)}
    session.step_skipped[2] = True  # 跳过步骤2
    session.step_skipped[4] = True  # 跳过步骤4

    session.step_data_quality = {i: True for i in range(1, 8)}
    session.step_data_quality[1] = False  # 步骤1数据质量差
    session.step_data_quality[3] = False  # 步骤3数据质量差

    # 设置步骤数据（模拟不合理数据）
    session.step_data = {
        1: {
            'viscosity_data': [100, 200, 300, 400, 500],  # 不合理的高粘度
            'shear_rate': [1, 2, 3, 4, 5],
            'inflection_point': 1000  # 不合理的拐点
        },
        3: {
            'pressure_drop_data': [-10, -20, -30],  # 不合理的负压力降
            'flow_rate': [0, 0, 0]  # 不合理的零流量
        },
        5: {
            'gate_freeze_time': -5,  # 不合理的负时间
            'pressure_curve': [0, 0, 0]
        },
        6: {
            'cooling_time': 0,  # 不合理
            'temp_profile': [1000, 1000, 1000]  # 不合理的高温
        },
        7: {
            'clamping_force': -1000,  # 不合理
            'part_ejection_force': 0
        }
    }

    # 设置AI评估（使用真实AI点评）
    print("正在获取AI实时点评...")
    for step in range(1, 8):
        if not session.step_skipped.get(step, False):
            print(f"\n=== 步骤{step} AI点评过程 ===")
            print(f"正在调用AI API评估步骤{step}...")
            assessment = _get_ai_assessment(session, step=step)
            if assessment:
                print(f"✅ 步骤{step} AI点评获取成功 (提供商: OpenAI)")
                print(f"📝 结论:")
                for conclusion in assessment.get('conclusions', []):
                    print(f"   • {conclusion}")
                print(f"🎯 建议行动:")
                for action in assessment.get('actions', []):
                    print(f"   • {action}")
                print(f"⚠️  风险评估:")
                for risk in assessment.get('risks', []):
                    print(f"   • {risk}")
                print(f"{'='*50}")
            else:
                print(f"❌ 步骤{step} AI点评获取失败 - 请检查API配置")
                print(f"{'='*50}")

    return session

def generate_pdf_report(session, output_path):
    """生成完整的Brand1 PDF报告"""
    print("生成完整的Brand1科学注塑验证报告...")

    # 准备PDF数据结构，使用不合理数据
    pdf_data = {
        'header': {
            'model_no': 'TEST-UNREASONABLE',
            'part_no': 'PART-001',
            'part_name': session.machine_snapshot.part_name or 'TestPart',
            'supplier': 'TestSupplier',
            'owner': 'TestOwner',
            'part_theoretical_weight': -10,  # 不合理
            'part_actual_weight': -5,  # 不合理
            'mold_number': session.machine_snapshot.mold_number or 'M-TEST',
            'runner_type': 'Cold Runner',
            'cavity_count': '1',
            'material_brand': session.machine_snapshot.material_brand or 'TestMaterial',
            'material_type': session.machine_snapshot.material_type or 'Plastic',
            'material_number': 'MAT-001',
            'material_color': 'RED',
            'material_density': -1,  # 不合理
            'drying_temp': '1000',  # 不合理
            'drying_time': '-1',  # 不合理
            'recommended_mold_temp': '200',  # 不合理
            'recommended_melt_temp': str(session.machine_snapshot.recommended_melt_temp or 500),
            'machine_number': 'MACHINE-001',
            'machine_brand': session.machine_snapshot.machine_brand or 'TestBrand',
            'machine_type': 'Injection Molding',
            'machine_tonnage': session.machine_snapshot.machine_tonnage or -100,
            'screw_diameter': -50,  # 不合理
            'intensification_ratio': -10,  # 不合理
            'retention_time': -5,  # 不合理
            'shot_percentage': -20,  # 不合理
        },
        'step_statuses': {
            1: {'completed': True, 'skipped': False, 'quality': session.step_data_quality.get(1, True)},
            2: {'completed': False, 'skipped': True, 'quality': True},
            3: {'completed': True, 'skipped': False, 'quality': session.step_data_quality.get(3, True)},
            4: {'completed': False, 'skipped': True, 'quality': True},
            5: {'completed': True, 'skipped': False, 'quality': True},
            6: {'completed': True, 'skipped': False, 'quality': True},
            7: {'completed': True, 'skipped': False, 'quality': True},
        },
        'viscosity': {
            'speed_percents': [0.1, 0.2, 0.3, 0.4, 0.5],  # 不合理
            'speed_mm_s': [-10, -20, -30, -40, -50],  # 不合理
            'fill_times': [-1, -2, -3, -4, -5],  # 不合理
            'peak_pressures': [-100, -200, -300, -400, -500],  # 不合理
            'switch_position': -30,  # 不合理
            'screw_diameter': -50,  # 不合理
        },
        'cavity_balance': {
            'short_shot_weights': {1: -10, 2: -20},  # 不合理
            'vp_switch_weights': {1: -15, 2: -25},  # 不合理
        },
        'pressure_drop': {
            'positions': ['-10', '-20', '-30'],  # 不合理
            'pressures': [-50, -100, -150],  # 不合理
        },
        'process_window': {
            'speeds': [-10, -20, -30],  # 不合理
            'pressures': [-100, -200, -300],  # 不合理
            'hold_times': [-1, -2, -3],  # 不合理
            'quality': ['Bad', 'Bad', 'Bad'],
        },
        'gate_freeze': {
            'hold_times': [-1, -2, -3, -4, -5],  # 不合理
            'weights': [-10, -20, -30, -40, -50],  # 不合理
        },
        'cooling_time': {
            'cooling_times': [-5, -10, -15],  # 不合理
            'part_temps': [1000, 1000, 1000],  # 不合理
            'deformations': [-1, -2, -3],  # 不合理
        },
        'clamping_force': {
            'forces': [-1000, -2000, -3000],  # 不合理
            'part_weights': [-50, -100, -150],  # 不合理
            'flash_detected': [True, True, True],
        },
    }

    # 使用generate_brand1_report_v2生成完整报告
    from pdf_generator_v2 import generate_brand1_report_v2
    result_path = generate_brand1_report_v2(pdf_data, output_path, session=session)
    print(f"完整Brand1 PDF报告已生成: {result_path}")

def main():
    print("开始测试科学注塑流程...")

    # 禁用代理以避免网络问题
    import os
    os.environ.pop('HTTP_PROXY', None)
    os.environ.pop('HTTPS_PROXY', None)
    print("已禁用代理设置")

    # 设置API优先级，使用DeepSeek进行真实AI点评
    app_state["api_priority_order"] = ["deepseek", "openai", "gemini", "claude"]
    app_state["current_api"] = "deepseek"
    print("已设置API优先级：DeepSeek优先")

    # 创建测试会话
    session = create_test_session()
    print("测试会话创建完成")

    # 生成PDF报告
    output_path = "/Users/aaa/SmartMold_Pilot/test_unreasonable_data_report.pdf"
    generate_pdf_report(session, output_path)

    print("测试完成！")
    print(f"请查看生成的PDF报告: {output_path}")

if __name__ == "__main__":
    main()