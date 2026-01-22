"""
Scientific Molding Advanced Module - Charts, Data Export, History Management
Enhanced functionality for scientific molding analysis with Plotly integration.
"""

import json
import csv
import io
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from algorithms import calculate_viscosity, cavity_balance, calculate_weight_repeatability


# ============================================================
# Chart Generation Functions
# ============================================================

def generate_viscosity_chart(temperatures: List[float], shear_rates: List[float]) -> str:
    """
    Generate viscosity vs. shear rate curve.
    
    Args:
        temperatures: List of temperature values (°C)
        shear_rates: List of shear rate values (s⁻¹)
    
    Returns:
        HTML string for Plotly chart
    """
    if not temperatures or not shear_rates:
        temperatures = [220, 230, 240, 250, 260]
        shear_rates = [0.5, 1.0, 2.0, 5.0, 10.0]
    
    # Calculate viscosity for each combination
    viscosities = []
    for temp in temperatures:
        row = [calculate_viscosity(temp, sr) for sr in shear_rates]
        viscosities.append(row)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=viscosities,
        x=shear_rates,
        y=temperatures,
        colorscale='Viridis',
        colorbar=dict(title="粘度<br>(Pa·s)")
    ))
    
    fig.update_layout(
        title="粘度 - 剪切速率曲线分析",
        xaxis_title="剪切速率 (s⁻¹)",
        yaxis_title="温度 (°C)",
        height=400,
        template="plotly_dark",
        font=dict(family="Arial, sans-serif", size=12, color="#f5f7fa"),
        paper_bgcolor="rgba(30, 30, 46, 0.8)",
        plot_bgcolor="rgba(40, 40, 60, 0.8)"
    )
    
    return fig.to_html(include_plotlyjs='cdn', div_id='viscosity_chart')


def generate_cavity_balance_chart(pressures: List[float]) -> str:
    """
    Generate cavity pressure distribution chart.
    
    Args:
        pressures: List of cavity pressure values (MPa)
    
    Returns:
        HTML string for Plotly chart
    """
    if not pressures:
        pressures = [52, 54, 51, 55, 53, 52, 54, 51]
    
    cavity_nums = [f"腔{i+1}" for i in range(len(pressures))]
    balance_pct = cavity_balance(pressures) * 100
    avg_pressure = np.mean(pressures)
    
    # Create bar chart
    fig = go.Figure(data=go.Bar(
        x=cavity_nums,
        y=pressures,
        marker=dict(
            color=pressures,
            colorscale='RdYlGn',
            colorbar=dict(title="压力(MPa)")
        ),
        text=[f"{p:.1f}" for p in pressures],
        textposition="outside"
    ))
    
    # Add average line
    fig.add_hline(
        y=avg_pressure,
        line_dash="dash",
        line_color="cyan",
        annotation_text=f"平均: {avg_pressure:.1f} MPa",
        annotation_position="right"
    )
    
    fig.update_layout(
        title=f"型腔压力分布 (平衡度: {balance_pct:.1f}%)",
        xaxis_title="型腔编号",
        yaxis_title="压力 (MPa)",
        height=400,
        showlegend=False,
        template="plotly_dark",
        font=dict(family="Arial, sans-serif", size=12, color="#f5f7fa"),
        paper_bgcolor="rgba(30, 30, 46, 0.8)",
        plot_bgcolor="rgba(40, 40, 60, 0.8)"
    )
    
    return fig.to_html(include_plotlyjs='cdn', div_id='cavity_chart')


