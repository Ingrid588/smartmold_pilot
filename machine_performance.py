"""
Machine Performance Module - Weight Repeatability & Speed Linearity Analysis
Advanced features for machine performance validation and testing.
"""

import json
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np
import plotly.graph_objects as go
from algorithms import calculate_weight_repeatability, linear_regression, speed_linearity_index


# ============================================================
# Machine Performance Test Functions
# ============================================================

def run_weight_repeatability_test(
    sample_count: int = 30,
    target_weight: float = 10.0,
    weights: List[float] = None
) -> Dict:
    """
    Run weight repeatability test.
    
    Args:
        sample_count: Number of samples to test
        target_weight: Target weight for each sample
        weights: Actual weights (if None, uses demo data)
    
    Returns:
        Test results dictionary
    """
    if weights is None:
        # Demo data: normally distributed around target with small variance
        np.random.seed(42)
        weights = list(np.random.normal(target_weight, 0.05, sample_count))
    
    repeatability = calculate_weight_repeatability(weights, target_weight)
    
    # Pass/Fail criteria
    pass_threshold = 0.98  # 98%
    status = "PASS" if repeatability >= pass_threshold else "FAIL"
    
    # Statistics
    mean_weight = np.mean(weights)
    std_dev = np.std(weights)
    variance = np.var(weights)
    
    return {
        "test_type": "Weight Repeatability",
        "status": status,
        "repeatability_percentage": repeatability * 100,
        "pass_threshold": pass_threshold * 100,
        "sample_count": sample_count,
        "target_weight": target_weight,
        "mean_weight": mean_weight,
        "std_dev": std_dev,
        "variance": variance,
        "min_weight": np.min(weights),
        "max_weight": np.max(weights),
        "weight_range": np.max(weights) - np.min(weights),
        "weights": weights,
        "timestamp": datetime.now().isoformat()
    }


def run_speed_linearity_test(
    speed_levels: List[float] = None,
    actual_speeds: List[float] = None
) -> Dict:
    """
    Run speed linearity test.
    
    Args:
        speed_levels: Commanded speed levels (%)
        actual_speeds: Actual measured speeds (mm/s)
    
    Returns:
        Test results dictionary
    """
    if speed_levels is None:
        speed_levels = [20, 30, 40, 50, 60, 70, 80, 90, 100]
    
    if actual_speeds is None:
        # Demo data: actual speeds close to theoretical (20% linear)
        np.random.seed(123)
        theoretical_speeds = [level * 2 for level in speed_levels]  # Max 200 mm/s at 100%
        actual_speeds = [spd + np.random.normal(0, 2) for spd in theoretical_speeds]
    
    # Linear regression
    slope, intercept, r_squared = linear_regression(
        np.array(speed_levels),
        np.array(actual_speeds)
    )
    
    linearity = speed_linearity_index(actual_speeds)
    
    # Pass/Fail criteria
    pass_threshold = 0.95  # R² >= 0.95
    status = "PASS" if r_squared >= pass_threshold else "FAIL"
    
    return {
        "test_type": "Speed Linearity",
        "status": status,
        "linearity_index": linearity,
        "r_squared": r_squared,
        "pass_threshold": pass_threshold,
        "slope": slope,
        "intercept": intercept,
        "speed_levels": speed_levels,
        "actual_speeds": actual_speeds,
        "theoretical_speeds": [level * 2 for level in speed_levels],
        "timestamp": datetime.now().isoformat()
    }


