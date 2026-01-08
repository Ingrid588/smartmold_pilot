"""
SmartMold Pilot V3 - Core Algorithms
Implements domain-specific calculations for Scientific Molding and Machine Performance.
"""

from typing import List, Tuple, Optional, Dict, Any
import math
from dataclasses import dataclass


# ============================================================
# Data Structures
# ============================================================

@dataclass
class ViscosityPoint:
    """Single viscosity measurement point."""
    fill_speed_percent: float
    fill_speed_mm_s: float
    fill_time: float
    peak_pressure: float
    shear_rate: Optional[float] = None
    viscosity: Optional[float] = None


@dataclass
class BalanceMetrics:
    """Cavity balance analysis result."""
    max_weight: float
    min_weight: float
    avg_weight: float
    imbalance_percent: float
    status: str  # "pass" or "fail"
    threshold: float


@dataclass
class PressureWindowResult:
    """Pressure process window analysis."""
    min_optimal_pressure: Optional[float]
    max_optimal_pressure: Optional[float]
    recommended_pressure: Optional[float]
    status: str  # "insufficient_data", "found", "failed"


@dataclass
class WeightRepeatabilityResult:
    """Injection weight repeatability analysis."""
    max_weight: float
    min_weight: float
    avg_weight: float
    repeatability_percent: float
    threshold: float
    status: str  # "pass" or "fail"


@dataclass
class SpeedLinearityResult:
    """Injection speed linearity analysis."""
    slope: float
    intercept: float
    r_squared: float
    status: str  # "excellent", "good", "poor", "insufficient_data"


# ============================================================
# Viscosity Curve Calculations
# ============================================================

def calculate_shear_rate(
    fill_speed_mm_s: float,
    screw_diameter: float
) -> float:
    """
    Calculate shear rate using simplified formula.
    
    Shear Rate (1/s) ≈ (Fill Speed in mm/s) / (Screw Diameter / 2)
    
    Args:
        fill_speed_mm_s: Fill speed in mm/s
        screw_diameter: Screw diameter in mm
        
    Returns:
        Shear rate in 1/s
    """
    if screw_diameter <= 0:
        raise ValueError("Screw diameter must be positive")
    
    shear_rate = fill_speed_mm_s / (screw_diameter / 2)
    return shear_rate


def calculate_viscosity(
    peak_pressure: float,
    fill_time: float
) -> float:
    """
    Calculate effective viscosity (simplified).
    
    Viscosity ≈ Peak Pressure × Fill Time
    (This is a simplified model; actual viscosity calculation may need refinement)
    
    Args:
        peak_pressure: Peak pressure in Bar/MPa
        fill_time: Fill time in seconds
        
    Returns:
        Effective viscosity
    """
    if fill_time <= 0:
        raise ValueError("Fill time must be positive")
    
    viscosity = peak_pressure * fill_time
    return viscosity


def process_viscosity_data(
    data_points: List[ViscosityPoint],
    screw_diameter: float
) -> List[Dict]:
    """
    Process multiple viscosity measurements and compute derived fields.
    
    Args:
        data_points: List of ViscosityPoint objects
        screw_diameter: Screw diameter in mm
        
    Returns:
        List of dicts with shear_rate and viscosity computed
    """
    results = []
    
    for point in data_points:
        shear_rate = calculate_shear_rate(point.fill_speed_mm_s, screw_diameter)
        viscosity = calculate_viscosity(point.peak_pressure, point.fill_time)
        
        results.append({
            "fill_speed_percent": point.fill_speed_percent,
            "fill_speed_mm_s": point.fill_speed_mm_s,
            "fill_time": point.fill_time,
            "peak_pressure": point.peak_pressure,
            "shear_rate": shear_rate,
            "viscosity": viscosity,
        })
    
    return results


# ============================================================
# Cavity Balance Calculations
# ============================================================