def generate_weight_repeatability_chart(weights: List[float], target: float) -> str:
    """
    Generate weight distribution histogram.
    
    Args:
        weights: List of sample weight values (g)
        target: Target weight (g)
    
    Returns:
        HTML string for Plotly chart
    """
    if not weights:
        weights = [10.1, 10.0, 9.9, 10.05, 9.95, 10.02, 9.98, 10.03]
        target = 10.0
    
    repeatability = calculate_weight_repeatability(weights, target)
    
    # Create histogram
    fig = go.Figure(data=go.Histogram(
        x=weights,
        nbinsx=15,
        marker=dict(color='rgba(76, 175, 80, 0.7)', line=dict(color='#4CAF50', width=1))
    ))
    
    # Add target line
    fig.add_vline(
        x=target,
        line_dash="dash",
        line_color="red",
        annotation_text=f"目标: {target}g",
        annotation_position="top right"
    )
    
    fig.update_layout(
        title=f"体重分布 (重复性: {repeatability*100:.1f}%)",
        xaxis_title="体重 (g)",
        yaxis_title="样本数",
        height=400,
        showlegend=False,
        template="plotly_dark",
        font=dict(family="Arial, sans-serif", size=12, color="#f5f7fa"),
        paper_bgcolor="rgba(30, 30, 46, 0.8)",
        plot_bgcolor="rgba(40, 40, 60, 0.8)"
    )
    
    return fig.to_html(include_plotlyjs='cdn', div_id='weight_chart')


def generate_process_window_chart(
    p_min: float, p_max: float,
    t_min: float, t_max: float,
    current_p: float = None,
    current_t: float = None
) -> str:
    """
    Generate 2D process window chart (Pressure vs Temperature).
    
    Args:
        p_min, p_max: Pressure range (MPa)
        t_min, t_max: Temperature range (°C)
        current_p: Current pressure (optional)
        current_t: Current temperature (optional)
    
    Returns:
        HTML string for Plotly chart
    """
    # Create rectangle for process window
    fig = go.Figure()
    
    # Add process window rectangle
    fig.add_shape(
        type="rect",
        x0=t_min, y0=p_min,
        x1=t_max, y1=p_max,
        line=dict(color="RoyalBlue", width=2, dash="solid"),
        fillcolor="rgba(65, 105, 225, 0.2)",
        name="工艺窗口"
    )
    
    # Add current operating point if provided
    if current_p is not None and current_t is not None:
        fig.add_trace(go.Scatter(
            x=[current_t],
            y=[current_p],
            mode='markers',
            marker=dict(
                size=12,
                color='lime',
                symbol='star'
            ),
            name='当前工艺点',
            text=[f"温度: {current_t}°C<br>压力: {current_p}MPa"],
            hovertemplate='%{text}<extra></extra>'
        ))
    
    fig.update_layout(
        title="压力-温度工艺窗口定义",
        xaxis=dict(title="温度 (°C)", range=[t_min-10, t_max+10]),
        yaxis=dict(title="压力 (MPa)", range=[p_min-10, p_max+10]),
        height=400,
        template="plotly_dark",
        font=dict(family="Arial, sans-serif", size=12, color="#f5f7fa"),
        paper_bgcolor="rgba(30, 30, 46, 0.8)",
        plot_bgcolor="rgba(40, 40, 60, 0.8)",
        hovermode='closest'
    )
    
    return fig.to_html(include_plotlyjs='cdn', div_id='process_window_chart')


# ============================================================
# Data Export Functions
# ============================================================

