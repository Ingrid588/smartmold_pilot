"""
SmartMold Pilot V3 - Seed Data Generator
生成符合物理规律的原始测试数据（Raw Data），而非计算后的结果。

核心原则：App是计算器，不是记录本。
- 存储: 速度%、时间、压力（原始测量值）
- 计算: 剪切率、粘度（App实时计算）
"""

import math
import random
from typing import List, Tuple, Dict


class ScientificMoldingSeedData:
    """生成符合科学注塑物理规律的原始数据"""
    
    def __init__(self, seed: int = 42):
        """
        Args:
            seed: 随机种子，确保可复现
        """
        random.seed(seed)
        
        # 项目信息（Project Info）
        self.project_info = {
            "model_no": "018467001",
            "part_no": "351514009",
            "part_name": "Handle Housing Support",
            "supplier": "GM",
            "engineer": "张工",
            "test_date": "2026-01-07",
        }
        
        # 产品信息（Part Info）
        self.part_info = {
            "theoretical_weight": 20.5,  # g
            "actual_weight": 23.0,  # g
            "volume": 16.9,  # cm³
        }
        
        # 模具信息（Mold Info）
        self.mold_info = {
            "mold_number": "TG34724342-07",
            "runner_type": "Hot Runner",
            "cavity_count": "1+1",
            "mold_size": "450x380x320",  # LWH (mm)
            "gate_type": "Side Gate",
        }
        
        # 机台参数（Machine Parameters）- 扩充版
        self.machine_params = {
            "brand": "YIZUMI",
            "model": "UN260EIII",
            "machine_number": "23#",
            "machine_type": "油压机",
            "tonnage": 260,
            "screw_diameter": 53,  # mm
            "intensification_ratio": 10.5,
            "max_pressure_bar": 1800,  # Bar
            "max_speed_mm_s": 200,  # mm/s
            "vp_switch_position": 30.0,  # mm (V/P切换位置)
            "retention_time": 1.71,  # min
            "shot_percentage": 61.6,  # % (占总胶量百分比)
            "cycle_time": 45,  # s (周期时间)
            "hot_runner_temp": 265,  # °C (Added)
            "barrel_temps": [245, 250, 255, 260, 265],  # Zone 1-5
        }
        
        # 材料参数（PA6 GF30）
        self.material_params = {
            "name": "PA6 GF30",
            "brand": "博云",
            "grade": "PA6 260G6 RE310",
            "material_number": "500181173",
            "color": "RED",
            "density": 1.36,  # g/cm³
            "melt_temp": 260,  # °C
            "drying_temp": "80~100",  # °C
            "drying_time": "2~3",  # H
            "recommended_mold_temp": "50~80",  # °C
            "recommended_melt_temp": "230~260",  # °C
            "mfr": "15~25",  # g/10min
            "power_law_index": 0.35,  # 流变学指数 n (非牛顿流体)
            "consistency_index": 5000,  # 流变学参数 K
        }
    
    # ============================================================
    # Step 1: 粘度曲线 - 生成原始压力和时间数据
    # ============================================================
    
    def generate_viscosity_raw_data(self, num_points: int = 7) -> List[Dict]:
        """
        生成粘度曲线的原始数据（压力、时间）。
        
        物理原理：
        1. 速度越快 → 填充时间越短
        2. 剪切变稀效应 → 速度越快，压力上升幅度减缓
        3. 压力 = f(速度, 材料粘度, 流道阻力)
        
        Returns:
            List of dicts with keys: speed_percent, speed_mm_s, fill_time, peak_pressure
        """
        data = []
        
        # 速度范围：10% ~ 95%
        speed_percents = [10, 20, 35, 50, 65, 80, 95]
        if num_points != 7:
            speed_percents = [10 + i * (85 / (num_points - 1)) for i in range(num_points)]
        
        screw_dia = self.machine_params["screw_diameter"]
        max_speed = self.machine_params["max_speed_mm_s"]
        
        for speed_pct in speed_percents:
            # 实际速度 (mm/s)
            speed_mm_s = (speed_pct / 100) * max_speed
            
            # 填充时间 (s) - 速度越快，时间越短
            # 基准：50%速度 → 2.5秒
            fill_time = 2.5 * (50 / speed_pct)
            
            # 剪切率 (1/s)
            shear_rate = speed_mm_s / (screw_dia / 2)
            
            # 粘度计算（Power Law模型）
            # η = K * (γ̇)^(n-1)
            # PA6在高剪切下有明显剪切变稀
            n = self.material_params["power_law_index"]
            K = self.material_params["consistency_index"]
            viscosity_pas = K * (shear_rate ** (n - 1))
            
            # 压力计算（修正版 - 符合注塑机实际范围）
            # 压力随速度增加，但有上限（剪切变稀效应）
            # 注塑机最大压力: 2000 Bar
            # 使用简化线性模型：压力 = 200 + 速度系数
            # 速度10% → 200 Bar, 速度95% → 1750 Bar
            pressure = 200 + (speed_pct / 100) * 1600
            
            # 限制在合理范围内 (200-1800 Bar)
            pressure = min(max(pressure, 200), 1800)
            
            # 添加测量噪声 (±3%)
            fill_time *= (1 + random.uniform(-0.03, 0.03))
            pressure *= (1 + random.uniform(-0.03, 0.03))
            
            data.append({
                "speed_percent": round(speed_pct, 1),
                "speed_mm_s": round(speed_mm_s, 1),
                "switch_position": 30.0,  # V/P切换位置固定为30mm
                "fill_time": round(fill_time, 3),
                "peak_pressure": round(pressure, 1),
            })
        
        return data
    
    # ============================================================
    # Step 2: 型腔平衡 - 区分短射和满射
    # ============================================================
    
    def generate_cavity_balance_data(
        self,
        num_cavities: int = 8,
        imbalance_percent: float = 3.0
    ) -> Dict[str, List[Dict]]:
        """
        生成型腔平衡原始数据。
        
        Args:
            num_cavities: 型腔数量
            imbalance_percent: 不平衡度 (%)
            
        Returns:
            Dict with keys: "short_shot", "vp_switch"
        """
        avg_weight_short = 6.2  # g (短射50% - 必须小于满射)
        avg_weight_full = 12.8  # g (满射99%)
        
        result = {
            "short_shot": self._generate_cavity_weights(
                num_cavities, avg_weight_short, imbalance_percent, test_type="Short_Shot"
            ),
            "vp_switch": self._generate_cavity_weights(
                num_cavities, avg_weight_full, imbalance_percent * 0.5, test_type="VP_Switch"
            )
        }
        
        return result
    
    def _generate_cavity_weights(
        self,
        num_cavities: int,
        avg_weight: float,
        imbalance_percent: float,
        test_type: str
    ) -> List[Dict]:
        """生成单次测试的各腔重量"""
        data = []
        
        # 生成不平衡分布
        weights = []
        for i in range(num_cavities):
            # 某些腔偏轻，某些偏重
            deviation = random.uniform(-imbalance_percent, imbalance_percent) / 100
            weight = avg_weight * (1 + deviation)
            weights.append(weight)
        
        for cav_idx, weight in enumerate(weights, start=1):
            data.append({
                "cavity_index": cav_idx,
                "weight": round(weight, 3),
                "visual_check": "OK" if random.random() > 0.1 else "NG",  # Added
                "test_type": test_type,
            })
        
        return data
    
    # ============================================================
    # Step 3: 压力降 - 标准测量位置
    # ============================================================
    
    def generate_pressure_drop_data(self) -> List[Dict]:
        """
        生成压力降数据（标准测量位置）。
        
        测量位置（枚举值）：
        - Nozzle: 射嘴
        - Runner: 流道
        - Gate: 浇口
        - Part_50%: 产品50%位置
        - Part_99%: 产品末端
        """
        # 压力从射嘴到产品末端递增（流动阻力累积）
        positions = ["Nozzle", "Runner", "Gate", "Part_50%", "Part_99%"]
        base_pressures = [50, 300, 600, 1000, 1200]  # Bar
        
        data = []
        for pos, pressure in zip(positions, base_pressures):
            # 添加测量噪声
            pressure *= (1 + random.uniform(-0.02, 0.02))
            data.append({
                "position": pos,
                "pressure": round(pressure, 1),
            })
        
        return data
    
    # ============================================================
    # Step 4: 工艺窗口 - 速度和压力组合测试
    # ============================================================
    
    def generate_process_window_data(self) -> List[Dict]:
        """
        生成工艺窗口测试数据。
        
        测试矩阵：不同速度和保压压力组合
        """
        data = []
        
        # 速度范围：40-70 mm/s
        speeds = [40, 50, 60, 70]
        # 保压压力范围：500-900 Bar
        pressures = [500, 650, 800, 900]
        
        for speed in speeds:
            for pressure in pressures:
                # 判断是否在工艺窗口内
                # 窗口中心：速度50-60，压力650-800
                in_window = (50 <= speed <= 60) and (650 <= pressure <= 800)
                
                # 边界判断
                near_boundary = (
                    (45 <= speed <= 65) and (600 <= pressure <= 850)
                )
                
                if in_window:
                    quality = "Pass"
                    # 产品重量随压力线性增加
                    prod_weight = 22.8 + (pressure / 1000) * 1.5
                elif near_boundary:
                    quality = "Pass" if random.random() > 0.3 else "Fail"
                    prod_weight = 22.5 + (pressure / 1000) * 1.5
                else:
                    quality = "Fail"
                    prod_weight = 22.0 + (pressure / 1000) * 1.5
                
                data.append({
                    "speed_mm_s": speed,
                    "hold_pressure_bar": pressure,
                    "product_weight": round(prod_weight, 3),  # Added
                    "hold_time": 8.0 + random.uniform(-1.0, 1.0),  # 保压时间 8±1s
                    "quality": quality,
                })
        
        return data
    
    # ============================================================
    # Step 5: 浇口冻结 - 保压时间和重量关系
    # ============================================================
    
    def generate_gate_freeze_data(self) -> List[Dict]:
        """
        生成浇口冻结测试数据。
        
        物理规律：
        - 保压时间短 → 重量不足
        - 保压时间适中 → 重量稳定
        - 保压时间过长 → 重量不再增加（浇口已冻结）
        """
        data = []
        
        hold_times = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
        
        # 浇口冻结时间：3.0秒
        freeze_time = 3.0
        max_weight = 12.85  # g
        
        for hold_time in hold_times:
            if hold_time < freeze_time:
                # 未冻结，重量持续增加
                weight = max_weight * (hold_time / freeze_time) * 0.95
                weight += max_weight * 0.05  # 基础重量
            else:
                # 已冻结，重量稳定
                weight = max_weight
            
            # 添加噪声
            weight *= (1 + random.uniform(-0.01, 0.01))
            
            data.append({
                "hold_time": hold_time,
                "weight": round(weight, 3),
            })
        
        return data
    
    # ============================================================
    # Step 6: 冷却时间 - 温度和变形关系
    # ============================================================
    
    def generate_cooling_time_data(self) -> List[Dict]:
        """
        生成冷却时间测试数据。
        
        物理规律：
        - 冷却时间越长 → 产品温度越低 → 变形越小
        """
        data = []
        
        cooling_times = [5, 8, 10, 12, 15, 18, 20, 25]
        
        for cool_time in cooling_times:
            # 温度下降曲线（指数衰减）
            initial_temp = 260  # °C (脱模时)
            ambient_temp = 25  # °C
            temp = ambient_temp + (initial_temp - ambient_temp) * math.exp(-cool_time / 10)
            
            # 变形量（温度越高，变形越大）
            # 基准：60°C时变形0.15mm
            deformation = 0.15 * ((temp - ambient_temp) / (60 - ambient_temp))
            deformation = max(0.01, deformation)
            
            # 添加噪声
            temp *= (1 + random.uniform(-0.02, 0.02))
            deformation *= (1 + random.uniform(-0.05, 0.05))
            
            data.append({
                "cooling_time": cool_time,
                "part_temp": round(temp, 1),
                "deformation": round(deformation, 3),
            })
        
        return data
    
    # ============================================================
    # Step 7: 锁模力 - 飞边检测
    # ============================================================
    
    def generate_clamping_force_data(self) -> List[Dict]:
        """
        生成锁模力测试数据。
        
        物理规律：
        - 锁模力过小 → 有飞边
        - 锁模力充足 → 无飞边
        - 最小安全锁模力：240吨
        """
        data = []
        
        forces = [200, 220, 230, 240, 250, 260, 270, 280]
        min_safe_force = 240  # 吨
        
        for force in forces:
            # 产品重量和飞边判断
            if force < min_safe_force:
                # 锁模力不足 -> 产品过重（有飞边）
                weight = self.part_info['actual_weight'] + random.uniform(0.5, 1.5)
                flash = "Yes"
            elif force < min_safe_force + 10:
                # 临界区域，可能有轻微飞边
                weight = self.part_info['actual_weight'] + random.uniform(-0.1, 0.5)
                flash = "Yes" if random.random() > 0.6 else "No"
            else:
                # 锁模力充足 -> 正常重量
                weight = self.part_info['actual_weight'] + random.uniform(-0.1, 0.1)
                flash = "No"
            
            data.append({
                "clamping_force": force,
                "part_weight": round(weight, 2),
                "flash_detected": flash,
            })
        
        return data
    
    # ============================================================
    # 完整测试套件生成
    # ============================================================
    
    def generate_complete_test_suite(self) -> Dict:
        """生成完整的7步测试数据套件"""
        return {
            "project_info": self.project_info,
            "part_info": self.part_info,
            "mold_info": self.mold_info,
            "machine_info": self.machine_params,
            "material_info": self.material_params,
            "step1_viscosity": self.generate_viscosity_raw_data(),
            "step2_cavity_balance": self.generate_cavity_balance_data(),
            "step3_pressure_drop": self.generate_pressure_drop_data(),
            "step4_process_window": self.generate_process_window_data(),
            "step5_gate_freeze": self.generate_gate_freeze_data(),
            "step6_cooling_time": self.generate_cooling_time_data(),
            "step7_clamping_force": self.generate_clamping_force_data(),
        }
    
    def print_summary(self, data: Dict):
        """打印数据摘要"""
        print("=" * 60)
        print("SmartMold 科学注塑测试数据生成")
        print("=" * 60)
        print(f"\n机台: {data['machine_info']['brand']} {data['machine_info']['model']}")
        print(f"螺杆直径: {data['machine_info']['screw_diameter']} mm")
        print(f"材料: {data['material_info']['name']}")
        print(f"\n生成数据:")
        print(f"  Step 1 粘度曲线: {len(data['step1_viscosity'])} 个测试点")
        print(f"  Step 2 型腔平衡: 短射 {len(data['step2_cavity_balance']['short_shot'])} 腔 + 满射 {len(data['step2_cavity_balance']['vp_switch'])} 腔")
        print(f"  Step 3 压力降: {len(data['step3_pressure_drop'])} 个测量位置")
        print(f"  Step 4 工艺窗口: {len(data['step4_process_window'])} 个测试组合")
        print(f"  Step 5 浇口冻结: {len(data['step5_gate_freeze'])} 个测试点")
        print(f"  Step 6 冷却时间: {len(data['step6_cooling_time'])} 个测试点")
        print(f"  Step 7 锁模力: {len(data['step7_clamping_force'])} 个测试点")
        print("\n" + "=" * 60)
        print("✓ 所有数据均为原始测量值（Raw Data）")
        print("✓ App 将实时计算派生指标（粘度、剪切率等）")
        print("=" * 60)


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    import json
    
    # 生成数据
    generator = ScientificMoldingSeedData(seed=42)
    data = generator.generate_complete_test_suite()
    
    # 打印摘要
    generator.print_summary(data)
    
    # 保存到JSON
    output_file = "seed_data_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 数据已保存到: {output_file}")
    
    # 显示Step 1样本数据
    print("\n" + "=" * 60)
    print("Step 1 粘度曲线原始数据样本（前3个点）:")
    print("=" * 60)
    for i, point in enumerate(data['step1_viscosity'][:3], 1):
        print(f"\n测试点 {i}:")
        print(f"  速度百分比: {point['speed_percent']}%")
        print(f"  实际速度: {point['speed_mm_s']} mm/s")
        print(f"  填充时间: {point['fill_time']} s")
        print(f"  峰值压力: {point['peak_pressure']} Bar")
        print(f"  → App将计算: 剪切率 和 有效粘度")