def calculate_cavity_balance(
    weights: List[float],
    imbalance_threshold: float = 5.0
) -> BalanceMetrics:
    """
    Analyze multi-cavity balance based on product weights.
    
    Imbalance % = (Max Weight - Min Weight) / Average Weight × 100
    Status: "pass" if Imbalance % <= threshold, else "fail"
    
    Args:
        weights: List of cavity weights (e.g., [weight_1, weight_2, ...])
        imbalance_threshold: Acceptable threshold in % (default 5%)
        
    Returns:
        BalanceMetrics object
    """
    if not weights or len(weights) == 0:
        raise ValueError("Weights list cannot be empty")
    
    max_weight = max(weights)
    min_weight = min(weights)
    avg_weight = sum(weights) / len(weights)
    
    if avg_weight == 0:
        raise ValueError("Average weight cannot be zero")
    
    imbalance_percent = ((max_weight - min_weight) / avg_weight) * 100
    status = "pass" if imbalance_percent <= imbalance_threshold else "fail"
    
    return BalanceMetrics(
        max_weight=max_weight,
        min_weight=min_weight,
        avg_weight=avg_weight,
        imbalance_percent=imbalance_percent,
        status=status,
        threshold=imbalance_threshold,
    )


# ============================================================
# Pressure Process Window Calculations
# ============================================================

def find_pressure_window(
    pressure_data: List[Tuple[float, str]]
) -> PressureWindowResult:
    """
    Identify optimal pressure window from test data.
    
    Logic: Find the lowest and highest pressure where appearance is "ok".
    The midpoint is the recommended pressure.
    
    Args:
        pressure_data: List of tuples (pressure, appearance_status)
                      where appearance_status in ["ok", "flash", "short", "incomplete"]
    
    Returns:
        PressureWindowResult object
    """
    ok_pressures = [p for p, status in pressure_data if status == "ok"]
    
    if not ok_pressures:
        return PressureWindowResult(
            min_optimal_pressure=None,
            max_optimal_pressure=None,
            recommended_pressure=None,
            status="failed",
        )
    
    min_optimal = min(ok_pressures)
    max_optimal = max(ok_pressures)
    recommended = (min_optimal + max_optimal) / 2
    
    return PressureWindowResult(
        min_optimal_pressure=min_optimal,
        max_optimal_pressure=max_optimal,
        recommended_pressure=recommended,
        status="found",
    )


# ============================================================
# Gate Freezing Time Calculation
# ============================================================

def find_gate_freeze_time(
    holding_time_weight_data: List[Tuple[float, float]],
    weight_plateau_threshold: float = 0.5
) -> Optional[float]:
    """
    Identify gate freeze time from weight vs holding time curve.
    
    Gate freeze time is when product weight plateaus (stops increasing).
    
    Args:
        holding_time_weight_data: List of (holding_time_sec, weight_g) tuples
        weight_plateau_threshold: If weight increment < this, consider plateau
        
    Returns:
        Estimated gate freeze time, or None if insufficient data
    """
    if len(holding_time_weight_data) < 2:
        return None
    
    # Sort by holding time
    data_sorted = sorted(holding_time_weight_data, key=lambda x: x[0])
    
    # Check for weight plateau
    for i in range(1, len(data_sorted)):
        prev_time, prev_weight = data_sorted[i - 1]
        curr_time, curr_weight = data_sorted[i]
        
        weight_increment = curr_weight - prev_weight
        
        if weight_increment < weight_plateau_threshold:
            # Weight has plateaued
            return prev_time
    
    # No clear plateau found
    return None


# ============================================================
# Machine Performance: Weight Repeatability
# ============================================================

def calculate_weight_repeatability(
    weights: List[float],
    threshold_percent: float = 1.0
) -> WeightRepeatabilityResult:
    """
    Analyze injection weight repeatability across consecutive shots.
    
    Repeatability % = (Max Weight - Min Weight) / Average Weight × 100
    Status: "pass" if <= threshold, else "fail"
    
    Args:
        weights: List of 5 consecutive shot weights
        threshold_percent: Acceptable threshold (default 1%)
        
    Returns:
        WeightRepeatabilityResult object
    """
    if not weights or len(weights) == 0:
        raise ValueError("Weights list cannot be empty")
    
    max_weight = max(weights)
    min_weight = min(weights)
    avg_weight = sum(weights) / len(weights)
    
    if avg_weight == 0:
        raise ValueError("Average weight cannot be zero")
    
    repeatability_percent = ((max_weight - min_weight) / avg_weight) * 100
    status = "pass" if repeatability_percent <= threshold_percent else "fail"
    
    return WeightRepeatabilityResult(
        max_weight=max_weight,
        min_weight=min_weight,
        avg_weight=avg_weight,
        repeatability_percent=repeatability_percent,
        threshold=threshold_percent,
        status=status,
    )