def export_to_csv(
    experiment_name: str,
    data: Dict[str, any]
) -> bytes:
    """
    Export experiment data to CSV format.
    
    Args:
        experiment_name: Name of the experiment
        data: Dictionary containing experiment data
    
    Returns:
        CSV file content as bytes
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["SmartMold 科学注塑数据导出"])
    writer.writerow([""])
    writer.writerow(["实验名称", experiment_name])
    writer.writerow(["导出时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([""])
    
    # Data sections
    for section_name, section_data in data.items():
        writer.writerow([section_name])
        
        if isinstance(section_data, dict):
            for key, value in section_data.items():
                writer.writerow([key, value])
        elif isinstance(section_data, list):
            for item in section_data:
                writer.writerow(item)
        
        writer.writerow([""])
    
    return output.getvalue().encode('utf-8')


def export_to_json(
    experiment_name: str,
    data: Dict[str, any],
    metadata: Dict[str, any] = None
) -> str:
    """
    Export experiment data to JSON format.
    
    Args:
        experiment_name: Name of the experiment
        data: Dictionary containing experiment data
        metadata: Optional metadata (machine, operator, etc.)
    
    Returns:
        JSON string
    """
    export_data = {
        "experiment": {
            "name": experiment_name,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
    }
    
    if metadata:
        export_data["metadata"] = metadata
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)


# ============================================================
# History Management
# ============================================================

class ExperimentHistory:
    """Manage experiment history records."""
    
    def __init__(self, storage_file: str = "experiment_history.json"):
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
    
    def add_record(
        self,
        experiment_name: str,
        experiment_type: str,
        results: Dict[str, any],
        metadata: Dict[str, any] = None
    ):
        """Add a new experiment record."""
        record = {
            "id": len(self.history) + 1,
            "timestamp": datetime.now().isoformat(),
            "name": experiment_name,
            "type": experiment_type,
            "results": results,
            "metadata": metadata or {}
        }
        self.history.append(record)
        self._save_history()
        return record
    
    def get_records(
        self,
        experiment_type: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """Retrieve experiment records."""
        if experiment_type:
            records = [r for r in self.history if r['type'] == experiment_type]
        else:
            records = self.history
        
        # Return most recent records first
        return sorted(records, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_record_by_id(self, record_id: int) -> Dict:
        """Get specific record by ID."""
        for record in self.history:
            if record['id'] == record_id:
                return record
        return None
    
    def delete_record(self, record_id: int) -> bool:
        """Delete a record by ID."""
        original_len = len(self.history)
        self.history = [r for r in self.history if r['id'] != record_id]
        
        if len(self.history) < original_len:
            self._save_history()
            return True
        return False
    
    def get_statistics(self, experiment_type: str = None) -> Dict:
        """Get statistics about stored records."""
        records = self.history
        
        if experiment_type:
            records = [r for r in records if r['type'] == experiment_type]
        
        if not records:
            return {
                "total_records": 0,
                "total_experiments": 0,
                "date_range": None
            }
        
        return {
            "total_records": len(records),
            "total_experiments": len(set(r['name'] for r in records)),
            "experiment_types": list(set(r['type'] for r in records)),
            "earliest_record": records[-1]['timestamp'] if records else None,
            "latest_record": records[0]['timestamp'] if records else None,
            "average_records_per_type": len(records) / len(set(r['type'] for r in records))
        }


# ============================================================
# Data Validation & Analysis
# ============================================================

def validate_viscosity_inputs(temperature: float, shear_rate: float) -> Tuple[bool, str]:
    """Validate viscosity calculation inputs."""
    if not 200 <= temperature <= 300:
        return False, "温度必须在 200-300°C 范围内"
    if not 0.1 <= shear_rate <= 100:
        return False, "剪切速率必须在 0.1-100 s⁻¹ 范围内"
    return True, "✓ 输入有效"


def validate_cavity_pressures(pressures: List[float]) -> Tuple[bool, str]:
    """Validate cavity pressure inputs."""
    if not pressures or len(pressures) != 8:
        return False, "必须提供 8 个型腔压力值"
    if not all(0 < p < 150 for p in pressures):
        return False, "压力必须在 0-150 MPa 范围内"
    return True, "✓ 输入有效"


def validate_weights(weights: List[float], target: float) -> Tuple[bool, str]:
    """Validate weight data."""
    if not weights or len(weights) < 3:
        return False, "至少需要 3 个样品数据"
    if not all(0 < w < 100 for w in weights):
        return False, "体重必须在 0-100g 范围内"
    if not 0 < target < 100:
        return False, "目标体重必须在 0-100g 范围内"
    return True, "✓ 输入有效"


def analyze_trends(
    records: List[Dict],
    metric: str = "result"
) -> Dict:
    """
    Analyze trends in historical experiment data.
    
    Args:
        records: List of experiment records
        metric: Metric to analyze
    
    Returns:
        Trend analysis dictionary
    """
    if not records:
        return {"error": "No records to analyze"}
    
    values = []
    timestamps = []
    
    for record in records:
        if metric in record.get('results', {}):
            values.append(float(record['results'][metric]))
            timestamps.append(record['timestamp'])
    
    if not values:
        return {"error": f"No data for metric: {metric}"}
    
    return {
        "metric": metric,
        "count": len(values),
        "mean": np.mean(values),
        "median": np.median(values),
        "std_dev": np.std(values),
        "min": np.min(values),
        "max": np.max(values),
        "trend": "improving" if values[-1] < values[0] else "declining"
    }