def run_pressure_consistency_test(
    measurements: List[float] = None,
    target_pressure: float = 50.0
) -> Dict:
    """
    Run pressure consistency test across multiple cycles.
    
    Args:
        measurements: Pressure measurements (MPa)
        target_pressure: Target pressure value
    
    Returns:
        Test results dictionary
    """
    if measurements is None:
        # Demo data: 20 cycles with small variation
        np.random.seed(456)
        measurements = list(np.random.normal(target_pressure, 2.0, 20))
    
    consistency = calculate_weight_repeatability(measurements, target_pressure)
    
    # Pass/Fail
    pass_threshold = 0.95
    status = "PASS" if consistency >= pass_threshold else "FAIL"
    
    return {
        "test_type": "Pressure Consistency",
        "status": status,
        "consistency_percentage": consistency * 100,
        "pass_threshold": pass_threshold * 100,
        "cycle_count": len(measurements),
        "target_pressure": target_pressure,
        "mean_pressure": np.mean(measurements),
        "std_dev": np.std(measurements),
        "min_pressure": np.min(measurements),
        "max_pressure": np.max(measurements),
        "measurements": measurements,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================
# Chart Generation Functions
# ============================================================

def generate_weight_trend_chart(weights: List[float], target: float) -> str:
    """Generate weight trend line chart."""
    cycles = list(range(1, len(weights) + 1))
    
    fig = go.Figure()
    
    # Weight data
    fig.add_trace(go.Scatter(
        x=cycles,
        y=weights,
        mode='lines+markers',
        name='实际体重',
        line=dict(color='#4CAF50', width=2),
        marker=dict(size=6)
    ))
    
    # Target line
    fig.add_hline(
        y=target,
        line_dash="dash",
        line_color="red",
        annotation_text=f"目标: {target}g"
    )
    
    # Upper/Lower control limits (±3%)
    ucl = target * 1.03
    lcl = target * 0.97
    
    fig.add_hline(y=ucl, line_dash="dot", line_color="orange", 
                  annotation_text="UCL (+3%)")
    fig.add_hline(y=lcl, line_dash="dot", line_color="orange",
                  annotation_text="LCL (-3%)")
    
    fig.update_layout(
        title="体重趋势分析",
        xaxis_title="周期数",
        yaxis_title="体重 (g)",
        height=400,
        template="plotly_dark",
        hovermode='x unified',
        font=dict(family="Arial, sans-serif", size=12, color="#f5f7fa"),
        paper_bgcolor="rgba(30, 30, 46, 0.8)",
        plot_bgcolor="rgba(40, 40, 60, 0.8)"
    )
    
    return fig.to_html(include_plotlyjs='cdn', div_id='weight_trend_chart')


def generate_speed_linearity_chart(
    speed_levels: List[float],
    actual_speeds: List[float],
    theoretical_speeds: List[float]
) -> str:
    """Generate speed linearity comparison chart."""
    
    fig = go.Figure()
    
    # Actual speeds
    fig.add_trace(go.Scatter(
        x=speed_levels,
        y=actual_speeds,
        mode='lines+markers',
        name='实际速度',
        line=dict(color='#2196F3', width=2),
        marker=dict(size=8)
    ))
    
    # Theoretical speeds
    fig.add_trace(go.Scatter(
        x=speed_levels,
        y=theoretical_speeds,
        mode='lines',
        name='理论速度',
        line=dict(color='#FF9800', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title="速度线性性分析",
        xaxis_title="指令速度 (%)",
        yaxis_title="速度 (mm/s)",
        height=400,
        template="plotly_dark",
        hovermode='x unified',
        font=dict(family="Arial, sans-serif", size=12, color="#f5f7fa"),
        paper_bgcolor="rgba(30, 30, 46, 0.8)",
        plot_bgcolor="rgba(40, 40, 60, 0.8)",
        legend=dict(x=0.02, y=0.98)
    )
    
    return fig.to_html(include_plotlyjs='cdn', div_id='speed_linearity_chart')


def generate_pressure_distribution_chart(
    measurements: List[float],
    target: float
) -> str:
    """Generate pressure distribution histogram."""
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=measurements,
        nbinsx=15,
        name='压力测量值',
        marker=dict(color='rgba(76, 175, 80, 0.7)', line=dict(color='#4CAF50', width=1))
    ))
    
    # Target line
    fig.add_vline(
        x=target,
        line_dash="dash",
        line_color="red",
        annotation_text=f"目标: {target} MPa"
    )
    
    fig.update_layout(
        title="压力分布分析",
        xaxis_title="压力 (MPa)",
        yaxis_title="出现次数",
        height=400,
        template="plotly_dark",
        font=dict(family="Arial, sans-serif", size=12, color="#f5f7fa"),
        paper_bgcolor="rgba(30, 30, 46, 0.8)",
        plot_bgcolor="rgba(40, 40, 60, 0.8)",
        showlegend=False
    )
    
    return fig.to_html(include_plotlyjs='cdn', div_id='pressure_distribution_chart')


def generate_test_summary_chart(test_results: Dict) -> str:
    """Generate test summary dashboard."""
    
    tests = []
    passed = []
    
    if isinstance(test_results, dict):
        if "status" in test_results:
            tests = [test_results]
        else:
            # Multiple tests
            tests = list(test_results.values())
    elif isinstance(test_results, list):
        tests = test_results
    
    test_names = [t.get("test_type", "Unknown") for t in tests]
    pass_counts = [1 if t.get("status") == "PASS" else 0 for t in tests]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=test_names,
        y=pass_counts,
        marker=dict(
            color=['#4CAF50' if p == 1 else '#F44336' for p in pass_counts]
        ),
        text=['PASS' if p == 1 else 'FAIL' for p in pass_counts],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="机台性能测试结果",
        yaxis=dict(title="通过状态", tickvals=[0, 1], ticktext=['FAIL', 'PASS']),
        height=300,
        template="plotly_dark",
        font=dict(family="Arial, sans-serif", size=12, color="#f5f7fa"),
        paper_bgcolor="rgba(30, 30, 46, 0.8)",
        plot_bgcolor="rgba(40, 40, 60, 0.8)",
        showlegend=False
    )
    
    return fig.to_html(include_plotlyjs='cdn', div_id='test_summary_chart')