# ============================================================
# Machine Performance: Speed Linearity
# ============================================================

def linear_regression(
    x_values: List[float],
    y_values: List[float]
) -> Tuple[float, float, float]:
    """
    Perform simple linear regression: y = slope * x + intercept.
    Returns (slope, intercept, r_squared).
    """
    if len(x_values) < 2 or len(x_values) != len(y_values):
        raise ValueError("x and y must have at least 2 points and same length")
    
    n = len(x_values)
    
    # Calculate means
    x_mean = sum(x_values) / n
    y_mean = sum(y_values) / n
    
    # Calculate slope and intercept
    numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
    denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        raise ValueError("Cannot compute regression: all x values are identical")
    
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    
    # Calculate R²
    ss_res = sum((y_values[i] - (slope * x_values[i] + intercept)) ** 2 for i in range(n))
    ss_tot = sum((y_values[i] - y_mean) ** 2 for i in range(n))
    
    if ss_tot == 0:
        r_squared = 0.0
    else:
        r_squared = 1 - (ss_res / ss_tot)
    
    return slope, intercept, r_squared


def calculate_speed_linearity(
    set_speed_percent: List[float],
    actual_speed_mm_s: List[float]
) -> SpeedLinearityResult:
    """
    Analyze injection speed linearity using linear regression.
    
    Args:
        set_speed_percent: Set speed values (%)
        actual_speed_mm_s: Actual speed values (mm/s)
        
    Returns:
        SpeedLinearityResult with R² and status
    """
    if len(set_speed_percent) < 2:
        return SpeedLinearityResult(
            slope=0,
            intercept=0,
            r_squared=0,
            status="insufficient_data",
        )
    
    slope, intercept, r_squared = linear_regression(set_speed_percent, actual_speed_mm_s)
    
    # Determine status based on R²
    if r_squared > 0.98:
        status = "excellent"
    elif r_squared > 0.95:
        status = "good"
    else:
        status = "poor"
    
    return SpeedLinearityResult(
        slope=slope,
        intercept=intercept,
        r_squared=r_squared,
        status=status,
    )


# ============================================================
# Check Ring (止逆环) Leakage Analysis
# ============================================================

