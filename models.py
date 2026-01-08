"""
SmartMold Pilot V3 - Tortoise-ORM Models
Database models for Scientific Molding and Machine Performance testing.
"""

from tortoise import Model, fields
from datetime import datetime
from typing import Optional


class Machine(Model):
    """Injection molding machine information."""
    id = fields.IntField(pk=True)
    code = fields.CharField(max_length=50, unique=True, description="Machine ID/Code")
    brand = fields.CharField(max_length=100, null=True, description="e.g., Arburg, Haitian")
    tonnage = fields.IntField(description="Clamping force in tons")
    screw_diameter = fields.FloatField(description="Screw diameter in mm")
    max_pressure = fields.FloatField(description="Max injection pressure in MPa")
    max_speed = fields.FloatField(null=True, description="Max injection speed in mm/s")
    intensification_ratio = fields.FloatField(null=True, description="Pressure intensification ratio")
    theoretical_injection_weight = fields.FloatField(null=True, description="Theoretical weight in g")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "machine"


class Mold(Model):
    """Injection mold information."""
    id = fields.IntField(pk=True)
    code = fields.CharField(max_length=50, unique=True, description="Mold ID/Code")
    cavity_count = fields.IntField(description="Number of cavities")
    material = fields.CharField(max_length=100, null=True, description="e.g., PC, ABS")
    gate_type = fields.CharField(max_length=50, null=True, description="e.g., Side Gate, Hot Runner")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "mold"


class ExperimentSession(Model):
    """Parent experiment session linking Machine and Mold."""
    id = fields.IntField(pk=True)
    session_code = fields.CharField(max_length=100, unique=True, description="Unique session identifier")
    machine = fields.ForeignKeyField("models.Machine", related_name="experiment_sessions")
    mold = fields.ForeignKeyField("models.Mold", related_name="experiment_sessions")
    
    # Snapshot: Freeze machine parameters at experiment creation time
    snapshot_machine_data = fields.JSONField(
        description="Machine parameters snapshot (tonnage, pressure, speed, etc.)"
    )
    
    experiment_type = fields.CharField(
        max_length=50,
        choices=["scientific_molding", "machine_performance"],
        description="Type of experiment"
    )
    status = fields.CharField(
        max_length=50,
        default="in_progress",
        choices=["in_progress", "completed", "archived"],
        description="Experiment status"
    )
    
    notes = fields.TextField(null=True, description="General notes")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "experiment_session"


# ============================================================
# Scientific Molding Module: Experiment Data Tables
# ============================================================

class ViscosityData(Model):
    """Viscosity Curve Experiment - one row per injection speed test."""
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField(
        "models.ExperimentSession",
        related_name="viscosity_data_list"
    )
    
    # Input fields
    fill_speed_percent = fields.FloatField(description="Fill speed as percentage (%)")
    fill_speed_mm_s = fields.FloatField(description="Fill speed in mm/s")
    switch_position = fields.FloatField(description="V/P switch position in mm")
    fill_time = fields.FloatField(description="Fill time in seconds")
    peak_pressure = fields.FloatField(description="Peak pressure in Bar/MPa")
    
    # Computed fields (auto-calculated)
    shear_rate = fields.FloatField(null=True, description="Shear rate in 1/s")
    viscosity = fields.FloatField(null=True, description="Effective viscosity")
    
    # Metadata
    sequence_number = fields.IntField(description="Test sequence (1, 2, 3...)")
    notes = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "viscosity_data"


class BalanceData(Model):
    """Cavity Balance Experiment - multiple cavities per test."""
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField(
        "models.ExperimentSession",
        related_name="balance_data_list"
    )
    
    # Cavity index and weight
    cavity_index = fields.IntField(description="Cavity number (1, 2, 3...)")
    weight = fields.FloatField(description="Product weight in grams")
    visual_check = fields.CharField(max_length=10, default="OK", description="Visual Check (OK/NG)")
    
    # Test round/iteration
    test_round = fields.IntField(default=1, description="Test round number")
    fill_percentage = fields.FloatField(null=True, description="Fill percentage (e.g., 50%, 99%)")
    
    notes = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "balance_data"


class BalanceResult(Model):
    """Cavity Balance Result - summary per test round."""
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField(
        "models.ExperimentSession",
        related_name="balance_results"
    )
    
    test_round = fields.IntField(description="Test round number")
    max_weight = fields.FloatField(description="Maximum weight among cavities")
    min_weight = fields.FloatField(description="Minimum weight among cavities")
    avg_weight = fields.FloatField(description="Average weight")
    
    # Calculated
    imbalance_percent = fields.FloatField(description="Imbalance % = (Max-Min)/Avg*100")
    imbalance_threshold = fields.FloatField(default=5.0, description="Acceptable threshold (%)")
    status = fields.CharField(
        max_length=20,
        choices=["pass", "fail"],
        description="Pass/Fail based on imbalance %"
    )
    
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "balance_result"


class PressureWindowData(Model):
    """Pressure Process Window Experiment - test different holding pressures."""
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField(
        "models.ExperimentSession",
        related_name="pressure_window_data"
    )
    
    # Input
    holding_pressure = fields.FloatField(description="Holding pressure in MPa/Bar")
    product_weight = fields.FloatField(null=True, description="Product weight in grams")
    appearance_status = fields.CharField(
        max_length=20,
        choices=["ok", "flash", "short", "incomplete"],
        description="OK/Flash/Short/Incomplete"
    )
    
    sequence = fields.IntField(description="Test sequence")
    notes = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "pressure_window_data"