# ============================================================
# Report Generation
# ============================================================

def generate_test_report(test_results: Dict) -> str:
    """
    Generate HTML test report.
    
    Args:
        test_results: Test results dictionary
    
    Returns:
        HTML report string
    """
    timestamp = test_results.get('timestamp', datetime.now().isoformat())
    test_type = test_results.get('test_type', 'Unknown')
    status = test_results.get('status', 'UNKNOWN')
    
    status_color = "#4CAF50" if status == "PASS" else "#F44336"
    status_icon = "✓" if status == "PASS" else "✗"
    
    html = f"""
    <div style="background: rgba(30, 30, 46, 0.9); padding: 20px; border-radius: 12px; 
                border: 1px solid rgba(255,255,255,0.1); color: #f5f7fa;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h2 style="margin: 0; color: #f5f7fa;">{test_type}</h2>
            <div style="font-size: 24px; color: {status_color}; font-weight: bold;">
                {status_icon} {status}
            </div>
        </div>
        
        <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p style="margin: 5px 0;"><strong>测试时间:</strong> {timestamp}</p>
    """
    
    # Add test-specific details
    for key, value in test_results.items():
        if key not in ['timestamp', 'test_type', 'status', 'weights', 'measurements', 'actual_speeds', 
                       'theoretical_speeds', 'speed_levels']:
            if isinstance(value, float):
                html += f"<p style=\"margin: 5px 0;\"><strong>{key}:</strong> {value:.4f}</p>"
            elif isinstance(value, (int, str)):
                html += f"<p style=\"margin: 5px 0;\"><strong>{key}:</strong> {value}</p>"
    
    html += """
        </div>
    </div>
    """
    
    return html


# ============================================================
# Test History Management
# ============================================================

class MachineTestHistory:
    """Manage machine performance test history."""
    
    def __init__(self, storage_file: str = "machine_test_history.json"):
        self.storage_file = storage_file
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """Load history from storage."""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_history(self):
        """Save history to storage."""
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
    
    def add_test_result(
        self,
        test_type: str,
        status: str,
        results: Dict[str, any]
    ):
        """Add a test result."""
        record = {
            "id": len(self.history) + 1,
            "timestamp": datetime.now().isoformat(),
            "test_type": test_type,
            "status": status,
            "results": results
        }
        self.history.append(record)
        self._save_history()
        return record
    
    def get_recent_tests(self, limit: int = 10) -> List[Dict]:
        """Get recent test results."""
        return sorted(self.history, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_tests_by_type(self, test_type: str) -> List[Dict]:
        """Get tests by type."""
        return [r for r in self.history if r['test_type'] == test_type]
    
    def get_pass_rate(self, test_type: str = None) -> float:
        """Calculate pass rate."""
        if test_type:
            records = self.get_tests_by_type(test_type)
        else:
            records = self.history
        
        if not records:
            return 0.0
        
        passed = sum(1 for r in records if r.get('status') == 'PASS')
        return (passed / len(records)) * 100
