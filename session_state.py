"""
SmartMold Pilot V3 - Session State Management
Implements data inheritance across the 7-step scientific molding workflow.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MachineSnapshot:
    """Machine parameter snapshot at experiment time."""
    # 产品信息 Product Information
    model_no: Optional[str] = None
    part_no: Optional[str] = None
    part_name: Optional[str] = None
    supplier: Optional[str] = None
    owner: Optional[str] = None
    theoretical_part_weight: Optional[float] = None
    actual_part_weight: Optional[float] = None
    
    # 模具信息 Mold Information
    mold_number: Optional[str] = None
    runner_type: Optional[str] = None
    cavity_count: Optional[str] = None
    cycle_time: Optional[float] = None  # Added Cycle Time
    
    # 材料信息 Material Information
    material_brand: Optional[str] = None
    material_type: Optional[str] = None
    material_number: Optional[str] = None
    material_color: Optional[str] = None
    material_density: Optional[float] = None
    drying_temp: Optional[str] = None
    drying_time: Optional[str] = None
    recommended_mold_temp: Optional[str] = None
    recommended_melt_temp: Optional[str] = None
    
    # 机台信息 Machine Information
    machine_number: Optional[str] = None
    machine_brand: Optional[str] = None
    machine_type: Optional[str] = None
    machine_tonnage: Optional[float] = None
    intensification_ratio: Optional[float] = None
    retention_time: Optional[float] = None
    shot_percentage: Optional[float] = None
    
    # Temperature zones
    barrel_temp_zone1: Optional[float] = None
    barrel_temp_zone2: Optional[float] = None
    barrel_temp_zone3: Optional[float] = None
    barrel_temp_zone4: Optional[float] = None  # Expanded
    barrel_temp_zone5: Optional[float] = None  # Expanded
    nozzle_temp: Optional[float] = None
    hot_runner_temp: Optional[float] = None  # Added
    mold_temp_fixed: Optional[float] = None
    mold_temp_moving: Optional[float] = None
    
    # Pressure & Speed
    max_injection_pressure: Optional[float] = None
    max_holding_pressure: Optional[float] = None
    screw_diameter: Optional[float] = None
    
    # V/P Transfer
    vp_transfer_position: Optional[float] = None
    vp_transfer_pressure: Optional[float] = None
    
    # Timestamp
    snapshot_time: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            # 产品信息
            "model_no": self.model_no,
            "part_no": self.part_no,
            "part_name": self.part_name,
            "supplier": self.supplier,
            "owner": self.owner,
            "theoretical_part_weight": self.theoretical_part_weight,
            "actual_part_weight": self.actual_part_weight,
            # 模具信息
            "mold_number": self.mold_number,
            "runner_type": self.runner_type,
            "cavity_count": self.cavity_count,
            "cycle_time": self.cycle_time,
            # 材料信息
            "material_brand": self.material_brand,
            "material_type": self.material_type,
            "material_number": self.material_number,
            "material_color": self.material_color,
            "material_density": self.material_density,
            "drying_temp": self.drying_temp,
            "drying_time": self.drying_time,
            "recommended_mold_temp": self.recommended_mold_temp,
            "recommended_melt_temp": self.recommended_melt_temp,
            # 机台信息
            "machine_number": self.machine_number,
            "machine_brand": self.machine_brand,
            "machine_type": self.machine_type,
            "machine_tonnage": self.machine_tonnage,
            "intensification_ratio": self.intensification_ratio,
            "retention_time": self.retention_time,
            "shot_percentage": self.shot_percentage,
            # 温度区域
            "barrel_temp_zone1": self.barrel_temp_zone1,
            "barrel_temp_zone2": self.barrel_temp_zone2,
            "barrel_temp_zone3": self.barrel_temp_zone3,
            "barrel_temp_zone4": self.barrel_temp_zone4,
            "barrel_temp_zone5": self.barrel_temp_zone5,
            "nozzle_temp": self.nozzle_temp,
            "hot_runner_temp": self.hot_runner_temp,
            "mold_temp_fixed": self.mold_temp_fixed,
            "mold_temp_moving": self.mold_temp_moving,
            # 压力速度
            "max_injection_pressure": self.max_injection_pressure,
            "max_holding_pressure": self.max_holding_pressure,
            "screw_diameter": self.screw_diameter,
            # VP切换
            "vp_transfer_position": self.vp_transfer_position,
            "vp_transfer_pressure": self.vp_transfer_pressure,
            "snapshot_time": self.snapshot_time,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MachineSnapshot':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class SevenStepSessionState:
    """
    Global state manager for the 7-step workflow.
    Stores intermediate results from each step to be inherited by subsequent steps.
    
    7-Step Scientific Molding Workflow:
    1. 粘度曲线分析 (Viscosity Curve)
    2. 型腔平衡测试 (Cavity Balance)
    3. 压力降测试 (Pressure Drop)
    4. 工艺窗口定义 (Process Window)
    5. 浇口冻结测试 (Gate Seal)
    6. 冷却时间优化 (Cooling Time)
    7. 锁模力优化 (Clamping Force)
    """
    
    def __init__(self):
        # Step outputs (inherited parameters)
        self.optimal_injection_speed: Optional[float] = None  # From Step 1
        self.optimal_holding_pressure: Optional[float] = None  # From Step 4
        self.gate_freeze_time: Optional[float] = None  # From Step 5
        self.recommended_cooling_time: Optional[float] = None  # From Step 6
        self.recommended_clamping_force: Optional[float] = None  # From Step 7
        
        # Step 1: Viscosity Curve
        self.viscosity_inflection_point: Optional[Dict[str, float]] = None
        self.viscosity_data_points: list = []
        
        # Step 2: Cavity Balance
        self.cavity_balance_ratio: Optional[float] = None
        self.cavity_weights: Optional[Dict[int, float]] = None  # Short shot weights
        self.cavity_weights_full: Optional[Dict[int, float]] = None  # Full shot weights
        
        # Step 3: Pressure Drop
        self.pressure_margin: Optional[float] = None
        self.pressure_limited: bool = False
        self.pressure_drop_data: Optional[Dict[str, Any]] = None  # Detailed pressures
        
        # Step 4: Process Window (O-Window)
        self.process_window_bounds: Optional[Dict[str, Any]] = None
        self.window_center: Optional[Dict[str, float]] = None
        self.process_window_data: Optional[list] = None  # Raw test points
        
        # Step 5: Gate Seal
        self.gate_seal_curve: Optional[list] = None
        
        # Step 6: Cooling Time
        self.cooling_curve: Optional[list] = None
        
        # Step 7: Clamping Force
        self.clamping_force_curve: Optional[list] = None
        self.min_clamping_force: Optional[float] = None
        
        # Machine snapshot (frozen at experiment start)
        self.machine_snapshot: Optional[MachineSnapshot] = None
        
        # Current step (1-7)
        self.current_step: int = 1
        
        # Experiment metadata
        self.experiment_id: Optional[int] = None
        self.machine_id: Optional[int] = None
        self.mold_id: Optional[int] = None
        self.session_code: Optional[str] = None
        
        # Step remarks (for unreasonable data explanations)
        self.step_remarks: Dict[int, Dict[str, Any]] = {}
        
        # Step data quality (True=reasonable, False=unreasonable)
        self.step_data_quality: Dict[int, bool] = {}
        
        # Step skipped status
        self.step_skipped: Dict[int, bool] = {}

        # Realtime AI assessments captured during the workflow (do not call AI during PDF generation)
        # step index: 0..7
        self.ai_assessments: Dict[int, Dict[str, Any]] = {}

    def set_ai_assessment(self, step: int, assessment: Dict[str, Any], provider: Optional[str] = None):
        """Store realtime AI assessment for a step.

        step: 0..7
        assessment: provider response dict (best-effort JSON)
        provider: 'openai'/'gemini'/etc.
        """
        if assessment is None:
            return
        try:
            step_int = int(step)
        except Exception:
            return
        if step_int < 0 or step_int > 7:
            return
        self.ai_assessments[step_int] = {
            'provider': provider,
            'timestamp': datetime.now().isoformat(),
            'assessment': assessment,
        }

    def get_ai_assessments(self) -> Dict[int, Dict[str, Any]]:
        """Get all stored realtime AI assessments."""
        return self.ai_assessments
    
    def set_step_remark(self, step: int, reason: str, remark: str, data_issue: str):
        """Store remark for a step with unreasonable data."""
        self.step_remarks[step] = {
            'reason': reason,
            'remark': remark,
            'data_issue': data_issue,
            'timestamp': datetime.now().isoformat()
        }
        self.step_data_quality[step] = False
        print(f"[SessionState] Step {step} marked as unreasonable: {data_issue}")
    
    def set_step_skipped(self, step: int, skipped: bool = True):
        """Mark a step as skipped."""
        self.step_skipped[step] = skipped
        print(f"[SessionState] Step {step} marked as skipped")
    
    def is_step_skipped(self, step: int) -> bool:
        """Check if a step was skipped."""
        return self.step_skipped.get(step, False)
    
    def set_step_quality(self, step: int, is_reasonable: bool):
        """Set the data quality for a step."""
        self.step_data_quality[step] = is_reasonable
    
    def get_step_remarks(self) -> Dict[int, Dict[str, Any]]:
        """Get all step remarks."""
        return self.step_remarks
    
    def reset(self):
        """Reset all state (start new experiment)."""
        self.__init__()
    
    def set_step1_result(self, optimal_speed: float, inflection_data: Dict[str, float]):
        """Store Step 1 (Viscosity) results."""
        self.optimal_injection_speed = optimal_speed
        self.viscosity_inflection_point = inflection_data
        print(f"[SessionState] Step 1 completed: Optimal Speed = {optimal_speed} mm/s")
    
    def set_step2_result(self, balance_ratio: float, cavity_weights: Dict[int, float], cavity_weights_full: Optional[Dict[int, float]] = None, visual_checks: Optional[Dict[int, str]] = None):
        """Set Step 2 results."""
        self.cavity_balance_ratio = balance_ratio
        self.cavity_weights = cavity_weights
        self.cavity_weights_full = cavity_weights_full
        self.cavity_visual_checks = visual_checks or {k: "OK" for k in cavity_weights.keys()}
        print(f"[SessionState] Step 2 completed: cavity_balance_ratio = {balance_ratio}")
    
    def set_step3_result(self, margin: float, is_limited: bool, detailed_data: Optional[Dict[str, Any]] = None):
        """Store Step 3 (Pressure Drop) results."""
        self.pressure_margin = margin
        self.pressure_limited = is_limited
        if detailed_data:
            self.pressure_drop_data = detailed_data
        print(f"[SessionState] Step 3 completed: Margin = {margin} MPa, Limited = {is_limited}")
    
    def set_step4_result(self, optimal_pressure: float, window_bounds: Dict[str, Any], raw_data: Optional[list] = None):
        """Store Step 4 (Process Window) results."""
        self.optimal_holding_pressure = optimal_pressure
        self.process_window_bounds = window_bounds
        self.window_center = window_bounds.get('center', {})
        if raw_data:
            self.process_window_data = raw_data
        print(f"[SessionState] Step 4 completed: Optimal Holding Pressure = {optimal_pressure} MPa")
    
    def set_step5_result(self, freeze_time: float, seal_curve: list):
        """Store Step 5 (Gate Seal) results."""
        self.gate_freeze_time = freeze_time
        self.gate_seal_curve = seal_curve
        print(f"[SessionState] Step 5 completed: Gate Freeze Time = {freeze_time}s")
    
    def set_step6_result(self, cooling_time: float, curve: list):
        """Store Step 6 (Cooling Time) results."""
        self.recommended_cooling_time = cooling_time
        self.cooling_curve = curve
        print(f"[SessionState] Step 6 completed: Recommended Cooling Time = {cooling_time}s")
    
    def set_step7_result(self, clamping_force: float, curve: list):
        """Store Step 7 (Clamping Force Optimization) results."""
        self.recommended_clamping_force = clamping_force
        self.clamping_force_curve = curve
        print(f"[SessionState] Step 7 completed: Recommended Clamping Force = {clamping_force} Ton")
    
    def get_inherited_params(self, step: int) -> Dict[str, Any]:
        """
        Get parameters that should be inherited by the given step.
        
        Step 2, 3: Inherit optimal_injection_speed from Step 1
        Step 5: Inherit optimal_holding_pressure from Step 4
        Step 6: Inherit gate_freeze_time from Step 5
        """
        params = {}
        
        if step == 2 or step == 3:
            # Steps 2 & 3 must use the optimal speed from Step 1
            if self.optimal_injection_speed is not None:
                params['injection_speed'] = self.optimal_injection_speed
                params['injection_speed_locked'] = True
                params['lock_reason'] = 'Inherited from Step 1 (Viscosity Curve)'
        
        if step == 5:
            # Step 5 uses optimal holding pressure from Step 4
            if self.optimal_holding_pressure is not None:
                params['holding_pressure'] = self.optimal_holding_pressure
                params['holding_pressure_locked'] = True
                params['lock_reason'] = 'Inherited from Step 4 (Process Window)'
        
        if step == 6:
            # Step 6 uses gate freeze time as minimum holding time
            if self.gate_freeze_time is not None:
                params['min_holding_time'] = self.gate_freeze_time
                params['holding_time_locked'] = True
                params['lock_reason'] = 'Inherited from Step 5 (Gate Seal)'
        
        return params
    
    def can_proceed_to_step(self, step: int) -> tuple[bool, str]:
        """
        Check if user can proceed to a given step.
        Returns (can_proceed, reason).
        跳过的步骤也算完成。
        """
        if step == 1:
            return True, "Step 1 is always accessible"
        
        if step == 2:
            # 步骤1完成或跳过都可以
            if self.optimal_injection_speed is None and not self.step_skipped.get(1, False):
                return False, "Please complete Step 1 (Viscosity Curve) first"
            return True, "OK"
        
        if step == 3:
            # 步骤1完成或跳过都可以
            if self.optimal_injection_speed is None and not self.step_skipped.get(1, False):
                return False, "Please complete Step 1 first"
            return True, "OK"
        
        if step == 4:
            return True, "Step 4 can be accessed independently"
        
        if step == 5:
            # 步骤4完成或跳过都可以
            if self.optimal_holding_pressure is None and not self.step_skipped.get(4, False):
                return False, "Please complete Step 4 (Process Window) first"
            return True, "OK"
        
        if step == 6:
            # 步骤5完成或跳过都可以
            if self.gate_freeze_time is None and not self.step_skipped.get(5, False):
                return False, "Please complete Step 5 (Gate Seal) first"
            return True, "OK"
        
        if step == 7:
            # 步骤6完成或跳过都可以进入步骤7
            if self.recommended_cooling_time is None and not self.step_skipped.get(6, False):
                return False, "Please complete Step 6 (Cooling Time) first"
            return True, "OK"
        
        return False, "Invalid step number"
    
    def is_all_completed(self) -> bool:
        """Check if all 7 steps are completed."""
        return all([
            self.optimal_injection_speed is not None,
            self.cavity_balance_ratio is not None,
            self.pressure_margin is not None,
            self.optimal_holding_pressure is not None,
            self.gate_freeze_time is not None,
            self.recommended_cooling_time is not None,
            self.recommended_clamping_force is not None,
        ])
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current workflow progress."""
        return {
            "step0_completed": self.machine_snapshot is not None,
            "current_step": self.current_step,
            "step1_completed": self.optimal_injection_speed is not None,
            "step2_completed": self.cavity_balance_ratio is not None,
            "step3_completed": self.pressure_margin is not None,
            "step4_completed": self.optimal_holding_pressure is not None,
            "step5_completed": self.gate_freeze_time is not None,
            "step6_completed": self.recommended_cooling_time is not None,
            "step7_completed": self.recommended_clamping_force is not None,
            "optimal_speed": self.optimal_injection_speed,
            "optimal_pressure": self.optimal_holding_pressure,
            "gate_freeze_time": self.gate_freeze_time,
            "cooling_time": self.recommended_cooling_time,
            "clamping_force": self.recommended_clamping_force,
            "step_remarks": self.step_remarks,
            "step_data_quality": self.step_data_quality,
        }


# Global singleton instance
_session_state = SevenStepSessionState()


def get_session_state() -> SevenStepSessionState:
    """Get the global session state instance."""
    return _session_state


def reset_session_state():
    """Reset the global session state."""
    global _session_state
    _session_state = SevenStepSessionState()