class PressureWindowResult(Model):
    """Pressure Window Result - identified optimal window."""
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField(
        "models.ExperimentSession",
        related_name="pressure_window_results"
    )
    
    min_optimal_pressure = fields.FloatField(null=True, description="Min pressure with OK appearance")
    max_optimal_pressure = fields.FloatField(null=True, description="Max pressure with OK appearance")
    recommended_pressure = fields.FloatField(null=True, description="Midpoint (optimal)")
    
    status = fields.CharField(
        max_length=20,
        choices=["insufficient_data", "found", "failed"],
        default="insufficient_data"
    )
    
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "pressure_window_result"


class GateFreezeData(Model):
    """Gate Freezing Time Experiment - track weight vs holding time."""
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField(
        "models.ExperimentSession",
        related_name="gate_freeze_data"
    )
    
    holding_time = fields.FloatField(description="Holding time in seconds")
    product_weight = fields.FloatField(description="Product weight in grams")
    sequence = fields.IntField(description="Test sequence")
    
    notes = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "gate_freeze_data"


class GateFreezeResult(Model):
    """Gate Freezing Result - identified freeze time."""
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField(
        "models.ExperimentSession",
        related_name="gate_freeze_results"
    )
    
    freeze_time = fields.FloatField(null=True, description="Gate freeze time in seconds")
    recommended_holding_time = fields.FloatField(null=True, description="Recommended holding time")
    
    status = fields.CharField(
        max_length=20,
        choices=["insufficient_data", "found"],
        default="insufficient_data"
    )
    
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "gate_freeze_result"


# ============================================================
# Machine Performance Module: Test Data Tables
# ============================================================

class InjectionWeightData(Model):
    """Injection Weight Repeatability Test - consecutive shots."""
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField(
        "models.ExperimentSession",
        related_name="injection_weight_data"
    )
    
    shot_number = fields.IntField(description="Shot sequence (1, 2, 3, 4, 5)")
    weight = fields.FloatField(description="Injection weight in grams")
    
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "injection_weight_data"


class InjectionWeightResult(Model):
    """Injection Weight Result - Pass/Fail judgment."""
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField(
        "models.ExperimentSession",
        related_name="injection_weight_results"
    )
    
    max_weight = fields.FloatField(description="Maximum weight")
    min_weight = fields.FloatField(description="Minimum weight")
    avg_weight = fields.FloatField(description="Average weight")
    
    # (Max - Min) / Avg
    repeatability_percent = fields.FloatField(description="Repeatability % = (Max-Min)/Avg*100")
    threshold_percent = fields.FloatField(default=1.0, description="Acceptable threshold (%)")
    
    status = fields.CharField(
        max_length=20,
        choices=["pass", "fail"],
        description="Pass if repeatability < threshold"
    )
    
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "injection_weight_result"


class InjectionSpeedData(Model):
    """Injection Speed Linearity Test - set speed vs actual speed."""
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField(
        "models.ExperimentSession",
        related_name="injection_speed_data"
    )
    
    set_speed_percent = fields.FloatField(description="Set speed as percentage (%)")
    actual_speed_mm_s = fields.FloatField(description="Actual speed in mm/s")
    
    sequence = fields.IntField(description="Test sequence")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "injection_speed_data"


class InjectionSpeedResult(Model):
    """Injection Speed Linearity Result - R² and regression info."""
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField(
        "models.ExperimentSession",
        related_name="injection_speed_results"
    )
    
    # Linear regression: y = slope * x + intercept
    slope = fields.FloatField(null=True, description="Regression slope")
    intercept = fields.FloatField(null=True, description="Regression intercept")
    r_squared = fields.FloatField(null=True, description="R² goodness of fit (0-1)")
    
    status = fields.CharField(
        max_length=20,
        choices=["insufficient_data", "excellent", "good", "poor"],
        default="insufficient_data",
        description="R² > 0.98: excellent; > 0.95: good; else poor"
    )
    
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "injection_speed_result"


class CheckRingData(Model):
    """Check Ring (止逆环) Dynamic/Static Leakage Test."""
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField(
        "models.ExperimentSession",
        related_name="check_ring_data"
    )
    
    test_type = fields.CharField(
        max_length=20,
        choices=["dynamic", "static"],
        description="Dynamic or Static leakage test"
    )
    
    cycle_number = fields.IntField(description="Cycle/repeat number")
    leakage_volume = fields.FloatField(null=True, description="Leakage volume (ml or cc)")
    pressure = fields.FloatField(null=True, description="Test pressure in MPa/Bar")
    
    notes = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "check_ring_data"


# ============================================================
# Utility/Meta Table
# ============================================================

class ExperimentTemplate(Model):
    """Pre-defined experiment templates for quick setup."""
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, description="e.g., 'Standard 6-Step Scientific Molding'")
    description = fields.TextField(null=True)
    template_type = fields.CharField(
        max_length=50,
        choices=["scientific_molding", "machine_performance"],
        description="Template category"
    )
    
    # Store template config as JSON
    config = fields.JSONField(description="Experiment configuration (thresholds, field names, etc.)")
    
    is_default = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "experiment_template"