def analyze_check_ring_leakage(
    leakage_volumes: List[float],
    test_type: str = "dynamic"
) -> Dict:
    """
    Analyze check ring leakage data (dynamic or static).
    
    Args:
        leakage_volumes: List of leakage volumes across cycles
        test_type: "dynamic" or "static"
        
    Returns:
        Dict with avg_leakage, trend, status
    """
    if not leakage_volumes:
        return {
            "avg_leakage": 0,
            "max_leakage": 0,
            "min_leakage": 0,
            "trend": "unknown",
            "status": "insufficient_data",
        }
    
    avg_leakage = sum(leakage_volumes) / len(leakage_volumes)
    max_leakage = max(leakage_volumes)
    min_leakage = min(leakage_volumes)
    
    # Determine trend
    trend = "stable"
    if len(leakage_volumes) > 1:
        first_half_avg = sum(leakage_volumes[:len(leakage_volumes)//2]) / (len(leakage_volumes)//2 + 1)
        second_half_avg = sum(leakage_volumes[len(leakage_volumes)//2:]) / (len(leakage_volumes) - len(leakage_volumes)//2)
        
        if second_half_avg > first_half_avg * 1.1:
            trend = "increasing"
        elif second_half_avg < first_half_avg * 0.9:
            trend = "decreasing"
    
    # Status
    status = "normal" if avg_leakage < 5 else "warning"  # Threshold example: < 5 ml is normal
    
    return {
        "avg_leakage": round(avg_leakage, 2),
        "max_leakage": max_leakage,
        "min_leakage": min_leakage,
        "trend": trend,
        "status": status,
    }


# ============================================================
# Utility Functions
# ============================================================

def format_number(value: float, decimal_places: int = 2) -> float:
    """Format a number to specified decimal places."""
    return round(value, decimal_places)

# ============================================================
# Additional Required Functions
# ============================================================

def cavity_balance(pressures: List[float]) -> float:
    """
    Calculate cavity balance percentage.
    
    Args:
        pressures: List of cavity pressure values (MPa)
        
    Returns:
        Balance percentage (0-1, where 1 is perfect balance)
    """
    if not pressures or len(pressures) < 2:
        return 0.0
    
    pressures = list(map(float, pressures))
    max_pressure = max(pressures)
    min_pressure = min(pressures)
    
    if max_pressure == 0:
        return 1.0
    
    # Balance = 1 - (max - min) / max
    imbalance = (max_pressure - min_pressure) / max_pressure
    balance = 1.0 - imbalance
    
    return max(0.0, min(1.0, balance))


def speed_linearity_index(speeds: List[float]) -> float:
    """
    Calculate speed linearity index.
    
    Args:
        speeds: List of speed measurements
        
    Returns:
        Linearity index as percentage (0-100)
    """
    if not speeds or len(speeds) < 2:
        return 0.0
    
    speeds = list(map(float, speeds))
    
    # Simple linearity calculation based on coefficient of variation
    mean_speed = sum(speeds) / len(speeds)
    if mean_speed == 0:
        return 0.0
    
    variance = sum((s - mean_speed) ** 2 for s in speeds) / len(speeds)
    std_dev = variance ** 0.5
    cv = (std_dev / mean_speed) * 100  # Coefficient of variation
    
    # Convert CV to linearity index (lower CV = higher linearity)
    linearity = max(0.0, 100.0 - cv)
    
    return min(100.0, linearity)


def linear_regression(
    x_values: List[float],
    y_values: List[float]
) -> Tuple[float, float, float]:
    """
    Calculate linear regression (slope, intercept, R²).
    
    Args:
        x_values: Independent variable values
        y_values: Dependent variable values
        
    Returns:
        Tuple of (slope, intercept, r_squared)
    """
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return 0.0, 0.0, 0.0
    
    n = len(x_values)
    x_mean = sum(x_values) / n
    y_mean = sum(y_values) / n
    
    numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
    denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return 0.0, y_mean, 0.0
    
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    
    # Calculate R²
    ss_res = sum((y_values[i] - (slope * x_values[i] + intercept)) ** 2 for i in range(n))
    ss_tot = sum((y_values[i] - y_mean) ** 2 for i in range(n))
    
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    return slope, intercept, r_squared


# ============================================================
# Six-Step Scientific Molding Algorithms
# ============================================================

def find_viscosity_inflection_point(speeds: List[float], viscosities: List[float]) -> Dict[str, float]:
    """
    Find the inflection point in viscosity curve (shear thinning knee).
    
    Algorithm:
    1. Calculate first derivative (slope between points)
    2. Find where slope flattens (second derivative approaches zero)
    3. Return the speed at inflection point
    
    Args:
        speeds: List of injection speeds (mm/s)
        viscosities: List of corresponding viscosity values
    
    Returns:
        Dict with 'optimal_speed', 'viscosity_at_optimal', 'inflection_index'
    """
    if len(speeds) < 3 or len(speeds) != len(viscosities):
        return {"optimal_speed": speeds[len(speeds)//2] if speeds else 50.0, 
                "viscosity_at_optimal": 0.0, 
                "inflection_index": 0}
    
    # Calculate first derivatives
    slopes = []
    for i in range(len(speeds) - 1):
        slope = (viscosities[i+1] - viscosities[i]) / (speeds[i+1] - speeds[i])
        slopes.append(slope)
    
    # Find where slope magnitude is minimal (flattest region)
    min_slope_idx = 0
    min_slope = abs(slopes[0])
    
    for i in range(1, len(slopes)):
        if abs(slopes[i]) < min_slope:
            min_slope = abs(slopes[i])
            min_slope_idx = i
    
    # Inflection point is at min_slope_idx + 1
    inflection_idx = min_slope_idx + 1
    optimal_speed = speeds[inflection_idx]
    viscosity_at_optimal = viscosities[inflection_idx]
    
    return {
        "optimal_speed": optimal_speed,
        "viscosity_at_optimal": viscosity_at_optimal,
        "inflection_index": inflection_idx,
        "curve_slope_at_optimal": slopes[min_slope_idx]
    }


def calculate_viscosity_fingerprint(pressure_curve: List[float], time_curve: List[float]) -> float:
    """
    Calculate viscosity fingerprint (pressure integral over time).
    Used to detect PCR material batch variations.
    
    Fingerprint = ∫ P(t) dt (area under pressure curve)
    
    Args:
        pressure_curve: List of pressure values
        time_curve: List of corresponding time values
    
    Returns:
        Fingerprint value (pressure integral)
    """
    if len(pressure_curve) != len(time_curve) or len(pressure_curve) < 2:
        return 0.0
    
    # Trapezoidal integration
    integral = 0.0
    for i in range(len(pressure_curve) - 1):
        dt = time_curve[i+1] - time_curve[i]
        avg_pressure = (pressure_curve[i] + pressure_curve[i+1]) / 2
        integral += avg_pressure * dt
    
    return integral


def detect_gate_freeze_time(holding_times: List[float], weights: List[float]) -> Dict[str, Any]:
    """
    Detect gate freeze time from weight vs holding time curve.
    
    Algorithm:
    1. Calculate dW/dT (weight derivative)
    2. Find where dW/dT ≈ 0 (weight plateau)
    3. Add 2s safety margin
    
    Args:
        holding_times: List of holding times (seconds)
        weights: List of corresponding part weights (grams)
    
    Returns:
        Dict with 'freeze_time', 'recommended_time', 'plateau_detected'
    """
    if len(holding_times) < 3 or len(holding_times) != len(weights):
        return {"freeze_time": None, "recommended_time": None, "plateau_detected": False}
    
    # Calculate derivatives
    derivatives = []
    for i in range(len(holding_times) - 1):
        dt = holding_times[i+1] - holding_times[i]
        dw = weights[i+1] - weights[i]
        derivatives.append(dw / dt if dt != 0 else 0.0)
    
    # Find where derivative approaches zero (threshold: < 0.01 g/s)
    threshold = 0.01
    freeze_idx = None
    
    for i in range(len(derivatives)):
        if abs(derivatives[i]) < threshold:
            freeze_idx = i + 1  # Freeze at this time index
            break
    
    if freeze_idx is None:
        return {"freeze_time": None, "recommended_time": None, "plateau_detected": False}
    
    freeze_time = holding_times[freeze_idx]
    recommended_time = freeze_time + 2.0  # Add 2s safety margin
    
    return {
        "freeze_time": freeze_time,
        "recommended_time": recommended_time,
        "plateau_detected": True,
        "weight_at_freeze": weights[freeze_idx]
    }


def calculate_pressure_margin(max_machine_pressure: float, peak_injection_pressure: float) -> Dict[str, Any]:
    """
    Calculate pressure drop/margin and check if pressure-limited.
    
    Args:
        max_machine_pressure: Machine max pressure limit (MPa)
        peak_injection_pressure: Actual peak pressure during fill (MPa)
    
    Returns:
        Dict with 'margin', 'is_limited', 'utilization_percent'
    """
    margin = max_machine_pressure - peak_injection_pressure
    utilization = (peak_injection_pressure / max_machine_pressure) * 100
    is_limited = peak_injection_pressure > (0.9 * max_machine_pressure)
    
    return {
        "margin": margin,
        "is_limited": is_limited,
        "utilization_percent": utilization,
        "status": "PRESSURE LIMITED" if is_limited else "OK"
    }


def find_process_window_center(
    test_points: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Find the center of the process window (O-Window).
    
    Algorithm:
    1. Filter points with 'ok' appearance
    2. Calculate geometric centroid
    3. Return recommended setpoint
    
    Args:
        test_points: List of dicts with keys:
            - 'holding_pressure': float
            - 'temperature': float (or other X-axis param)
            - 'appearance_status': str ('ok', 'flash', 'short')
    
    Returns:
        Dict with 'center_pressure', 'center_temperature', 'window_size', 'status'
    """
    ok_points = [p for p in test_points if p.get('appearance_status') == 'ok']
    
    if len(ok_points) < 2:
        return {
            "center_pressure": None,
            "center_temperature": None,
            "window_size": 0,
            "status": "insufficient_data"
        }
    
    # Calculate centroid
    avg_pressure = sum(p['holding_pressure'] for p in ok_points) / len(ok_points)
    avg_temp = sum(p.get('temperature', 0) for p in ok_points) / len(ok_points)
    
    # Calculate window size (range)
    pressures = [p['holding_pressure'] for p in ok_points]
    window_size = max(pressures) - min(pressures)
    
    return {
        "center_pressure": avg_pressure,
        "center_temperature": avg_temp,
        "window_size": window_size,
        "min_pressure": min(pressures),
        "max_pressure": max(pressures),
        "status": "found"
    }

